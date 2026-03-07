from typing import Any
from fastmcp import Client, FastMCP, Context
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from pydantic import BaseModel
from simple_salesforce import Salesforce
from rich.console import Console

import os
from dotenv import load_dotenv

console = Console()
dotenv_loaded = load_dotenv()

SAMPLING_MODEL = "gpt-4o-mini"
CLIENT_ID = os.getenv('CLIENT_ID')
USERNAME = os.getenv('USERNAME')
PRIVATE_KEY_FILE = os.getenv('PRIVATE_KEY_FILE')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

if PRIVATE_KEY_FILE:
    with open(PRIVATE_KEY_FILE, 'r') as f:
        PRIVATE_KEY = f.read()

mcp = FastMCP("Custom Salesforce MCP Server",
    sampling_handler=OpenAISamplingHandler(default_model=SAMPLING_MODEL),
    sampling_handler_behavior="fallback")

def get_sf_client( 
        client_id=CLIENT_ID, 
        username=USERNAME, 
        private_key=PRIVATE_KEY,
) -> Salesforce:  

    return Salesforce(
        username=username, 
        consumer_key=client_id, 
        privatekey=private_key
    )


@mcp.tool()
async def query_salesforce(soql_query: str) -> list[dict]:
    """Run a SOQL query against the Salesforce org and return results."""
    sf = get_sf_client()
    result = sf.query(soql_query)
    records = result.get("records", [])
    return records


def extract_creatable_fields(object_description: dict) -> dict:
    if not object_description:
        return {}
    
    return {
        field['name']: {key :field[key] for key in ['type', 'nillable']} 
        for field in object_description['fields'] 
        if field['createable']
    }


@mcp.tool(
    description=(
        "Get the basic data model of the scratch org."
        "This which includes the sObjects Account, Contact, "
        "Case and User with their respective creatable fields."
    )
)
async def get_basic_datamodel() -> dict:
    console.print(f"    [bold cyan]SERVER[/] Describe basic data model...")
    sf = get_sf_client()

    basic_sobject_types = ['Account', 'Contact', 'Case', 'User']
    data_model = {}

    for sobject in basic_sobject_types:
        object_description = sf.__getattr__(sobject).describe()
        if object_description['createable']:
            data_model[sobject] = extract_creatable_fields(object_description)
    return data_model

    
@mcp.tool()
async def describe_sobject(sobject_name: str) -> dict:
    """returns the fields of a specific sObject in the salesforce scratch org"""
    console.print(f"    [bold cyan]SERVER[/] Describe {sobject_name}...")
    sf = get_sf_client()

    object_description = sf.__getattr__(sobject_name).describe()
    if not object_description['createable']:
        return {}
    return extract_creatable_fields(object_description)

class ResultType(BaseModel):
    record: dict[str, Any]
    
@mcp.tool(
    description=(
        "Generate a nested record according to the user specification. "
        "The generated record must be compatible with the Salesforce Composite Tree API. "
        "Includes the describe_sobject tool to look up sObject schemas and their fields when needed."
    )
)
async def generate_nested_record(user_specification: str, ctx: Context) -> ResultType:
    console.print("    [bold cyan]SERVER[/] Starting to generate record...")

    prompt = (
        "Create a nested record, that is compatible with the Salesforce Composite Tree API "
        "and conforms to the provided user_specification.\n\n"
        f"user_specification:\n\n {user_specification}"
    )

    draft_record = await ctx.sample(
        messages=prompt,
        system_prompt="You are a Salesforce expert.",
        tools=[describe_sobject, tree_api_record_example],
        result_type=str,
        temperature=0.7,
        max_tokens=500
    )

    record = await ctx.sample(
        messages=f'Normalize this into valid JSON under key "record":\n\n{draft_record.text}',
        system_prompt="Return strictly valid JSON only.",
        result_type=ResultType,
    )

    console.print(f"    [bold cyan]SERVER[/] {str(record.result)}")
    return record.result



@mcp.tool()
async def insert_record(root_sobject: str, record: dict) -> dict:
    """ insert a record or nested record into the salesforce scratch org.
        The root_sobject parameter specifies the sObject type of the top-level record in the provided record, 
        which is required for the Salesforce Composite Tree API endpoint.
    """
    endpoint = f"composite/tree/{root_sobject}/"
    sf = get_sf_client()
   
    response = sf.restful(
        endpoint,
        method='POST',
        json=record
    )
    return response

def tree_api_record_example() -> str:
    """example of a nested record that is compatible with the Salesforce Composite Tree API """
    return """{
        "records" :[{
            "attributes" : {"type" : "Account", "referenceId" : "ref1"},
            "name" : "SampleAccount",
            "phone" : "1234567890",
            "website" : "www.salesforce.com",
            "numberOfEmployees" : "100",
            "industry" : "Banking",
            "Contacts" : {
            "records" : [{
                "attributes" : {"type" : "Contact", "referenceId" : "ref2"},
                "lastname" : "Smith",
                "title" : "President",
                "email" : "sample@salesforce.com"
                },{         
                "attributes" : {"type" : "Contact", "referenceId" : "ref3"},
                "lastname" : "Evans",
                "title" : "Vice President",
                "email" : "sample@salesforce.com"
                }]
            }
            },{
            "attributes" : {"type" : "Account", "referenceId" : "ref4"},
            "name" : "SampleAccount2",
            "phone" : "1234567890",
            "website" : "www.salesforce2.com",
            "numberOfEmployees" : "100",
            "industry" : "Banking"
            }]
        }"""

async def main():
   
    handler = OpenAISamplingHandler(default_model=SAMPLING_MODEL)

    async with Client(mcp, sampling_handler=handler) as client:
        tool_to_call = "generate_nested_record"
        
        match tool_to_call:
            case "generate_nested_record":
                user_specification = "create a salesforce nested record for a case where an old lady has trouble with her wlan router."
                result = await client.call_tool("generate_nested_record", {"user_specification": user_specification})
                console.print("LLM Response:", result.structured_content)
            case "query_salesforce":
                result = await client.call_tool("query_salesforce", {"soql_query": "SELECT Id, Name FROM Account"})
                console.print("LLM Response:", result.structured_content)
            case "get_basic_datamodel":
                result = await client.call_tool("get_basic_datamodel", {})
                console.print("LLM Response:", result.structured_content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())