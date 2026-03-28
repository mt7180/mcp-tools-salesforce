## Why Skills + Prompts Instead of MCP

Converted this MCP tool into composable Copilot **skills** and an orchestrating **prompt** — no server, just self-contained markdown + Python scripts with `uv`.

### Structure

```
.github/
├── prompts/
│   └── upload-nested-data.prompt.md   ← orchestration workflow
└── skills/
	├── describe-sobject/              ← atomic skill: introspect sObject fields
	│   ├── SKILL.md
	│   └── describe_sobject.py
	├── insert-record/                 ← atomic skill: insert nested records
	│   ├── SKILL.md
	│   └── insert_record.py
	└── upload-nested-data/
		└── .env                       ← Salesforce JWT credentials
```

- **Prompt** orchestrates multi-step workflows, referencing skills
- **Skills** are atomic, reusable tasks with clear inputs/outputs
- **Python scripts** use [PEP 723](https://peps.python.org/pep-0723/) inline dependencies and run via `uv run` — no venv, no setup script

### Advantages
- No MCP server to run locally or deploy — just copy the folders and go
- Fully version-controlled alongside the codebase
- `uv run` + PEP 723 inline deps = no venv management, no requirements.txt
- Skills are independently reusable; the prompt composes them

### Disadvantages
- **Token usage is context-dependent**: skill metadata (~100 tokens) loads at startup, full SKILL.md on trigger
- **Hard dependency on `uv`**: scripts require [`uv`](https://docs.astral.sh/uv/) to be installed
- **Security risk**: the agent executes Python directly on the host with no sandboxing
- **Agent-dependent**: relies on the LLM interpreting markdown instructions rather than a strict tool schema

## Getting Started

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed

### Salesforce Auth (JWT Bearer Flow)

1. Follow these [steps](https://medium.com/@mira.theidel/how-to-connect-your-custom-mcp-server-to-salesforce-scratch-orgs-and-let-ai-generate-your-test-270ec91b41be#bd06) to set up the connection to your Salesforce org
2. Add a `.env` file at `.github/skills/upload-nested-data/.env`:

```
CLIENT_ID = 'xxx'
USERNAME = 'xxx'
PRIVATE_KEY_FILE = 'server.key'
```

3. Place your `server.key` in the same directory as `.env`

**OR**: Less secure, but you could also get the access token from `sf` CLI and inject it as input for the scripts.

---

> Interesting discussion by **Pamela Fox**:
>
> **"Can VS Code skills be a replacement for MCP servers?"**
> - https://github.com/orgs/microsoft-foundry/discussions/280#discussioncomment-16338085
> - https://youtu.be/Uufh7cPUnmQ?si=GuBGanruQCn0gDYT&t=885
