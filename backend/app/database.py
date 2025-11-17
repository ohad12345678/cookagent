"""
Database configuration and models
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://payslip_user:payslip_pass@db:5432/payslip_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Payslip(Base):
    """
    טבלת תלושי שכר
    """
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True)

    # File info
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    # Employee info
    employee_name = Column(String)
    employee_id = Column(String)
    department = Column(String)

    # Period
    month = Column(String)
    year = Column(String)

    # Salary
    base_salary = Column(Float)
    gross_salary = Column(Float)
    net_salary = Column(Float)
    final_payment = Column(Float)  # תשלום סופי

    # Hours
    work_hours = Column(Float)  # שעות עבודה
    overtime_hours = Column(Float)  # שעות נוספות

    # Days
    vacation_days = Column(Float)  # ימי חופש
    sick_days = Column(Float)  # ימי מחלה

    # Parsed data (full JSON)
    from sqlalchemy.ext.mutable import MutableDict
    parsed_data = Column(MutableDict.as_mutable(JSON))

    # Validation results
    is_valid = Column(Boolean)
    validation_issues = Column(JSON)

    # Analysis results
    has_anomalies = Column(Boolean)
    anomalies = Column(JSON)

    # Full report
    report = Column(JSON)

    # Raw text extracted from PDF
    raw_text = Column(Text)


class FeedbackEntry(Base):
    """
    טבלת feedback מהמשתמש
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    feedback_type = Column(String)  # false_positive, missing_issue, pattern, etc.
    agent_name = Column(String)

    context = Column(JSON)
    user_input = Column(Text)
    correction = Column(JSON)

    processed = Column(Boolean, default=False)
    processing_result = Column(JSON)


class LearningPattern(Base):
    """
    טבלת patterns שנלמדו
    """
    __tablename__ = "learning_patterns"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    pattern_type = Column(String)  # validation_rule, anomaly_threshold, etc.
    description = Column(Text)
    pattern_data = Column(JSON)

    source = Column(String)  # user_feedback, auto_learned, etc.
    active = Column(Boolean, default=True)


class ChatHistory(Base):
    """
    טבלת היסטוריית צ'אט
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    role = Column(String, nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)

    # Additional context
    tools_used = Column(JSON)  # List of tools used in this message
    extra_data = Column(JSON)  # Any additional metadata


class AgentLearning(Base):
    """
    טבלת למידה עצמית של הסוכן
    """
    __tablename__ = "agent_learning"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    learning_type = Column(String, nullable=False)  # 'correction', 'preference', 'pattern', etc.
    context = Column(JSON)  # What was the context when this was learned
    learned_data = Column(JSON)  # What was learned

    confidence = Column(Float, default=1.0)  # Confidence level (0-1)
    times_used = Column(Integer, default=0)  # How many times this learning was applied
    success_rate = Column(Float, default=1.0)  # Success rate when applied

    active = Column(Boolean, default=True)


class KnowledgeInsight(Base):
    """
    טבלת insights ומידע שנלמד לאורך זמן
    """
    __tablename__ = "knowledge_insights"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Category of insight
    category = Column(String, index=True, nullable=False)  # 'employee_preference', 'correction', 'domain_knowledge', etc.

    # The insight itself
    key = Column(String, index=True, nullable=False)  # Unique identifier (e.g., 'employee_name_HAO_vs_ZHAO')
    value = Column(JSON, nullable=False)  # The actual insight data

    # Metadata
    source_session_id = Column(String)  # Which session generated this
    importance = Column(Float, default=0.5)  # How important is this (0-1)

    # Usage stats
    times_applied = Column(Integer, default=0)
    last_applied = Column(DateTime)

    active = Column(Boolean, default=True)


class SavedKPI(Base):
    """
    טבלת KPIs שנוצרו על ידי Analyzer Agent
    """
    __tablename__ = "saved_kpis"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # KPI definition
    name = Column(String, nullable=False, index=True)
    description = Column(String)

    # Parameters
    metric = Column(String, nullable=False)  # sick_days, vacation_days, work_hours, gross_salary, net_salary
    aggregation = Column(String, nullable=False)  # average, sum, min, max, count
    group_by = Column(String, nullable=False)  # department, employee, month, none

    # Results (last calculated)
    results = Column(JSON)  # The actual KPI values

    # Metadata
    created_by_session = Column(String)
    active = Column(Boolean, default=True)


class Employee(Base):
    """
    טבלת עובדים - לשמירת שמות עובדים
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, nullable=False, index=True)  # מספר עובד
    employee_name = Column(String, nullable=False)  # שם עובד
    department = Column(String)  # מחלקה
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """
    יצירת הטבלאות
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency לקבלת session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
