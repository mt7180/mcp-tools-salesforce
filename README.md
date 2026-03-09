

# Salesforce MCP Server
### Connect Your Custom MCP Server to Salesforce Scratch Orgs — and Let AI Generate Your Test Data

Creating meaningful Salesforce test data sounds simple — until you are the one filling in realistic field values, required fields and nested records that actually make sense. It’s not difficult. It’s just the kind of annoying, time-consuming work that’s perfect to hand off.
In this write-up I document how I built a custom MCP server that connects to a Salesforce scratch org and uses MCP Sampling to let the LLM autonomously generate and insert nested test records. You describe the scenario in plain English. The server does the rest.

>TL;DR: FastMCP + simple-salesforce + Sampling with tools and structured output = a little server that turns natural language into Salesforce test data, ingested via Composite Tree REST API.


📝 Read the full write-up on [Medium](https://medium.com/@mira.theidel/how-to-connect-your-custom-mcp-server-to-salesforce-scratch-orgs-and-let-ai-generate-your-test-270ec91b41be?postPublishedType=repub)

![notes](notes.excalidraw.png)

A custom MCP server that connects to a Salesforce org using JWT Bearer OAuth and exposes tools to inspect metadata and autonomously generate/insert records (including Composite Tree API upload).

What it provides
- describe_sobject(sobject_name): returns createable fields for an sObject (name, type, nillable).
- get_basic_datamodel(): returns a lightweight field map for Account, Contact, Case, User.
- generate_nested_record(request): uses LLM sampling to draft a Composite Tree compatible nested record JSON for a natural-language request.
- insert_record(root_sobject, record): posts the payload to POST /services/data/vXX.X/composite/tree/{root_sobject}.  
s
  
>Note:
>- generate_nested_record uses MCP sampling and structured output to generate the record
>- the MCP Server is registered as external client app and authenticates via JWT Bearer Flow to the Salesforce scratch org. 


## Resources
- https://help.salesforce.com/s/articleView?id=xcloud.jwt_connectedapp_enable.htm&type=5
- https://generect.com/blog/salesforce-mcp-integration/
https://www.jlowin.dev/blog/the-inverted-agent
- https://generect.com/blog/salesforce-mcp-integration/