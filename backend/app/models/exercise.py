from sqlalchemy import Column, Integer, String, ForeignKey, Float
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    muscle_group = Column(String, nullable=True)
    equipment = Column(String, nullable=True)


class ExerciseSynonym(Base):
    __tablename__ = "exercise_synonyms"

    id = Column(Integer, primary_key=True, index=True)
    canonical_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    synonym = Column(String, nullable=False, unique=True, index=True)
