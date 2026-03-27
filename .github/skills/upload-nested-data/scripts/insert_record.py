import json
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


def run(root_sobject: str, payload: dict) -> dict:
    settings = Settings()
    try:
        sf = get_sf_client(settings)

        endpoint = f"composite/tree/{root_sobject}/"
        response = sf.restful(endpoint, method="POST", json=payload)

        return {
            "status": "error" if response.get("hasErrors") else "success",
            "data": response,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


# optional CLI für lokale Tests
if __name__ == "__main__":
    import sys

    root = sys.argv[1]
    with open(sys.argv[2]) as f:
        payload = json.load(f)

    result = run(root, payload)
    print(json.dumps(result))
    result