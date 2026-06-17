"""
Database models for Finance Analyzer
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.models.domain import TransactionType

Base = declarative_base()


class TransactionDB(Base):
    """Database model for transactions"""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    amount = Column(Float, nullable=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    category = Column(String, nullable=True)
    item = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0)
    extracted_from = Column(Text, nullable=True)
    original_text = Column(Text, nullable=True)
    language_detected = Column(String, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'amount': self.amount,
            'transaction_type': self.transaction_type.value if self.transaction_type else None,
            'category': self.category,
            'item': self.item,
            'merchant': self.merchant,
            'confidence_score': self.confidence_score,
            'extracted_from': self.extracted_from,
            'original_text': self.original_text,
            'language_detected': self.language_detected,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AnalysisSessionDB(Base):
    """Database model for analysis sessions"""
    __tablename__ = "analysis_sessions"
    
    id = Column(String, primary_key=True)
    session_type = Column(String, nullable=False)  # 'text' or 'voice'
    original_input = Column(Text, nullable=True)
    transcribed_text = Column(Text, nullable=True)
    language_detected = Column(String, nullable=True)
    total_transactions = Column(Integer, default=0)
    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    processing_time_ms = Column(Integer, nullable=True)
    confidence_avg = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_type': self.session_type,
            'original_input': self.original_input,
            'transcribed_text': self.transcribed_text,
            'language_detected': self.language_detected,
            'total_transactions': self.total_transactions,
            'total_income': self.total_income,
            'total_expenses': self.total_expenses,
            'net_amount': self.net_amount,
            'processing_time_ms': self.processing_time_ms,
            'confidence_avg': self.confidence_avg,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserFeedbackDB(Base):
    """Database model for user feedback on transaction accuracy"""
    __tablename__ = "user_feedback"
    
    id = Column(String, primary_key=True)
    transaction_id = Column(String, nullable=False)
    original_category = Column(String, nullable=True)
    corrected_category = Column(String, nullable=True)
    original_item = Column(String, nullable=True)
    corrected_item = Column(String, nullable=True)
    original_amount = Column(Float, nullable=True)
    corrected_amount = Column(Float, nullable=True)
    feedback_type = Column(String, nullable=False)  # 'correction', 'confirmation'
    user_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'original_category': self.original_category,
            'corrected_category': self.corrected_category,
            'original_item': self.original_item,
            'corrected_item': self.corrected_item,
            'original_amount': self.original_amount,
            'corrected_amount': self.corrected_amount,
            'feedback_type': self.feedback_type,
            'user_comment': self.user_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }