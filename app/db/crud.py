from typing import Literal, Optional

import patisson_errors
from ariadne import MutationType, QueryType
from db.models import Ban, User
from graphql import GraphQLResolveInfo
from patisson_graphql.selected_fields import selected_fields
from patisson_graphql.stmt_filter import Stmt
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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
                          | tuple[Literal[False], patisson_errors.ErrorSchema]
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
        return False, patisson_errors.ErrorSchema(
            error=patisson_errors.ErrorCode.ACCESS_ERROR,
            extra=str(e)
        )
        
    except ValueError as e:  # sqlalchemy model validators
        return False, patisson_errors.ErrorSchema(
            error=patisson_errors.ErrorCode.JWT_EXPIRED,
            extra=str(e)
        )
        
    