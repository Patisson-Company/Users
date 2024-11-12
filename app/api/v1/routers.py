import config
from api.deps import (CreateBan_UserJWT, CreateLib_UserJWT, ServiceJWT,
                      SessionDep, UserReg_ServiceJWT)
from db.crud import create_ban, create_library, create_user
from fastapi import APIRouter, HTTPException, status
from patisson_request.roles import ClientRole
from patisson_request.service_requests import UsersRequest
from patisson_request.service_responses import SuccessResponse, TokensSet
from patisson_request.service_routes import AuthenticationRoute

from app.db.models import Ban, Library

router = APIRouter()

@router.post('/create-user')
async def create_user_route(
    service: UserReg_ServiceJWT, session: SessionDep, 
    user: UsersRequest.CreateUser) -> TokensSet:
    async with session as session_:  
        is_valid, body = await create_user(
            session=session_, 
            role=ClientRole.MEMBER.name, 
            username=user.username, 
            password=user.password, 
            first_name=user.first_name, 
            last_name=user.last_name, 
            avatar=user.avatar, 
            about=user.about
            )
     
    if is_valid:
        response = await config.SelfService.post_request(
            *-AuthenticationRoute.api.v1.client.jwt.create(
                client_id=str(body.id),  # type: ignore[reportAttributeAccessIssue]
                client_role=ClientRole(str(body.role)), # type: ignore[reportAttributeAccessIssue]
                expire_in=user.expire_in
            )
        )
        return TokensSet(
            access_token=response.body.access_token,
            refresh_token=response.body.refresh_token
        )
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=[body.model_dump()]
            )
        
 
@router.post('/create-library')
async def create_library_route(
    service: ServiceJWT, user: CreateLib_UserJWT, 
    session: SessionDep, library: UsersRequest.CreateLibrary
    ) -> SuccessResponse:
    async with session as session_: 
        is_valid, body = await create_library(
            session=session_, 
            book_id=library.book_id,
            user_id=library.user_id, 
            status=Library.Status(library.status))
    if is_valid:
        return SuccessResponse()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=[body.model_dump()]
            )
 

@router.post('/create-ban')
async def create_ban_route(
    service: ServiceJWT, user: CreateBan_UserJWT, 
    session: SessionDep, ban: UsersRequest.CreateBan
    ) -> SuccessResponse:
    async with session as session_: 
        is_valid, body = await create_ban(
            session=session_, 
            user_id=ban.user_id,
            reason=Ban.Reason(ban.reason),
            comment=ban.comment,
            end_date=ban.end_date
            )
    if is_valid:
        return SuccessResponse()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=[body.model_dump()]
            )
 