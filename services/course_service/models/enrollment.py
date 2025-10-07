from sqlalchemy import Column, Integer, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Enrollment(Base):
    __tablename__ = 'enrollments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    enrolled_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (UniqueConstraint('user_id', 'course_id', name='uq_user_course'),)
