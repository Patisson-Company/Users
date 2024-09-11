from db.base import Base
from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from ulid import ULID

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def ulid() -> str:
    return str(ULID())


class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=ulid)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    avatar = Column(String)
    about = Column(Text)
    role = Column(String, nullable=False)
    
    Library = relationship('Library', back_populates='user')
    ban = relationship('Ban', back_populates='user')
    
    def set_password(self, password: str) -> None:
        self.password = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)
    
    
class Library(Base):
    __tablename__ = 'libraries'
    
    id = Column(String, primary_key=True, default=ulid)
    book_id = Column(String, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    status = Column(String, nullable=False)
    
    user = relationship('User', back_populates='library')
    
    
class Ban(Base):
    __tablename__ = 'bans'
    
    id = Column(String, primary_key=True, default=ulid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    reason = Column(String, nullable=False)
    comment = Column(Text)
    end_date = Column(DateTime)
    
    user = relationship('User', back_populates='ban')