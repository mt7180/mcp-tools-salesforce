## Why SKILL.md Instead of MCP

Converted this MCP tool into a SKILL.md agent skill for portability — no server, just a self-contained markdown file with executable scripts.

**Advantages**
- No MCP server to run locally or deploy — just copy the file into your project and you're done
- Fully version-controlled alongside the codebase
- Easy to share and drop into any agent setup

**Disadvantages**
- **Higher token usage**: the SKILL.md content is loaded into context on each call, whereas MCP only exposes a lightweight tool signature
- **More hacky**: requires setting up and maintaining a venv — without one, skill dependencies bleed into the system Python, risking version conflicts and broken environments across projects
- **Doesn't scale well** — each new capability means another file to manage; MCP consolidates everything behind one server
- **No streaming or async responses** — scripts are run-and-done
- **Security risk**: the agent executes shell/Python directly on the host machine with no sandboxing layer
- **Agent-dependent**: the skill relies on the LLM correctly interpreting markdown instructions rather than a strict tool schema — behavior may vary across agents or model versions