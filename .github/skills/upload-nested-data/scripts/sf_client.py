from pydantic_settings import BaseSettings, SettingsConfigDict
from simple_salesforce import Salesforce


class Settings(BaseSettings):
    CLIENT_ID: str
    USERNAME: str
    PRIVATE_KEY_FILE: str | None = None
    PRIVATE_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def get_sf_client(settings: Settings) -> Salesforce:

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