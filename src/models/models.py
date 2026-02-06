import uuid

from sqlalchemy import Integer, String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base



class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    weight: Mapped[float] = mapped_column(Float())
    height: Mapped[float] = mapped_column(Float())
    age: Mapped[int] = mapped_column(Integer())
    target_weight: Mapped[float]= mapped_column(Float())
    sex: Mapped[str] = mapped_column(String())
    activity_level: Mapped[str] = mapped_column(String())
    bmr: Mapped[int] = mapped_column(Integer(), default=-1)
    base_calorie_intake: Mapped[int] = mapped_column(Integer(), default=-1)
    calorie_intake: Mapped[int] = mapped_column(Integer(), default=-1)
    weight_check : Mapped[list[float]] = mapped_column(JSON, default=[])