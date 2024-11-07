import config
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from opentelemetry import trace
from patisson_request.depends import (dep_jaeger_decorator,
                                      verify_service_token_dep)
from patisson_request.errors import InvalidJWT
from patisson_request.jwt_tokens import ServiceAccessTokenPayload

security = HTTPBearer()
tracer = trace.get_tracer(__name__)

@dep_jaeger_decorator(tracer)
async def verify_service_token(credentials: HTTPAuthorizationCredentials 
                               = Depends(security)) -> ServiceAccessTokenPayload:
    token = credentials.credentials
    try:
        payload = await verify_service_token_dep(
            self_service=config.SelfService, access_token=token)
    except InvalidJWT as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.error_schema
            )
    return payload
    