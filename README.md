# mcp-tools-salesforce
### Custom MCP Server that Connects to Salesforce Scratch Orgs — and Lets AI Generate Test Data

> 📝 [Read the full write-up on Medium](https://medium.com/@mira.theidel/how-to-connect-your-custom-mcp-server-to-salesforce-scratch-orgs-and-let-ai-generate-your-test-270ec91b41be)

A custom MCP server built with FastMCP that connects to a Salesforce scratch org via JWT Bearer Flow. It uses MCP Sampling to let an LLM autonomously look up the data model, generate realistic nested test records, and insert them via the Composite Tree REST API. You describe the scenario in plain English. The server does the rest.

![notes](notes.excalidraw.png)

### Tools

| Tool | Description |
|---|---|
| `query_salesforce(soql_query)` | Runs a SOQL query against the connected scratch org and returns matching records|
| `describe_sobject(sobject_name)` | Returns createable fields for an sObject (name, type, nillable) |
| `get_basic_datamodel()` | Returns a lightweight field map for Account, Contact, Case, User |
| `generate_nested_record(request)` | Uses LLM sampling to draft a Composite Tree compatible nested record from a natural-language request |
| `insert_record(root_sobject, record)` | Posts the payload to `composite/tree/{root_sobject}` |

&nbsp;&nbsp;

> **Note:** `generate_nested_record` uses MCP Sampling with tools + structured output. Authentication via JWT Bearer Flow.

### Getting Started
- Follow the [steps](https://medium.com/@mira.theidel/how-to-connect-your-custom-mcp-server-to-salesforce-scratch-orgs-and-let-ai-generate-your-test-270ec91b41be#bd06) to set up the connection to your Salesforce org.
- Add a custom `.env` file into the root project folder and add your credentials:  

```
CLIENT_ID = 'xxx'
CONSUMER_PW = 'xxx'
USERNAME = 'xxx'
PRIVATE_KEY_FILE = 'server.key'
OPENAI_API_KEY = 'xxx'
```

## Resources
- https://help.salesforce.com/s/articleView?id=xcloud.jwt_connectedapp_enable.htm&type=5
- https://generect.com/blog/salesforce-mcp-integration/
- https://www.jlowin.dev/blog/the-inverted-agent