
from sqlalchemy import Column, String, Integer, DateTime

from .base import Base


class Worker(Base) :
    __tablename__ = "worker"

    id = Column(Integer, primary_key=True, index=True)
    worker_name = Column(String(255) , nullable=False)
