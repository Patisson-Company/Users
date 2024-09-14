from typing import Optional

from ariadne import QueryType
from db.crud import users_ban_subquery
from db.models import User
from graphql import GraphQLResolveInfo
from patisson_graphql.selected_fields import selected_fields
from patisson_graphql.stmt_filter import Stmt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

query = QueryType()


@query.field("users")
async def users(_, info: GraphQLResolveInfo, 
                ids: Optional[list[str]] = None,
                usernames: Optional[list[str]] = None,
                first_names: Optional[list[str]] = None,
                last_names: Optional[list[str]] = None,
                roles: Optional[list[str]] = None,
                is_banned: Optional[bool] = None,
                offset: Optional[int] = None,
                limit: Optional[int] = 10):
    db: AsyncSession = info.context["db"]
    
    stmt_selected_fields = selected_fields(info, User)
    is_banned_field = None
    if is_banned is not None:
        is_banned_field = users_ban_subquery()
        stmt_selected_fields.append(is_banned_field)  # type: ignore[reportArgumentType]
        
    stmt = (
        Stmt(
            select(*stmt_selected_fields)
            )
        .con_filter(User.id, ids)
        .con_filter(User.username, usernames)
        .con_filter(User.first_name, first_names)
        .con_filter(User.last_name, last_names)
        .con_filter(User.role, roles)
        .where_filter(is_banned_field, is_banned)  # type: ignore[reportArgumentType]
        .offset(offset).limit(limit).ordered_by(User.id)
    )
    result = await db.execute(stmt())
    return result.fetchall()


resolvers = [query]