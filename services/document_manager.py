"""
Research Document Storage System
===============================

Manages saving and retrieving research results as organized MD documents
with proper metadata and folder structure.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import re

class ResearchDocumentManager:
    """Manages storage and retrieval of research documents"""
    
    def __init__(self, base_path: str = "./research_documents"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self._create_folder_structure()
    
    def _create_folder_structure(self):
        """Create organized folder structure for research documents"""
        folders = [
            "comprehensive_research",
            "idea_validation", 
            "market_research",
            "financial_analysis",
            "custom_research",
            "metadata",
            "archives"
        ]
        
        for folder in folders:
            (self.base_path / folder).mkdir(exist_ok=True)
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert idea name to safe filename"""
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.lower()[:50]  # Limit length
    
    def _get_folder_for_type(self, research_type: str) -> Path:
        """Get appropriate folder for research type"""
        folder_map = {
            "comprehensive": "comprehensive_research",
            "validation": "idea_validation",
            "market": "market_research", 
            "financial": "financial_analysis",
            "custom": "custom_research"
        }
        
        folder_name = folder_map.get(research_type, "custom_research")
        return self.base_path / folder_name
    
    def save_research_document(self, 
                             task_id: str,
                             idea_name: str,
                             research_type: str,
                             research_data: Dict[str, Any],
                             model_used: str) -> str:
        """
        Save research result as MD document with metadata
        
        Returns: Path to saved document
        """
        
        # Create filename
        sanitized_name = self._sanitize_filename(idea_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_name}_{research_type}_{timestamp}.md"
        
        # Get appropriate folder
        folder = self._get_folder_for_type(research_type)
        file_path = folder / filename
        
        # Extract key information from research data
        result = research_data.get('result', {})
        
        # Generate MD content
        md_content = self._generate_markdown_content(
            idea_name=idea_name,
            research_type=research_type,
            research_data=result,
            model_used=model_used,
            task_id=task_id
        )
        
        # Save MD file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Save metadata
        self._save_metadata(task_id, file_path, {
            'idea_name': idea_name,
            'research_type': research_type,
            'model_used': model_used,
            'created_at': datetime.now().isoformat(),
            'file_path': str(file_path),
            'word_count': len(md_content.split()),
            'task_id': task_id
        })
        
        return str(file_path)
    
    def _generate_markdown_content(self, 
                                 idea_name: str,
                                 research_type: str,
                                 research_data: Dict[str, Any],
                                 model_used: str,
                                 task_id: str) -> str:
        """Generate formatted markdown content"""
        
        # Header
        md_content = f"""# {idea_name}
**Research Type:** {research_type.title()}  
**AI Model:** {model_used}  
**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}  
**Task ID:** `{task_id}`

---

"""
        
        # Executive Summary
        if 'executive_summary' in research_data:
            md_content += f"""## Executive Summary

{research_data['executive_summary']}

---

"""
        
        # Main content based on research type
        if research_type == "comprehensive":
            md_content += self._format_comprehensive_research(research_data)
        elif research_type == "validation":
            md_content += self._format_validation_research(research_data)
        elif research_type == "market":
            md_content += self._format_market_research(research_data)
        elif research_type == "financial":
            md_content += self._format_financial_research(research_data)
        else:
            md_content += self._format_custom_research(research_data)
        
        # Citations and Sources
        if 'citations' in research_data:
            md_content += f"""## Sources and Citations

{research_data['citations']}

"""
        
        # Metadata footer
        md_content += f"""---

*This research report was generated using {model_used} on {datetime.now().strftime("%B %d, %Y")}. Task ID: {task_id}*
"""
        
        return md_content
    
    def _format_comprehensive_research(self, data: Dict[str, Any]) -> str:
        """Format comprehensive research results"""
        content = ""
        
        # Idea Validation Section
        if 'validation' in data:
            content += f"""## 🔍 Idea Validation

{data['validation']}

"""
        
        # Market Research Section  
        if 'market_research' in data:
            content += f"""## 📊 Market Research

{data['market_research']}

"""
        
        # Financial Analysis Section
        if 'financial_analysis' in data:
            content += f"""## 💰 Financial Analysis

{data['financial_analysis']}

"""
        
        return content
    
    def _format_validation_research(self, data: Dict[str, Any]) -> str:
        """Format idea validation research"""
        content = f"""## 🔍 Idea Validation Analysis

"""
        
        if 'analysis' in data:
            content += f"{data['analysis']}\n\n"
        
        if 'key_findings' in data:
            content += f"""### Key Findings

{data['key_findings']}

"""
        
        return content
    
    def _format_market_research(self, data: Dict[str, Any]) -> str:
        """Format market research results"""
        content = f"""## 📊 Market Research Analysis

"""
        
        if 'market_analysis' in data:
            content += f"{data['market_analysis']}\n\n"
        
        if 'competitive_analysis' in data:
            content += f"""### Competitive Analysis

{data['competitive_analysis']}

"""
        
        return content
    
    def _format_financial_research(self, data: Dict[str, Any]) -> str:
        """Format financial analysis results"""
        content = f"""## 💰 Financial Analysis

"""
        
        if 'financial_projections' in data:
            content += f"{data['financial_projections']}\n\n"
        
        if 'cost_analysis' in data:
            content += f"""### Cost Analysis

{data['cost_analysis']}

"""
        
        return content
    
    def _format_custom_research(self, data: Dict[str, Any]) -> str:
        """Format custom research results"""
        content = f"""## 🔬 Research Analysis

"""
        
        if 'analysis' in data:
            content += f"{data['analysis']}\n\n"
        elif 'result' in data:
            content += f"{data['result']}\n\n"
        
        return content
    
    def _save_metadata(self, task_id: str, file_path: Path, metadata: Dict[str, Any]):
        """Save metadata for research document"""
        metadata_file = self.base_path / "metadata" / f"{task_id}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def get_document_path(self, task_id: str) -> Optional[str]:
        """Get document path for a task ID"""
        metadata_file = self.base_path / "metadata" / f"{task_id}.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata.get('file_path')
        
        return None
    
    def list_documents(self, research_type: Optional[str] = None) -> list:
        """List all research documents, optionally filtered by type"""
        documents = []
        metadata_dir = self.base_path / "metadata"
        
        for metadata_file in metadata_dir.glob("*.json"):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
                if research_type is None or metadata.get('research_type') == research_type:
                    documents.append(metadata)
        
        # Sort by creation date, newest first
        documents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return documents
    
    def archive_document(self, task_id: str) -> bool:
        """Move document to archives folder"""
        try:
            document_path = self.get_document_path(task_id)
            if document_path and os.path.exists(document_path):
                # Move to archives
                source = Path(document_path)
                destination = self.base_path / "archives" / source.name
                source.rename(destination)
                
                # Update metadata
                metadata_file = self.base_path / "metadata" / f"{task_id}.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    metadata['archived'] = True
                    metadata['archived_at'] = datetime.now().isoformat()
                    metadata['file_path'] = str(destination)
                    
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error archiving document: {e}")
        
        return False

# Initialize document manager
research_docs = ResearchDocumentManager()

if __name__ == "__main__":
    # Test the document manager
    print("✅ Research Document Manager initialized")
    print(f"📁 Base path: {research_docs.base_path}")
    
    # List existing documents
    docs = research_docs.list_documents()
    print(f"📄 Found {len(docs)} existing documents")
