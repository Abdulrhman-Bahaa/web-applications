# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Samples(db.Model):

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    hash_md5 = db.Column(db.CHAR(32), unique=True, nullable=False)
    hash_sha1 = db.Column(db.CHAR(40), unique=True)
    hash_sha256 = db.Column(db.CHAR(64), unique=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger)
    file_type = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Sample id={self.id} file_name={self.file_name}>"
