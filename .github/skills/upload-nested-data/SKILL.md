---
name: upload-nested-data
description: Insert a nested Salesforce record hierarchy into a scratch org via the Composite Tree REST API. Use when asked to create nested test data, insert parent-child record hierarchies (Account → Contact → Case), or populate demo environments in a Salesforce scratch org.
---

# Upload Nested Record to Salesforce Scratch Org

Inserts a nested record hierarchy into a scratch org via the **Composite Tree REST API**. Authentication is handled automatically via JWT Bearer Flow.

## When to Use

Use this skill when you need to:

- Insert **parent-child record hierarchies** in a single API call (e.g. Account → Contact → Case)
- Create **nested test data** for a Salesforce scratch org
- **Populate demo or sandbox environments** with realistic, related records


Do **not** use this skill when:
- The hierarchy exceeds 200 records or 5 nesting levels (Composite Tree API limit)
- You need to update or upsert existing records (this skill is insert-only)

---

## Important

- **NEVER** read, display, or modify `.env` or `server.key` — scripts handle auth autonomously
- Always use the skill's venv Python directly: `.github/skills/upload-nested-data/scripts/.venv/bin/python`
- Execute all steps **sequentially** — do not build a payload before confirming field accessibility
- Always create a **new** timestamped payload file, never reuse old ones
- Scripts return **structured JSON** (`status`, `data`, `error`) — always parse the response instead of relying on raw stdout

---

## Scripts

All scripts live at `.github/skills/upload-nested-data/scripts/`.

| File | Purpose |
|---|---|
| `setup.sh` | Creates venv and installs dependencies (idempotent) |
| `describe_sobject.py` | Returns creatable fields for a given sObject (structured JSON) |
| `insert_record.py` | Inserts a nested payload via Composite Tree API (structured JSON) |

---

## Workflow

### Step 1 — Setup
```bash
bash setup.sh
```

Idempotent — only installs dependencies when `requirements.txt` has changed.

After running setup.sh, confirm the output contains `"status": "success"` 
before proceeding. If status is "error", stop and report to the user.
---

### Step 2 — Introspect the data model (REQUIRED before Step 3)
Do not build the payload until you have analyzed this output — field names and types from Step 2 determine what goes into the payload.

Run for each sObject in the hierarchy and do not rely on stdout formatting — always parse the JSON response.

```bash
.venv/bin/python describe_sobject.py <sObject>
```

Output format
The script returns structured JSON:

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

Only use fields from data where nillable and type match your intended payload.

After running for all sObjects, confirm the output contains `"status": "success"` before proceeding. If status is "error", stop and report to the user.

---

### Step 3 — Build the payload

Create `payload_<YYYYMMDD_HHMMSS>.json` following the Composite Tree format:

- Every record needs `attributes.type` (sObject API name) and a unique `attributes.referenceId`
- Nest child records under their relationship name (e.g. `Contacts`, `Cases`) as `{ "records": [...] }`
- Max 200 records, 5 nesting levels
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

---

### Step 4 — Insert
```bash
.venv/bin/python insert_record.py <sObject> <payload-file>
```

Output format
The script returns structured JSON:

```json
{
  "status": "success",
  "data": {
    "hasErrors": false,
    "results": [...]
  }
}

after running, confirm the output contains `"status": "success"` and `"hasErrors": false` before proceeding. If status is "error" or hasErrors is true, stop and report to the user.

- "status": "success" → request succeeded
- "status": "error" → request failed (see data or error field)


---

## Error reference

| Error | Likely cause | Fix |
|---|---|---|
| `REQUIRED_FIELD_MISSING` | Non-nillable field omitted | Add field (check Step 2 output) |
| `INVALID_FIELD` | Field not creatable or misspelled | Verify against `describe_sobject.py` |
| `INVALID_TYPE` | Wrong sObject name | sObject names are case-sensitive |
| `DUPLICATE_VALUE` | `referenceId` reused | Ensure all `referenceId` values are unique |
| `JWT auth failure` | Invalid credentials | Ask user to update `.env` — never access it directly |