"""
This module contains functions and decorators for verifying service and client tokens
in GraphQL requests. It integrates OpenTelemetry tracing and handles errors related 
to invalid or missing tokens.

Functions:
    verify_service_token: Verifies the service token from the request headers.
    verify_client_token: Verifies the client token from the request headers.
    verify_tokens_decorator: A decorator to verify service and client tokens for GraphQL resolvers.
"""

import inspect
from functools import wraps

import config
from fastapi.security import HTTPBearer
from graphql import GraphQLError, GraphQLResolveInfo
from opentelemetry import trace
from patisson_graphql.framework_utils.fastapi import GraphQLContext
from patisson_request.depends import (dep_opentelemetry_client_decorator,
                                      dep_opentelemetry_service_decorator,
                                      verify_client_token_dep,
                                      verify_service_token_dep)
from patisson_request.errors import ErrorCode, ErrorSchema, InvalidJWT
from patisson_request.jwt_tokens import (ClientAccessTokenPayload,
                                         ServiceAccessTokenPayload)

security = HTTPBearer()
tracer = trace.get_tracer(__name__)

@dep_opentelemetry_service_decorator(tracer)
async def verify_service_token(context: GraphQLContext) -> ServiceAccessTokenPayload:
    """
    Verifies the service token from the request headers.

    Args:
        context (GraphQLContext): The GraphQL context containing the request.

    Returns:
        ServiceAccessTokenPayload: The decoded service token payload.

    Raises:
        GraphQLError: If the token is missing or invalid, a GraphQL error is raised with the details.

    Notes:
        This function expects the token to be in the 'Authorization' header of the request.
    """
    try:
        token_header = context.request.headers.get("Authorization")
        if not token_header: 
            raise InvalidJWT(error=ErrorSchema(
                error=ErrorCode.JWT_INVALID,
                extra='The server token is incorrect (missing or empty)'
            ))
        payload = await verify_service_token_dep(
            self_service=config.SelfService, 
            access_token=config.SelfService.extract_token_from_header(token_header)[1:]
            )
    except InvalidJWT as e:
        raise GraphQLError(
            message=str(e.error_schema.error),
            extensions={
                "details": e.error_schema.extra,
            },
        )
    return payload


@dep_opentelemetry_client_decorator(tracer)
async def verify_client_token(context: GraphQLContext) -> ClientAccessTokenPayload:
    """
    Verifies the client token from the request headers.

    Args:
        context (GraphQLContext): The GraphQL context containing the request.

    Returns:
        ClientAccessTokenPayload: The decoded client token payload.

    Raises:
        GraphQLError: If the token is missing or invalid, a GraphQL error is raised with the details.

    Notes:
        This function expects the token to be in the 'X-Token-Client' header of the request.
    """
    try:
        token = context.request.headers.get("X-Client-Token")
        if not token: 
            raise InvalidJWT(error=ErrorSchema(
                error=ErrorCode.CLIENT_JWT_INVALID,
                extra='The server token is incorrect (missing or empty)'
            ))
        payload = await verify_client_token_dep(
            self_service=config.SelfService, 
            access_token=token
            )
    except InvalidJWT as e:
        raise GraphQLError(
            message=str(e.error_schema.error),
            extensions={
                "details": e.error_schema.extra,
            },
        )
    return payload
        
        
def verify_tokens_decorator(func):
    """
    A decorator that verifies service and client tokens before executing the GraphQL resolver.

    Args:
        func (Callable): The original GraphQL resolver function.

    Returns:
        Callable: The wrapped resolver function with token verification.

    Notes:
        This decorator checks the function signature for the presence of 'service_token' and
        'user_token' arguments and automatically verifies the corresponding tokens before calling
        the resolver. The verified tokens are passed to the resolver as arguments.
    """
    
    @wraps(func)
    async def wrapper(root, info: GraphQLResolveInfo, **kwargs):
        func_signature_arguments = [param.name for param in 
                                    inspect.signature(func).parameters.values()]
        func_kwargs = {}
        if (service:='service_token') in func_signature_arguments: 
            func_kwargs[service] = await verify_service_token(info.context)
        if (user:='client_token') in func_signature_arguments: 
            func_kwargs[user] = await verify_client_token(info.context)
        return await func(root, info, **func_kwargs, **kwargs)
    
    return wrapper