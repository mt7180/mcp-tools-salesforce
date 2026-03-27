"""
Insert a nested record into a Salesforce scratch org via the Composite Tree REST API.

Usage:
    python scripts/insert_record.py <RootSObjectName> <payload.json>

Credentials are read from a .env file (or environment) via pydantic-settings.
"""

import json
import sys
import argparse

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
    parser = argparse.ArgumentParser(
        description="Insert nested Salesforce records via Composite Tree API."
    )
    parser.add_argument("root_sobject", help="Root sObject API name (e.g. Account)")
    parser.add_argument(
        "record_file",
        help="Path to JSON file containing the record payload (Composite Tree format)",
    )
    args = parser.parse_args()

    with open(args.record_file) as f:
        record_payload = json.load(f)

    settings = Settings()
    sf = get_sf_client(settings)

    endpoint = f"composite/tree/{args.root_sobject}/"
    response = sf.restful(endpoint, method="POST", json=record_payload)

    print(json.dumps(response, indent=2))

    if response.get("hasErrors"):
        print("\nERROR: Salesforce reported insertion errors.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
