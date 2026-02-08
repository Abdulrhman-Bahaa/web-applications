from sqlalchemy import Column, Integer, String
from database import Base
from datetime import datetime
from sqlalchemy.types import DateTime
from sqlalchemy.types import Boolean


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hash_md5 = Column(String(32), unique=True, nullable=False)
    hash_sha1 = Column(String(40), unique=True)
    hash_sha256 = Column(String(64), unique=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(100))
    upload_date = Column(DateTime, default=datetime.now())
    static_analysis = Column(Boolean, default=False)
    dynamic_analysis = Column(Boolean, default=False)
