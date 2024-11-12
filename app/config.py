import os

from dotenv import load_dotenv
from patisson_request.core import SelfAsyncService
from patisson_request.services import Service

load_dotenv()

SERVICE_NAME: str = Service.USERS.value
SERVICE_HOST: str = os.getenv("SERVICE_HOST")  # type: ignore[reportArgumentType]

DATABASE_URL: str = os.getenv("DATABASE_URL")  # type: ignore[reportArgumentType]

EXTERNAL_SERVICES: list[Service] = [Service.AUTHENTICATION, Service.BOOKS]

PATH_TO_GSCHEMA = '/api/graphql/schema.graphql'

SelfService = SelfAsyncService(
    self_service=Service(SERVICE_NAME),
    login=os.getenv("LOGIN"),  # type: ignore[reportArgumentType]
    password=os.getenv("PASSWORD"),  # type: ignore[reportArgumentType]
    external_services=EXTERNAL_SERVICES,
)