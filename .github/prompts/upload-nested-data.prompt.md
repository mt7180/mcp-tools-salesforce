---
agent: 'agent'
description: >-
  Insert a nested Salesforce record hierarchy into a scratch org.
  Orchestrates: introspecting the data model, building the payload, and inserting records via the Composite Tree REST API.
---

# Upload Nested Record to Salesforce Scratch Org

Inserts a nested record hierarchy into a scratch org via the **Composite Tree REST API**. Authentication is handled automatically via JWT Bearer Flow.

## When to Use

Use this prompt when you need to:

- Insert **parent-child record hierarchies** in a single API call (e.g. Account → Contact → Case)
- Create **nested test data** for a Salesforce scratch org
- **Populate demo or sandbox environments** with realistic, related records

Do **not** use when:
- The hierarchy exceeds 200 records or 5 nesting levels (Composite Tree API limit)
- You need to update or upsert existing records (this workflow is insert-only)

## Security

- **NEVER** read, display, or modify `.env` or `server.key` — scripts handle auth autonomously
- Always parse the structured JSON response instead of relying on raw stdout

## Pipeline

Follow these steps **in order**. Do not build a payload before confirming field accessibility.

### Step 1 — Introspect the data model

Use the `describe-sobject` tool to inspect the fields of any needed sObject.

Parse the JSON response. Confirm `"status": "success"` before proceeding. If `"status": "error"`, stop and report to the user.

Only use fields from `data` where `nillable` and `type` match your intended payload. Field names and types from this step determine what goes into the payload.

### Step 2 — Build the payload

Create `payload_<YYYYMMDD_HHMMSS>.json` following the Composite Tree format. Always create a **new** timestamped payload file — never reuse old ones.

Rules:
- Every record needs `attributes.type` (sObject API name) and a unique `attributes.referenceId`
- Nest child records under their relationship name (e.g. `Contacts`, `Cases`) as `{ "records": [...] }`
- Max 200 records, 5 nesting levels
- Only include fields confirmed as creatable in Step 1
- For non-nillable fields, always provide a value

Example:
```json
{
  "records": [
    {
      "attributes": { "type": "Account", "referenceId": "ref1" },
      "Name": "Mustermann GmbH",
      "Contacts": {
        "records": [
          {
            "attributes": { "type": "Contact", "referenceId": "ref2" },
            "LastName": "Mustermann",
            "Cases": {
              "records": [
                {
                  "attributes": { "type": "Case", "referenceId": "ref3" },
                  "Subject": "Issue",
                  "Status": "New",
                  "Origin": "Phone"
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

### Step 3 — Insert

Use the `insert-record` tool to insert the payload into the scratch org.

Parse the JSON response. Confirm `"status": "success"` **and** `"hasErrors": false` before proceeding. If status is `"error"` or `hasErrors` is `true`, consult the error reference below and report to the user.

### Step 4 — Verify and report

Confirm results to the user. Summarize the created records with their IDs and reference IDs.

## Error Reference

| Error | Likely Cause | Fix |
|---|---|---|
| `REQUIRED_FIELD_MISSING` | Non-nillable field omitted | Add field (check Step 1 output) |
| `INVALID_FIELD` | Field not creatable or misspelled | Verify against Step 1 output |
| `INVALID_TYPE` | Wrong sObject name | sObject names are case-sensitive |
| `DUPLICATE_VALUE` | `referenceId` reused | Ensure all `referenceId` values are unique |
| `JWT auth failure` | Invalid credentials | Ask user to update `.env` — never access it directly |
