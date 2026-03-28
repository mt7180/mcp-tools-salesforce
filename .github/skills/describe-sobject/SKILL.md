---
name: describe-sobject
description: >-
  Describe creatable fields for a Salesforce sObject.
  Returns structured JSON with field names, types, and nillability.
  USE FOR: describe sObject, list creatable fields, introspect Salesforce data model, field metadata.
argument-hint: <sObject>
---

# Describe sObject Fields

Returns all creatable fields for a given Salesforce sObject as structured JSON. Used to validate field names and types before building a Composite Tree payload.

## Security

- **NEVER** read, display, or modify `.env` or `server.key` — scripts handle auth autonomously
- Always parse the structured JSON response instead of relying on raw stdout

## Invocation

```bash
uv run .github/skills/describe-sobject/describe_sobject.py <sObject>
```

## Arguments

| Argument | Required | Description |
|---|---|---|
| `sObject` | Yes | API name of the sObject (e.g. `Account`, `Contact`, `Case`). Case-sensitive. |


## Output

Structured JSON printed to stdout:

```json
{
  "status": "success",
  "data": {
    "FieldName": {
      "type": "string",
      "nillable": false
    }
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

## Prerequisites

- `uv` installed
- Valid `.env` with `CLIENT_ID`, `USERNAME`, `PRIVATE_KEY_FILE` (JWT Bearer Flow) in project root directory
- `server.key` accessible from the `.env` file's directory
