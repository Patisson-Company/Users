from datetime import datetime
from typing import Literal, Optional

from db.models import Ban, Library, User
from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from patisson_request.errors import ErrorCode, ErrorSchema, ValidateError


def users_ban_subquery():
    active_ban_subquery = (
        select(func.count(Ban.id))
        .where(
            and_(
                Ban.user_id == User.id,
                or_(
                    Ban.end_date == None, 
                    Ban.end_date > func.now()
                )
            )
        )
    )
    return case(       
        (active_ban_subquery.scalar_subquery() > 0, True),
        else_=False
        ).label("is_banned")
    

async def create_user(session: AsyncSession, role: str,
                      username: str, password: str, 
                      first_name: Optional[str] = None,
                      last_name: Optional[str] = None,
                      avatar: Optional[str] = None,
                      about: Optional[str] = None,
                      ) -> (
                          tuple[Literal[True], User]
                          | tuple[Literal[False], ErrorSchema]
                      ):
    '''
    Makes an asynchronous request to the database. 
    If all the passed fields are correct,
    it will return User (db.models), else it will return None
    '''
    try:
        user = User(
            username=username, first_name=first_name,
            last_name=last_name, avatar=avatar,
            about=about, role=role
        )
        user.set_password(password)
        session.add(user)
        await session.commit()
        return True, user
    
    except SQLAlchemyError as e:
        await session.rollback()
        return False, ErrorSchema(
            error=ErrorCode.INVALID_PARAMETERS,
            extra=str(e)
        )
        
    except ValidateError as e: 
        return False, ErrorSchema(
            error=ErrorCode.VALIDATE_ERROR,
            extra=str(e)
        )
        

async def create_library(session: AsyncSession, book_id: str,
                         user_id: str, status: Library.Status) -> (
                          tuple[Literal[True], Library]
                          | tuple[Literal[False], ErrorSchema]
                      ):
    try:
        library = Library(
            book_id=book_id, user_id=user_id,
            status=status
        )
        
        record_exists = await session.scalar(
            select(exists().where(Library.user_id == user_id, Library.book_id == book_id))
        )
        if record_exists:
            return False, ErrorSchema(
                error=ErrorCode.ACCESS_ERROR,
                extra=f"The user ({user_id}) already has this book ({book_id}) in their library"
            )
            
        session.add(library)
        await session.commit()
        return True, library
    
    except IntegrityError:
        await session.rollback()
        return False, ErrorSchema(
            error=ErrorCode.INVALID_PARAMETERS,
            extra=f'The user ({user_id}) was not found'
        )
        
    except SQLAlchemyError as e:
        await session.rollback()
        return False, ErrorSchema(
            error=ErrorCode.INVALID_PARAMETERS,
            extra=str(e)
        )
    
    except ValidateError as e: 
        await session.rollback()
        return False, ErrorSchema(
            error=ErrorCode.VALIDATE_ERROR,
            extra=str(e)
        )


async def create_ban(session: AsyncSession, user_id: str,
                     reason: Ban.Reason, comment: str, end_date: datetime) -> ( 
                        tuple[Literal[True], User]
                        | tuple[Literal[False], ErrorSchema]
                      ):
    try:
        ban = Ban(
            user_id=user_id, reason=reason, 
            comment=comment, end_date=end_date
        )
        session.add(ban)
        await session.commit()
        return True, ban
    
    except IntegrityError:
        await session.rollback()
        return False, ErrorSchema(
            error=ErrorCode.INVALID_PARAMETERS,
            extra=f'The user ({user_id}) was not found'
        )
        
    except SQLAlchemyError as e:
        await session.rollback()
        return False, ErrorSchema(
            error=ErrorCode.INVALID_PARAMETERS,
            extra=str(e)
        )
    
    except ValidateError as e:
        return False, ErrorSchema(
            error=ErrorCode.VALIDATE_ERROR,
            extra=str(e)
        )