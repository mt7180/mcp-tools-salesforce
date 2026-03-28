# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "simple-salesforce",
#   "pydantic-settings",
# ]
# ///

import argparse
import json
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from simple_salesforce import Salesforce

BASE_DIR = Path(__file__).parent.parent.parent.parent

class Settings(BaseSettings):
    CLIENT_ID: str
    USERNAME: str
    PRIVATE_KEY_FILE: str | None = None
    PRIVATE_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


def get_sf_client() -> Salesforce:
    settings = Settings()
    private_key = settings.PRIVATE_KEY
    if settings.PRIVATE_KEY_FILE:
        key_path = Path(BASE_DIR / settings.PRIVATE_KEY_FILE)
        with key_path.open() as f:
            private_key = f.read()
    if not private_key:
        raise ValueError("Missing private key")
    return Salesforce(
        username=settings.USERNAME,
        consumer_key=settings.CLIENT_ID,
        privatekey=private_key,
    )


def describe_creatable_fields(sobject: str) -> dict:
    sf = get_sf_client()
    description = getattr(sf, sobject).describe()
    if not description.get("createable"):
        return {}
    return {
        field["name"]: {"type": field["type"], "nillable": field["nillable"]}
        for field in description["fields"]
        if field.get("createable")
    }


def fetch_metadata(sobject: str) -> dict:
    try:
        return {
            "status": "success",
            "data": describe_creatable_fields(sobject),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List creatable fields for an sObject.")
    parser.add_argument("sobject", help="API name of the sObject (e.g., Account)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    result = fetch_metadata(args.sobject)
    print(json.dumps(result))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
