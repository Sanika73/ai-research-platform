"""
Storage Service for Research Platform
====================================

Integrates database and document storage with the research workflow.
Provides methods to store, retrieve, and analyze research data.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
import json
import re

from models.database import (
    SessionLocal, ResearchTask, ResearchResult, IdeaPortfolio, SystemMetrics,
    get_db, init_database
)
from services.document_manager import research_docs

class StorageService:
    """Main service for handling research data storage and retrieval"""
    
    def __init__(self):
        self.doc_manager = research_docs
        init_database()  # Ensure database is initialized
    
    def get_db_session(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def save_research_task(self, task_data: Dict[str, Any]) -> str:
        """Save a research task to database"""
        db = self.get_db_session()
        try:
            task = ResearchTask(
                task_id=task_data['task_id'],
                query=task_data['query'],
                model=task_data['model'],
                research_type=task_data['research_type'],
                status=task_data.get('status', 'pending'),
                progress=task_data.get('progress', 'Task created'),
                enrich_prompt=task_data.get('enrich_prompt', True),
                created_at=datetime.utcnow()
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            return task.task_id
        finally:
            db.close()
    
    def update_research_task(self, task_id: str, updates: Dict[str, Any]):
        """Update research task status and progress"""
        db = self.get_db_session()
        try:
            task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
            if task:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # Set timestamps based on status
                if updates.get('status') == 'running' and not task.started_at:
                    task.started_at = datetime.utcnow()
                elif updates.get('status') in ['completed', 'failed']:
                    task.completed_at = datetime.utcnow()
                
                db.commit()
        finally:
            db.close()
    
    def complete_research_task(self, task_id: str, result_data: Dict[str, Any]) -> bool:
        """Complete a research task with results"""
        db = self.get_db_session()
        try:
            # Update task with results
            task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
            if not task:
                return False
            
            # Save result data to task
            task.result_data = result_data
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            
            # Extract idea name from query for document and analysis
            idea_name = self._extract_idea_name(task.query)
            
            # Save as MD document
            try:
                doc_path = self.doc_manager.save_research_document(
                    task_id=task_id,
                    idea_name=idea_name,
                    research_type=task.research_type,
                    research_data=result_data,
                    model_used=task.model
                )
                task.md_document_path = doc_path
            except Exception as e:
                print(f"Error saving document: {e}")
            
            # Process and save research results for dashboard
            self._process_research_results(task, result_data, idea_name)
            
            # Update or create portfolio entry
            self._update_idea_portfolio(task, result_data, idea_name)
            
            # Update system metrics
            self._update_system_metrics()
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"Error completing research task: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def _extract_idea_name(self, query: str) -> str:
        """Extract or generate idea name from research query"""
        # Look for common patterns
        patterns = [
            r"(?:idea|concept|startup|business).*?[:]\\s*(.+)",
            r"(.+?)(?:\\s+(?:startup|idea|business|app|platform|service))",
            r"^(.{1,50})"  # First 50 characters as fallback
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                idea_name = match.group(1).strip()
                if len(idea_name) > 5:  # Must be meaningful
                    return idea_name
        
        # Fallback: use first few words
        words = query.split()[:5]
        return " ".join(words)
    
    def _process_research_results(self, task: ResearchTask, result_data: Dict[str, Any], idea_name: str):
        """Process and save research results for dashboard display"""
        db = self.get_db_session()
        try:
            # Extract metrics from research result
            result = result_data.get('result', {})
            
            # Calculate scores from research content
            scores = self._calculate_scores_from_research(result)
            
            # Extract citations and word count
            citations = self._count_citations(result)
            word_count = self._count_words(result)
            
            # Determine industry from query/result
            industry = self._determine_industry(task.query, result)
            
            research_result = ResearchResult(
                task_id=task.task_id,
                idea_name=idea_name,
                description=task.query[:500],  # Truncate description
                industry=industry,
                market_opportunity_score=scores.get('market_opportunity', 0),
                technical_feasibility_score=scores.get('technical_feasibility', 0),
                competitive_advantage_score=scores.get('competitive_advantage', 0), 
                risk_level=scores.get('risk_level', 5),
                total_citations=citations,
                research_depth_score=min(100, citations * 2),  # Scale citations to score
                word_count=word_count,
                validation_status='completed',
                last_updated=datetime.utcnow()
            )
            
            db.add(research_result)
            db.commit()
            
        except Exception as e:
            print(f"Error processing research results: {e}")
        finally:
            db.close()
    
    def _calculate_scores_from_research(self, result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scores based on research content analysis"""
        scores = {
            'market_opportunity': 70,  # Default values
            'technical_feasibility': 65,
            'competitive_advantage': 60,
            'risk_level': 5
        }
        
        # Analyze content for positive/negative indicators
        content = str(result).lower()
        
        # Market opportunity indicators
        positive_market = ['large market', 'growing market', 'opportunity', 'demand', 'potential']
        negative_market = ['small market', 'declining', 'saturated', 'competitive']
        
        market_score = 70
        for indicator in positive_market:
            if indicator in content:
                market_score += 5
        for indicator in negative_market:
            if indicator in content:
                market_score -= 5
        
        scores['market_opportunity'] = max(0, min(100, market_score))
        
        # Technical feasibility indicators
        tech_positive = ['feasible', 'proven technology', 'available tools', 'straightforward']
        tech_negative = ['complex', 'challenging', 'difficult', 'unproven', 'experimental']
        
        tech_score = 65
        for indicator in tech_positive:
            if indicator in content:
                tech_score += 5
        for indicator in tech_negative:
            if indicator in content:
                tech_score -= 5
        
        scores['technical_feasibility'] = max(0, min(100, tech_score))
        
        # Competitive advantage 
        comp_positive = ['unique', 'innovative', 'first-mover', 'differentiated']
        comp_negative = ['crowded market', 'many competitors', 'commoditized']
        
        comp_score = 60
        for indicator in comp_positive:
            if indicator in content:
                comp_score += 5
        for indicator in comp_negative:
            if indicator in content:
                comp_score -= 5
        
        scores['competitive_advantage'] = max(0, min(100, comp_score))
        
        return scores
    
    def _count_citations(self, result: Dict[str, Any]) -> int:
        """Count citations/sources in research result"""
        content = str(result)
        
        # Count various citation patterns
        patterns = [
            r'\\[\\d+\\]',  # [1], [2], etc.
            r'\\(\\d{4}\\)',  # (2023), (2024), etc.
            r'http[s]?://[^\\s]+',  # URLs
            r'doi:[^\\s]+',  # DOI references
            r'(?:according to|source:|reference:|study by)',  # Reference indicators
        ]
        
        total_citations = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            total_citations += len(matches)
        
        return min(total_citations, 50)  # Cap at 50 to be realistic
    
    def _count_words(self, result: Dict[str, Any]) -> int:
        """Count words in research result"""
        content = str(result)
        words = re.findall(r'\\b\\w+\\b', content)
        return len(words)
    
    def _determine_industry(self, query: str, result: Dict[str, Any]) -> str:
        """Determine industry from query and result content"""
        content = (query + " " + str(result)).lower()
        
        industry_keywords = {
            'technology': ['tech', 'software', 'ai', 'blockchain', 'iot', 'cloud', 'saas'],
            'healthcare': ['health', 'medical', 'hospital', 'patient', 'therapy', 'wellness', 'pharma'],
            'fintech': ['finance', 'payment', 'banking', 'crypto', 'trading', 'investment', 'loan'],
            'education': ['education', 'learning', 'student', 'school', 'university', 'course', 'teaching'],
            'e-commerce': ['ecommerce', 'retail', 'shopping', 'marketplace', 'store', 'commerce'],
            'fitness': ['fitness', 'workout', 'exercise', 'gym', 'sports', 'training'],
            'entertainment': ['game', 'media', 'music', 'video', 'streaming', 'entertainment'],
            'food': ['food', 'restaurant', 'cooking', 'delivery', 'recipe', 'meal']
        }
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    return industry
        
        return 'other'
    
    def _update_idea_portfolio(self, task: ResearchTask, result_data: Dict[str, Any], idea_name: str):
        """Update or create idea portfolio entry"""
        db = self.get_db_session()
        try:
            # Check if idea already exists in portfolio
            existing_idea = db.query(IdeaPortfolio).filter(
                IdeaPortfolio.idea_name == idea_name
            ).first()
            
            if existing_idea:
                # Update existing idea
                existing_idea.latest_task_id = task.task_id
                existing_idea.research_model = task.model
                existing_idea.last_research = datetime.utcnow()
                existing_idea.research_count += 1
                
                # Update scores from latest research
                result = db.query(ResearchResult).filter(
                    ResearchResult.task_id == task.task_id
                ).first()
                if result:
                    existing_idea.market_opportunity_score = result.market_opportunity_score
                    existing_idea.technical_feasibility_score = result.technical_feasibility_score
                    existing_idea.competitive_advantage_score = result.competitive_advantage_score
                    existing_idea.risk_level = result.risk_level
                    existing_idea.industry = result.industry
                    
                    # Update status based on scores
                    if result.market_opportunity_score > 80 and result.technical_feasibility_score > 75:
                        existing_idea.status = 'ready'
                    elif result.market_opportunity_score > 60:
                        existing_idea.status = 'validated'
                    else:
                        existing_idea.status = 'in-progress'
            
            else:
                # Create new portfolio entry
                result = db.query(ResearchResult).filter(
                    ResearchResult.task_id == task.task_id
                ).first()
                
                status = 'initial'
                if result:
                    if result.market_opportunity_score > 80 and result.technical_feasibility_score > 75:
                        status = 'ready'
                    elif result.market_opportunity_score > 60:
                        status = 'validated'
                    else:
                        status = 'in-progress'
                
                new_idea = IdeaPortfolio(
                    idea_name=idea_name,
                    description=task.query[:500],
                    industry=result.industry if result else 'other',
                    latest_task_id=task.task_id,
                    research_model=task.model,
                    status=status,
                    market_opportunity_score=result.market_opportunity_score if result else 0,
                    technical_feasibility_score=result.technical_feasibility_score if result else 0,
                    competitive_advantage_score=result.competitive_advantage_score if result else 0,
                    risk_level=result.risk_level if result else 5,
                    created_at=datetime.utcnow(),
                    last_research=datetime.utcnow(),
                    research_count=1
                )
                
                db.add(new_idea)
            
            db.commit()
            
        except Exception as e:
            print(f"Error updating idea portfolio: {e}")
        finally:
            db.close()
    
    def _update_system_metrics(self):
        """Update system-wide metrics for dashboard"""
        db = self.get_db_session()
        try:
            # Calculate current metrics
            total_ideas = db.query(IdeaPortfolio).count()
            
            # Average market scores
            avg_market_score = db.query(func.avg(IdeaPortfolio.market_opportunity_score)).scalar() or 0
            
            # Ideas ready for development
            ideas_ready = db.query(IdeaPortfolio).filter(IdeaPortfolio.status == 'ready').count()
            
            # Calculate total market opportunity (sum of top ideas)
            top_ideas = db.query(IdeaPortfolio).order_by(desc(IdeaPortfolio.market_opportunity_score)).limit(10).all()
            total_market_opportunity = sum([idea.market_opportunity_score * 100000000 for idea in top_ideas])  # Scale to billions
            market_opportunity_str = f"${total_market_opportunity / 1000000000:.1f}B"
            
            # New ideas this month
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            new_ideas_this_month = db.query(IdeaPortfolio).filter(
                extract('month', IdeaPortfolio.created_at) == current_month,
                extract('year', IdeaPortfolio.created_at) == current_year
            ).count()
            
            # Average research depth
            avg_research_depth = db.query(func.avg(ResearchResult.research_depth_score)).scalar() or 0
            
            # Validation success rate
            validated_ideas = db.query(IdeaPortfolio).filter(
                IdeaPortfolio.status.in_(['validated', 'ready'])
            ).count()
            validation_success_rate = (validated_ideas / total_ideas * 100) if total_ideas > 0 else 0
            
            # Research task statistics
            total_research_tasks = db.query(ResearchTask).count()
            completed_tasks = db.query(ResearchTask).filter(ResearchTask.status == 'completed').count()
            failed_tasks = db.query(ResearchTask).filter(ResearchTask.status == 'failed').count()
            
            # Industry distribution
            industry_counts = db.query(
                IdeaPortfolio.industry, 
                func.count(IdeaPortfolio.id)
            ).group_by(IdeaPortfolio.industry).all()
            
            industry_distribution = [
                {"name": industry.title(), "value": count, "percentage": (count / total_ideas * 100) if total_ideas > 0 else 0}
                for industry, count in industry_counts
            ]
            
            # Create or update metrics record
            metrics = SystemMetrics(
                total_ideas=total_ideas,
                avg_market_score=round(avg_market_score, 1),
                ideas_ready_for_development=ideas_ready,
                total_market_opportunity=market_opportunity_str,
                new_ideas_this_month=new_ideas_this_month,
                avg_research_depth=round(avg_research_depth, 1),
                validation_success_rate=round(validation_success_rate, 1),
                total_research_tasks=total_research_tasks,
                completed_research_tasks=completed_tasks,
                failed_research_tasks=failed_tasks,
                industry_distribution=industry_distribution,
                metric_date=datetime.utcnow()
            )
            
            db.add(metrics)
            db.commit()
            
        except Exception as e:
            print(f"Error updating system metrics: {e}")
        finally:
            db.close()
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get dashboard overview metrics"""
        db = self.get_db_session()
        try:
            # Get latest metrics
            metrics = db.query(SystemMetrics).order_by(desc(SystemMetrics.metric_date)).first()
            
            if metrics:
                return {
                    "total_ideas": metrics.total_ideas,
                    "avg_market_score": metrics.avg_market_score,
                    "ideas_ready_for_development": metrics.ideas_ready_for_development,
                    "total_market_opportunity": metrics.total_market_opportunity,
                    "new_ideas_this_month": metrics.new_ideas_this_month,
                    "avg_research_depth": metrics.avg_research_depth,
                    "validation_success_rate": metrics.validation_success_rate
                }
            else:
                # Return defaults if no metrics yet
                return {
                    "total_ideas": 0,
                    "avg_market_score": 0,
                    "ideas_ready_for_development": 0,
                    "total_market_opportunity": "$0",
                    "new_ideas_this_month": 0,
                    "avg_research_depth": 0,
                    "validation_success_rate": 0
                }
                
        finally:
            db.close()
    
    def get_dashboard_ideas(self) -> List[Dict[str, Any]]:
        """Get all ideas for dashboard display"""
        db = self.get_db_session()
        try:
            ideas = db.query(IdeaPortfolio).filter(
                IdeaPortfolio.archived == False
            ).order_by(desc(IdeaPortfolio.last_research)).all()
            
            return [
                {
                    "idea_id": idea.idea_id,
                    "idea_name": idea.idea_name,
                    "description": idea.description,
                    "industry": idea.industry,
                    "research_model": idea.research_model,
                    "status": idea.status,
                    "created_at": idea.created_at.isoformat() if idea.created_at else None,
                    "last_research": idea.last_research.isoformat() if idea.last_research else None,
                    "scores": {
                        "market_opportunity": idea.market_opportunity_score,
                        "technical_feasibility": idea.technical_feasibility_score,
                        "competitive_advantage": idea.competitive_advantage_score,
                        "risk_level": idea.risk_level
                    },
                    "research_data": {
                        "total_citations": 0,  # Will be populated from research_results if needed
                        "research_depth_score": 0,
                        "validation_sources": 0,
                        "competitor_analysis_count": 0
                    }
                }
                for idea in ideas
            ]
            
        finally:
            db.close()
    
    def get_research_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get research task by ID"""
        db = self.get_db_session()
        try:
            task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
            if task:
                return {
                    "task_id": task.task_id,
                    "query": task.query,
                    "model": task.model,
                    "research_type": task.research_type,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result_data": task.result_data
                }
            return None
        finally:
            db.close()
    
    def get_all_research_results(self) -> List[Dict[str, Any]]:
        """Get all completed research results"""
        db = self.get_db_session()
        try:
            tasks = db.query(ResearchTask).filter(
                ResearchTask.status == 'completed'
            ).order_by(desc(ResearchTask.completed_at)).all()
            
            results = []
            for task in tasks:
                result_data = {
                    "task_id": task.task_id,
                    "query": task.query,
                    "model": task.model,
                    "research_type": task.research_type,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                
                # Add result summary if available
                if task.result_data:
                    result_data["result"] = {
                        "total_citations": self._count_citations(task.result_data),
                        "word_count": self._count_words(task.result_data)
                    }
                
                results.append(result_data)
            
            return results
            
        finally:
            db.close()

# Initialize storage service
storage_service = StorageService()

if __name__ == "__main__":
    print("✅ Storage Service initialized")
    
    # Test database connection
    overview = storage_service.get_dashboard_overview()
    print(f"📊 Dashboard overview: {overview}")
    
    ideas = storage_service.get_dashboard_ideas()
    print(f"💡 Portfolio ideas: {len(ideas)}")
