from pydantic_settings import BaseSettings, SettingsConfigDict
from simple_salesforce import Salesforce
from pathlib import Path

BASEDIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    CLIENT_ID: str
    USERNAME: str
    PRIVATE_KEY_FILE: str | None = None
    PRIVATE_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=BASEDIR / ".env", extra="ignore")

def get_sf_client() -> Salesforce:

    settings = Settings()

    private_key = settings.PRIVATE_KEY
    if settings.PRIVATE_KEY_FILE:
        with open(settings.PRIVATE_KEY_FILE) as f:
            private_key = f.read()

    if not private_key:
        raise ValueError("Missing private key")

    return Salesforce(
        username=settings.USERNAME,
        consumer_key=settings.CLIENT_ID,
        privatekey=private_key,
    )