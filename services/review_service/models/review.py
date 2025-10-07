from sqlalchemy import Column, Integer, Text, TIMESTAMP, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)
    comment = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (UniqueConstraint('user_id', 'course_id', name='uq_user_course_review'),)
