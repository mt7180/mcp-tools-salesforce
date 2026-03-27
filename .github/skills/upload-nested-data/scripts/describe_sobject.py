"""
Describe the creatable fields of a Salesforce sObject.

Usage:
    python scripts/describe_sobject.py <SObjectName>

Credentials are read from a .env file (or environment) via pydantic-settings
"""

import json
import sys

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
        raise ValueError("Either PRIVATE_KEY_FILE or PRIVATE_KEY must be set.")
    return Salesforce(
        username=settings.USERNAME,
        consumer_key=settings.CLIENT_ID,
        privatekey=private_key,
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python describe_sobject.py <SObjectName>", file=sys.stderr)
        sys.exit(1)

    sobject_name = sys.argv[1]
    settings = Settings()
    sf = get_sf_client(settings)

    description = sf.__getattr__(sobject_name).describe()

    if not description.get("createable"):
        print(json.dumps({}))
        return

    creatable_fields = {
        field["name"]: {"type": field["type"], "nillable": field["nillable"]}
        for field in description["fields"]
        if field["createable"]
    }

    print(json.dumps(creatable_fields, indent=2))


if __name__ == "__main__":
    main()
