import enum
import re
from datetime import datetime

from db.base import Base
from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship, validates
from ulid import ULID
from patisson_request.errors import ValidateError

def ulid() -> str:
    return str(ULID())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    
    library = relationship('Library', back_populates='user')
    ban = relationship('Ban', back_populates='user')
    
    def set_password(self, password: str) -> None:
        regex = re.compile(
            r'^(?!.*(.)\1{3})(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_])[a-zA-Z\d\W_]{6,24}$'
        )
        if (not regex.match(password) or sum(c.isalpha() for c in password) 
            <= sum(c.isdigit() for c in password)):
            raise ValidateError(f'the password is invalid')
        self.password = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)  # type: ignore[reportArgumentType]
    
    @validates("username")
    def validate_username(self, key, value: str):
        if not re.match(r'^[A-Za-z]{3}[A-Za-z0-9]{1,21}$', value):
            raise ValidateError(f'the username ({value}) is invalid')
        return value
    
    @validates('first_name')
    def validate_first_name(self, key, value: str):
        if not re.match(r'^[A-Za-z]{2,18}$', value):
            raise ValidateError(f"the first name ({value}) is invalid")
        return value.capitalize()
    
    @validates('last_name')
    def validate_last_name(self, key, value: str):
        if not re.match(r'^[A-Za-z]{2,18}$', value):
            raise ValidateError(f"the last name ({value}) is invalid")
        return value.capitalize()
    
    
class Library(Base):
    __tablename__ = 'libraries'
    
    class Status(enum.Enum):
        PLANNING = 0
        READING = 1
        FINISHED = 2
    
    id = Column(String, primary_key=True, default=ulid)
    book_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(Status), nullable=False)
    
    user = relationship('User', back_populates='library')
        
    
class Ban(Base):
    __tablename__ = 'bans'
    
    class Reason(enum.Enum):
        INAPPROPRIATE_BEHAVIOR = 0
    
    id = Column(String, primary_key=True, default=ulid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    reason = Column(Enum(Reason), nullable=False)
    comment = Column(Text)
    end_date = Column(DateTime)
    
    user = relationship('User', back_populates='ban')
    
    @validates('end_date')
    def validate_end_date(self, key, value: datetime):
        if value < datetime.now():
            raise ValidateError(f'The end date of the ban must be greater than the current time (recived {value})')
        return value