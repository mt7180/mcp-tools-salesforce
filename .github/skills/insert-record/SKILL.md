---
name: insert-record
description: >-
  Insert a nested record hierarchy into a Salesforce scratch org
  via the Composite Tree REST API.
  Accepts a JSON payload file and root sObject. Returns structured JSON with insert results.
  USE FOR: insert records, composite tree API, upload test data, create Salesforce records, nested hierarchy.
argument-hint: <root_sObject> <payload_file>
---

# Insert Nested Record Hierarchy

Inserts a nested payload into a Salesforce scratch org via the Composite Tree REST API. Takes a JSON file following the Composite Tree format and a root sObject name.

## Invocation

```bash
uv run .github/skills/insert-record/insert_record.py <root_sObject> <payload_file> 
```

## Arguments

| Argument | Required | Description |
|---|---|---|
| `root_sObject` | Yes | API name of the root sObject (e.g. `Account`). Case-sensitive. |
| `payload_file` | Yes | Path to JSON file following Composite Tree format. |

## Output

Structured JSON printed to stdout:

```json
{
  "status": "success",
  "data": {
    "hasErrors": false,
    "results": [
      { "referenceId": "ref1", "id": "001..." },
      { "referenceId": "ref2", "id": "003..." }
    ]
  }
}
```

On failure:

```json
{
  "status": "error",
  "error": "error message"
}
```

## Payload Format

The JSON payload must follow the Composite Tree format:

- Every record needs `attributes.type` (sObject API name) and unique `attributes.referenceId`
- Nest child records under their relationship name (e.g. `Contacts`, `Cases`) as `{ "records": [...] }`
- Max 200 records, 5 nesting levels

## Prerequisites

- `uv` installed
- Valid `.env` with `CLIENT_ID`, `USERNAME`, `PRIVATE_KEY_FILE` (JWT Bearer Flow) in project root directory
- `server.key` accessible from the `.env` file's directory

## Errors

| Error | Likely Cause | Fix |
|---|---|---|
| `REQUIRED_FIELD_MISSING` | Non-nillable field omitted | Add field with valid value |
| `INVALID_FIELD` | Field not creatable or misspelled | Verify with `describe-sobject` skill |
| `INVALID_TYPE` | Wrong sObject name | sObject names are case-sensitive |
| `DUPLICATE_VALUE` | `referenceId` reused | Ensure all `referenceId` values are unique |
| `JWT auth failure` | Invalid credentials | Ask user to update `.env` |
