import argparse
import json
from pathlib import Path
import sys

from sf_client import get_sf_client


def insert_tree(root_sobject: str, payload: dict) -> dict:
    try:
        sf = get_sf_client()
        response = sf.restful(f"composite/tree/{root_sobject}/", method="POST", json=payload)
        return {
            "status": "error" if response.get("hasErrors") else "success",
            "data": response,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Insert a nested payload via Composite Tree API.")
    parser.add_argument("root_sobject", help="API name of the root sObject (e.g., Account)")
    parser.add_argument("payload", type=Path, help="Path to the JSON payload file")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    with args.payload.open() as handle:
        payload = json.load(handle)

    result = insert_tree(args.root_sobject, payload)
    print(json.dumps(result))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
 