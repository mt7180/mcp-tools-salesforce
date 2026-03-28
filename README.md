## Why SKILL.md Instead of MCP

Converted this MCP tool into a SKILL.md agent skill for portability — no server, just a self-contained markdown file with executable scripts.

**Advantages**
- No MCP server to run locally or deploy — just copy the folder into your project and you're done
- Fully version-controlled alongside the codebase
- Easy to share and drop into any agent setup

**Disadvantages**
- **Token usage is context-dependent**: only skill metadata (~100 tokens) loads at startup, and the full SKILL.md only loads on trigger — but a large SKILL.md can cost more than a lean MCP tool definition
- More hacky & **dependency management requires discipline**: without `uv` and PEP 723 inline script metadata, the agent may install packages into system Python, polluting the host environment. With `uv run` and a `# /// script` block, this is largely solved — but it adds a hard dependency on `uv` being installed.
- **Security risk**: the agent executes shell/Python directly on the host machine with no sandboxing layer
- **Agent-dependent**: the skill relies on the LLM correctly interpreting markdown instructions rather than a strict tool schema — behavior may vary across agents or model versions

## Getting Started
For OAuth 2.0 JWT Bearer Flow:
- Follow this [steps](https://medium.com/@mira.theidel/how-to-connect-your-custom-mcp-server-to-salesforce-scratch-orgs-and-let-ai-generate-your-test-270ec91b41be#bd06) to set up the connection to your Salesforce org.
- Place your `server.key` and a custom `.env` file in the root project folder and add your credentials:  

```
CLIENT_ID = 'xxx'
CONSUMER_PW = 'xxx'
USERNAME = 'xxx'
PRIVATE_KEY_FILE = 'server.key'
```
**OR**: Less secure, but you could also consider getting the access token for your Salesforce Org from sf cli and let the agent inject it as input for the python scrips (in this case you won't need the sf_client and .env file anymore)

&nbsp;&nbsp;  

> &nbsp;  
> Interesting discussion by the awesome **Pamela Fox**:  
>
> __"Can VS Code skills be a replacement for MCP servers?"__: 
>- https://github.com/orgs/microsoft-foundry/discussions/280#discussioncomment-16338085
>- https://youtu.be/Uufh7cPUnmQ?si=GuBGanruQCn0gDYT&t=885  
