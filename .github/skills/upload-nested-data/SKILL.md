# Skill: Upload Nested Record to Salesforce Scratch Org

Insert a nested Salesforce record hierarchy into a scratch org via the **Composite Tree REST API**. All scripts authenticate autonomously via JWT Bearer Flow — the agent never handles or passes access tokens or key files.

## When to use

Use this skill when asked to:
- Create nested test data in a Salesforce scratch org (e.g. Account with Contacts and Cases)
- Insert a record hierarchy via the Composite Tree API endpoint
- Generate and upload sObject payloads that match the actual data model of the connected org
- Set up related parent-child records in a single API call (up to 200 records, 5 nesting levels)
- Populate demo environments with Account → Contact → Case type scenarios

## Scripts

All scripts live at `.github/skills/upload-nested-data/scripts/` relative to the project root.

| File | Purpose |
|---|---|
| `scripts/describe_sobject.py` | Prints creatable fields for a given sObject |
| `scripts/insert_record.py` | POSTs a JSON payload to the Composite Tree API |
| `scripts/example_payload.json` | Example payload (Account → Contact → Case) |

**Run all commands from the project root** so that `pydantic-settings` picks up the `.env` file there.

---

## Important notes

**NEVER** read, modify, or display the contents of `.env` or `server.key` files. The Python scripts handle authentication automatically.

**ALWAYS** when executig pip or python commands, make sure to pre-fix to activate the virtual environment in the same command Examples:
- `source .venv/bin/activate && pip install ...`
- `source .venv/bin/activate && python ...`

**Workflow**: Execute all steps sequentially in the same terminal session (use `isBackground: false` for all commands) to maintain the active virtual environment throughout.

---

## Workflow
### Step 1 – Set up the virtual environment and install dependencies

Execute the following commands:

```bash
# Create virtual environment if not already present
python3 -m venv .venv 

# Activate virtual environment and install required packages
source .venv/bin/activate && pip install -r .github/skills/upload-nested-data/scripts/requirements.txt
```


---

### Step 2 – Introspect the data model

Describe each sObject that will appear in the hierarchy to learn which fields are creatable, their types, and whether they are nillable.

```bash
source .venv/bin/activate && python .github/skills/upload-nested-data/scripts/describe_sobject.py Account
source .venv/bin/activate && python .github/skills/upload-nested-data/scripts/describe_sobject.py Contact
source .venv/bin/activate && python .github/skills/upload-nested-data/scripts/describe_sobject.py Case
```

Analyze the JSON output to understand which fields are available and required before building your payload.

---

### Step 3 – Build the payload

Create a JSON file named `payload_<datetime>.json` (e.g. `payload_20260327_143022.json`) with the current date and time in `YYYYMMDD_HHMMSS` format.

The file must follow the Composite Tree API format:

Key rules:
- Every record needs `attributes.type` (sObject API name) and a unique `attributes.referenceId`
- Child records are nested under the relationship name (e.g. `Contacts`, `Cases`) as `{ "records": [...] }`
- Only include fields confirmed as creatable in Step 2
- Maximum 200 records and 5 nesting levels per request

Example (`scripts/example_payload.json`):

```json
{
  "records": [
    {
      "attributes": { "type": "Account", "referenceId": "ref1" },
      "Name": "Mustermann GmbH",
      "Industry": "Technology",
      "Contacts": {
        "records": [
          {
            "attributes": { "type": "Contact", "referenceId": "ref2" },
            "LastName": "Mustermann",
            "FirstName": "Erika",
            "Email": "erika@mustermann.de",
            "Cases": {
              "records": [
                {
                  "attributes": { "type": "Case", "referenceId": "ref3" },
                  "Subject": "WLAN-Router funktioniert nicht",
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

### Step 4 – Insert the record

Pass the root sObject name and the timestamped payload file to the insert script.

**Run in the same terminal** (with venv still active):

```bash
source .venv/bin/activate && python .github/skills/upload-nested-data/scripts/insert_record.py Account <payload-json-file>
```

(Replace `<payload-json-file>` with the actual filename you created in Step 3.)

A successful response:

```json
{
  "hasErrors": false,
  "results": [
    { "referenceId": "ref1", "id": "001..." },
    { "referenceId": "ref2", "id": "003..." }
  ]
}
```

The script exits with a non-zero code if `hasErrors` is `true`.

---

## Error reference

| Salesforce error | Likely cause | Fix |
|---|---|---|
| `REQUIRED_FIELD_MISSING` | Non-nillable field omitted | Add the field (check Step 2 output) |
| `INVALID_FIELD` | Field not createable or misspelled | Verify against `describe_sobject.py` output |
| `INVALID_TYPE` | Wrong sObject name in `attributes.type` | sObject names are case-sensitive |
| `DUPLICATE_VALUE` | `referenceId` used more than once | Ensure all `referenceId` values are unique |
| `JWT auth failure` | `.env` credentials wrong or key mismatch | Ask User to update the `.env` file with correct credentials, never access the `.env` or `server.key` file directly |
