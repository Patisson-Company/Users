from typing import Annotated

import config
from db.base import get_session
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from opentelemetry import trace
from patisson_request.depends import (dep_jaeger_client_decorator,
                                      dep_jaeger_service_decorator,
                                      verify_client_token_dep,
                                      verify_service_token_dep)
from patisson_request.errors import ErrorCode, ErrorSchema, InvalidJWT
from patisson_request.jwt_tokens import (ClientAccessTokenPayload,
                                         ServiceAccessTokenPayload)
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()
tracer = trace.get_tracer(__name__)

@dep_jaeger_service_decorator(tracer)
async def verify_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> ServiceAccessTokenPayload:
    token = credentials.credentials
    try:
        payload = await verify_service_token_dep(
            self_service=config.SelfService, access_token=token)
    except InvalidJWT as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[e.error_schema.model_dump()]
            )
    return payload


async def verify_serice__user_reg__token(
    payload: ServiceAccessTokenPayload = Depends(verify_service_token)
    ) -> ServiceAccessTokenPayload:
    REQUIRED_PERM = [
        payload.role.permissions.user_reg
    ]
    if not all(REQUIRED_PERM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[ErrorSchema(
                error=ErrorCode.ACCESS_ERROR
                ).model_dump()]
            )
    return payload


@dep_jaeger_client_decorator(tracer)
async def verify_user_token(
    X_Client_Token: str = Header(...)
    ) -> ClientAccessTokenPayload:
    try:
        payload = await verify_client_token_dep(
            self_service=config.SelfService,
            access_token=X_Client_Token
        )
    except InvalidJWT as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[e.error_schema.model_dump()]
            )
    return payload


async def verify_user__create_lib__token(
    payload: ClientAccessTokenPayload = Depends(verify_user_token)
    ) -> ClientAccessTokenPayload:
    REQUIRED_PERM = [
        payload.role.permissions.create_lib
    ]
    if not all(REQUIRED_PERM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[ErrorSchema(
                error=ErrorCode.ACCESS_ERROR
                ).model_dump()]
            )
    return payload


async def verify_user__create_ban__token(
    payload: ClientAccessTokenPayload = Depends(verify_user_token)
    ) -> ClientAccessTokenPayload:
    REQUIRED_PERM = [
        payload.role.permissions.create_ban
    ]
    if not all(REQUIRED_PERM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[ErrorSchema(
                error=ErrorCode.ACCESS_ERROR
                ).model_dump()]
            )
    return payload


SessionDep = Annotated[AsyncSession, Depends(get_session)]

ServiceJWT = Annotated[ServiceAccessTokenPayload, Depends(verify_service_token)]
UserReg_ServiceJWT = Annotated[ServiceAccessTokenPayload, Depends(verify_serice__user_reg__token)]

UserJWT = Annotated[ClientAccessTokenPayload, Depends(verify_user_token)]
CreateBan_UserJWT = Annotated[ClientAccessTokenPayload, Depends(verify_user__create_ban__token)]
CreateLib_UserJWT = Annotated[ClientAccessTokenPayload, Depends(verify_user__create_lib__token)]