

# mcp-tools-salesforce
### Custom MCP Server that Connects to Salesforce Scratch Orgs — and Lets AI Generate Test Data

>📝 Read the full write-up on [Medium](https://medium.com/@mira.theidel/how-to-connect-your-custom-mcp-server-to-salesforce-scratch-orgs-and-let-ai-generate-your-test-270ec91b41be?postPublishedType=repub).   
>TL;DR: FastMCP + simple-salesforce + Sampling with tools and structured output = a little server that turns natural language into Salesforce test data, ingested via Composite Tree REST API.

This project is a custom MCP server built with FastMCP that connects to a Salesforce scratch org via JWT Bearer Flow. It exposes tools for querying and inserting records — and uses MCP Sampling to let an LLM autonomously look up the data model, generate realistic nested test records, and insert them via the Salesforce Composite Tree API. You describe the scenario in plain English. The server does the rest.

![notes](notes.excalidraw.png)



What it provides
- describe_sobject(sobject_name): returns createable fields for an sObject (name, type, nillable).
- get_basic_datamodel(): returns a lightweight field map for Account, Contact, Case, User.
- generate_nested_record(request): uses LLM sampling to draft a Composite Tree compatible nested record JSON for a natural-language request.
- insert_record(root_sobject, record): posts the payload to POST /services/data/vXX.X/composite/tree/{root_sobject}.  
s
  
>Key Facts:
>- generate_nested_record uses MCP sampling and structured output to generate the record
>- the MCP Server is registered as external client app and authenticates via JWT Bearer Flow to the Salesforce scratch org. 


## Resources
- https://help.salesforce.com/s/articleView?id=xcloud.jwt_connectedapp_enable.htm&type=5
- https://generect.com/blog/salesforce-mcp-integration/
- https://www.jlowin.dev/blog/the-inverted-agent