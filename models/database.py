"""
Database Models for Research Platform
=====================================

This module defines the database schema for storing research results, ideas, and metadata.
Using SQLAlchemy ORM with SQLite for simplicity and portability.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import os

# Database setup
DATABASE_URL = "sqlite:///./research_platform.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ResearchTask(Base):
    """Stores research tasks and their execution details"""
    __tablename__ = "research_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    model = Column(String, nullable=False)  # o3-deep-research, o4-mini-research
    research_type = Column(String, nullable=False)  # custom, validation, market, financial, comprehensive
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(String, default="Task created")
    enrich_prompt = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results storage
    result_data = Column(JSON, nullable=True)  # Store complete research result
    error_message = Column(Text, nullable=True)
    
    # File paths for MD documents
    md_document_path = Column(String, nullable=True)
    
    # Relationships
    research_results = relationship("ResearchResult", back_populates="task", cascade="all, delete-orphan")

class ResearchResult(Base):
    """Stores processed research results for dashboard display"""
    __tablename__ = "research_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("research_tasks.task_id"))
    
    # Basic info
    idea_name = Column(String, index=True)
    description = Column(Text)
    industry = Column(String, index=True)
    
    # Scores and metrics
    market_opportunity_score = Column(Float, default=0)
    technical_feasibility_score = Column(Float, default=0)
    competitive_advantage_score = Column(Float, default=0)
    risk_level = Column(Integer, default=5)
    
    # Market analysis
    total_addressable_market = Column(String, nullable=True)
    target_market_size = Column(String, nullable=True)
    customer_segments = Column(JSON, nullable=True)  # Array of strings
    growth_rate = Column(String, nullable=True)
    
    # Research metadata
    total_citations = Column(Integer, default=0)
    research_depth_score = Column(Float, default=0)
    validation_sources = Column(Integer, default=0)
    competitor_analysis_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    
    # Financial projections
    development_cost = Column(String, nullable=True)
    time_to_market = Column(String, nullable=True)
    break_even_timeline = Column(String, nullable=True)
    projected_revenue_y1 = Column(String, nullable=True)
    projected_revenue_y3 = Column(String, nullable=True)
    
    # Status tracking
    validation_status = Column(String, default="initial")  # initial, in-progress, validated, ready
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("ResearchTask", back_populates="research_results")

class IdeaPortfolio(Base):
    """Aggregated view of ideas for portfolio management"""
    __tablename__ = "idea_portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic info
    idea_name = Column(String, index=True, nullable=False)
    description = Column(Text)
    industry = Column(String, index=True)
    
    # Latest research data (from most recent research)
    latest_task_id = Column(String, ForeignKey("research_tasks.task_id"))
    research_model = Column(String)
    status = Column(String, default="initial")
    
    # Aggregated scores (from latest research)
    market_opportunity_score = Column(Float, default=0)
    technical_feasibility_score = Column(Float, default=0)
    competitive_advantage_score = Column(Float, default=0)
    risk_level = Column(Integer, default=5)
    
    # Portfolio tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    last_research = Column(DateTime, nullable=True)
    research_count = Column(Integer, default=0)  # Number of times researched
    
    # Tags and categorization
    tags = Column(JSON, nullable=True)  # Array of strings
    priority = Column(String, default="medium")  # low, medium, high
    archived = Column(Boolean, default=False)

class SystemMetrics(Base):
    """Stores system-wide metrics for dashboard"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Calculated metrics
    total_ideas = Column(Integer, default=0)
    avg_market_score = Column(Float, default=0)
    ideas_ready_for_development = Column(Integer, default=0)
    total_market_opportunity = Column(String, default="$0")
    new_ideas_this_month = Column(Integer, default=0)
    avg_research_depth = Column(Float, default=0)
    validation_success_rate = Column(Float, default=0)
    
    # Usage statistics
    total_research_tasks = Column(Integer, default=0)
    completed_research_tasks = Column(Integer, default=0)
    failed_research_tasks = Column(Integer, default=0)
    
    # Industry breakdown (JSON)
    industry_distribution = Column(JSON, nullable=True)

# Database initialization functions
def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables and sample data if needed"""
    create_tables()
    print("✅ Database tables created successfully")

if __name__ == "__main__":
    init_database()
