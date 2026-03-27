import argparse
import json
import sys

from sf_client import get_sf_client


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
        return {"status": "success", "data": describe_creatable_fields(sobject)}
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
   