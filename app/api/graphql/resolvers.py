from typing import Optional

from api.graphql.deps import verify_tokens_decorator
from ariadne import QueryType
from config import logger
from db.crud import users_ban_subquery
from db.models import Library, User
from graphql import GraphQLResolveInfo
from patisson_graphql.framework_utils.fastapi import GraphQLContext
from patisson_graphql.selected_fields import selected_fields
from patisson_graphql.stmt_filter import Stmt
from patisson_request.jwt_tokens import ServiceAccessTokenPayload
from sqlalchemy.future import select

query = QueryType()


@query.field("users")
@verify_tokens_decorator
async def users(_, info: GraphQLResolveInfo, 
                service_token: ServiceAccessTokenPayload,
                ids: Optional[list[str]] = None,
                usernames: Optional[list[str]] = None,
                first_names: Optional[list[str]] = None,
                last_names: Optional[list[str]] = None,
                roles: Optional[list[str]] = None,
                is_banned: Optional[bool] = None,
                offset: Optional[int] = None,
                limit: Optional[int] = 10):
    context: GraphQLContext[ServiceAccessTokenPayload, None] = info.context
    
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
    logger.info(stmt.log())
    result = await context.db_session.execute(stmt())
    return result.fetchall()


@query.field("libraries")
@verify_tokens_decorator
async def libraries(_, info: GraphQLResolveInfo,
                    service_token: ServiceAccessTokenPayload,
                    ids: Optional[list[str]] = None,
                    user_ids: Optional[list[str]] = None,
                    book_ids: Optional[list[str]] = None,
                    statuses: Optional[list[str]] = None,
                    offset: Optional[int] = None,
                    limit: Optional[int] = 10):
    context: GraphQLContext[ServiceAccessTokenPayload, None] = info.context
    
    stmt_selected_fields = selected_fields(info, Library)
    stmt = (
        Stmt(
            select(*stmt_selected_fields)
            )
        .con_filter(Library.id, ids)
        .con_filter(Library.user_id, user_ids)
        .con_filter(Library.book_id, book_ids)
        .con_filter(Library.status, statuses)
        .offset(offset).limit(limit).ordered_by(Library.id)
    )
    logger.info(stmt.log())
    result = await context.db_session.execute(stmt())
    return result.fetchall()

resolvers = [query]