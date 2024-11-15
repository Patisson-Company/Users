import config
from api.deps import (CreateBan_UserJWT, CreateLib_UserJWT, ServiceJWT,
                      SessionDep, UserReg_ServiceJWT)
from db.crud import create_ban, create_library, create_user, get_active_user
from db.models import Ban, Library
from fastapi import APIRouter, Header, HTTPException, status
from patisson_request.errors import ErrorSchema
from patisson_request.roles import ClientRole
from patisson_request.service_requests import UsersRequest
from patisson_request.service_responses import SuccessResponse, TokensSet, VerifyUser, UsersResponse
from patisson_request.service_routes import AuthenticationRoute

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
    
    
@router.post('/verify-user')
async def verify_user_route(
    service: ServiceJWT, session: SessionDep, body: UsersRequest.VerifyUser
    ) -> VerifyUser:
    response = await config.SelfService.post_request(
        *-AuthenticationRoute.api.v1.client.jwt.verify(body.access_token)
    )
    if not response.body.is_verify:
        return VerifyUser(is_verify=False, payload=None, error=ErrorSchema(
            error=response.body.error.error  # type: ignore[reportOptionalMemberAccess]
        ))
    
    async with session as session_:
        is_valid, body = await get_active_user(
            session=session_,
            user_id=response.body.payload.sub  # type: ignore[reportOptionalMemberAccess]
        )
    
    if is_valid:
        return VerifyUser(is_verify=True, payload=body)
    
    return VerifyUser(is_verify=False, payload=None, error=body)


@router.post('/update-user')
async def update_user_route(
    service: ServiceJWT, body: UsersRequest.UpdateUser, 
    session: SessionDep, X_Client_Token: str = Header(...)
    ) -> TokensSet:
    
    verify_response = await config.SelfService.post_request(
        *-AuthenticationRoute.api.v1.client.jwt.verify(X_Client_Token)
    )
    if not verify_response.body.is_verify:
       raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorSchema(
                error=verify_response.body.error.error  # type: ignore[reportOptionalMemberAccess]  
                ).model_dump()
            )
       
    async with session as session_:
        is_valid, body_= await get_active_user(
            session=session_,
            user_id=verify_response.body.payload.sub  # type: ignore[reportOptionalMemberAccess]
        )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=body_.model_dump()
            )
        
    update_response = await config.SelfService.post_request(
        *-AuthenticationRoute.api.v1.client.jwt.update(
            client_access_token=X_Client_Token,
            client_refresh_token=body.refresh_token
            )
        )
    if update_response.is_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=update_response.body.model_dump()
        )
    
    return update_response.body