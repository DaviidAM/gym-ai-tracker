from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    muscle_group = Column(String, nullable=True)
    equipment = Column(String, nullable=True)


class ExerciseSynonym(Base):
    __tablename__ = "exercise_synonyms"
    __table_args__ = (
        UniqueConstraint("exercise_id", "synonym", name="uq_exercise_synonym_pair"),
    )

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    synonym = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
