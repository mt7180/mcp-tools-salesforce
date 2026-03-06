

# Salesforce MCP Server
### (mcp-tools-salesforce)

implements a Model Context Protocol (MCP) server that connects to a Salesforce org using JWT Bearer OAuth and exposes tools to inspect metadata and create/insert records (including Composite Tree API nested payloads).

![notes](notes.excalidraw.png)

What it provides
- describe_sobject(sobject_name): returns createable fields for an sObject (name, type, nillable).
- get_basic_datamodel(): returns a lightweight field map for Account, Contact, Case, User.
- generate_nested_record(request): uses LLM sampling to draft a Composite Tree compatible nested record JSON for a natural-language request.
- insert_record(root_sobject, record): posts the payload to POST /services/data/vXX.X/composite/tree/{root_sobject}.

  
  
>Note:
>- generate_nested_record uses MCP sampling and structured output to generate the record
>- the MCP Server is registered as external client app and authenticates via JWT Bearer Flow to the Salesforce scratch org. 


## Resources
- https://github.com/salesforcecli/mcp
- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_mcp_use_core_tools.htm
- https://generect.com/blog/salesforce-mcp-integration/