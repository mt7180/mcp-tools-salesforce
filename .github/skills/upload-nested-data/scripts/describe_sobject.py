import json
import asyncio
from pydantic_settings import BaseSettings, SettingsConfigDict
from simple_salesforce import Salesforce
from pathlib import Path

from sf_client import get_sf_client

BASEDIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    CLIENT_ID: str
    USERNAME: str
    PRIVATE_KEY_FILE: str | None = None
    PRIVATE_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=BASEDIR / ".env", extra="ignore")


def describe_creatable_fields(sobject_name: str) -> dict:
    settings = Settings()
    sf = get_sf_client(settings)

    description = getattr(sf, sobject_name).describe()

    if not description.get("createable"):
        return {}

    return {
        field["name"]: {
            "type": field["type"],
            "nillable": field["nillable"],
        }
        for field in description["fields"]
        if field["createable"]
    }


async def main(sobject: str) -> dict:
    try:
        return {
            "status": "success",
            "data": describe_creatable_fields(sobject),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }



if __name__ == "__main__":
    import sys
    
    # Check if argument is provided
    if len(sys.argv) < 2:
        error_result = {
            "status": "error",
            "error": "Missing required argument: sobject name"
        }
        print(json.dumps(error_result))
        sys.stdout.flush()
        sys.exit(1)
    
    # Run the main function
    result = asyncio.run(main(sys.argv[1]))
    
    # Print result and flush output to ensure it's immediately available
    print(json.dumps(result))
    sys.stdout.flush()
    
    # Exit with appropriate code
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)