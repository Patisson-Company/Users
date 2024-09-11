import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME: str = f'authentication.{os.getenv("SERVICE_ID")}'
SERVICE_HOST: str = os.getenv("SERVICE_HOST")  # type: ignore[reportArgumentType]
SERVICE_PORT = int(os.getenv("SERVICE_PORT"))  # type: ignore[reportArgumentType]

DATABASE_URL: str = os.getenv("DATABASE_URL")  # type: ignore[reportArgumentType]