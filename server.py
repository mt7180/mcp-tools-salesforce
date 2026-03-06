
from typing import Any, DefaultDict
from fastmcp import Client, FastMCP, Context
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from pydantic import BaseModel
from simple_salesforce import Salesforce
from rich.console import Console

import jwt

import os
import time
import requests
from dotenv import load_dotenv

console = Console()
dotenv_loaded = load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
USERNAME = os.getenv('USERNAME')

mcp = FastMCP("Custom Salesforce MCP Server",
    sampling_handler=OpenAISamplingHandler(default_model="gpt-4o-mini"),
    sampling_handler_behavior="fallback")

if dotenv_loaded:
    with open(os.getenv('PRIVATE_KEY_FILE'), 'r') as f:
        PRIVATE_KEY = f.read()
else:
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')

assert PRIVATE_KEY is not None, "Private key must be provided either in .env file or as an environment variable."

class TokenError(Exception):
    pass

def get_sf_client(
        client_id=CLIENT_ID, 
        username=USERNAME, 
        private_key=PRIVATE_KEY, 
        domain='login'
    ) -> Salesforce:

    url = f'https://{domain}.salesforce.com/services/oauth2/token'

    claim = {
        'iss': client_id,
        'sub': username,
        'aud': f'https://{domain}.salesforce.com',
        'exp': int(time.time()) + 300
    }
    
    assertion = jwt.encode(claim, private_key, algorithm='RS256')
    payload = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': assertion
    }
    
    response = requests.post(url, data=payload)
    
    try:
        response_json = response.json()
    except ValueError:
        raise TokenError(f"Token endpoint returned non-JSON (status={response.status_code})")

    if response.status_code != 200 or 'error' in response_json:
        err = response_json.get('error_description') or response_json.get('error') or response_json
        raise TokenError(f"Failed to obtain token: {err}")

    if not 'access_token' in response_json:
        raise TokenError(f"No access_token in response: {response_json}")
    
    sf = Salesforce(
        instance_url = response_json['instance_url'], 
        session_id = response_json['access_token']
    )

    return sf

async def extract_relevant_fields(object_description: dict) -> dict:
    if not object_description:
        return {}
    
    return {
        field['name']: {key :field[key] for key in ['type', 'nillable']} 
        for field in object_description['fields'] 
        if field['createable']
    }


@mcp.tool()
async def get_basic_datamodel() -> dict:
    """returns the basic data model of the scratch org as dictionary 
    of the most relevant sObject Types (Account, Contact, Case and User) with their fields.
    """

    sf = get_sf_client()

    basic_sobject_types = [
        'Account', 'Contact', 'Case', 'User'
    ]

    data_model = {}

    for sobject in basic_sobject_types:
        object_description = sf.__getattr__(sobject).describe()
        if object_description['createable']:
            data_model[sobject] = extract_relevant_fields(object_description)
    return data_model

    
@mcp.tool()
async def describe_sobject(sobject_name: str) -> dict:
    """returns the fields of a specific sObject in the salesforce scratch org"""
    console.print(f"    [bold cyan]SERVER[/] Describe {sobject_name}...")
    sf = get_sf_client()

    object_description = sf.__getattr__(sobject_name).describe()

    if not object_description['createable']:
        return {}
    return await extract_relevant_fields(object_description)

class ResultType(BaseModel):
    record: dict[str, Any]
    
@mcp.tool()
async def generate_nested_record(request: str, ctx: Context) -> ResultType:
    """generates a Salesforce nested record according to the request"""
    
    console.print("    [bold cyan]SERVER[/] Starting to generate record...")
    example_record = example_nested_record()
    prompt = f"""Create a nested record, that is compatible 
        with the Salesforce Composite Tree API and conforms to the provided request.
        
        request:\n\n {request}

        Example nested record: \n\n 
        {example_record}
    """

    draft_record = await ctx.sample(
        messages=prompt,
        system_prompt="You are a Salesforce expert. You are a Salesforce expert. Use describe_sobject when needed.",
        tools=[describe_sobject],
        result_type=str,
        temperature=0.7,
        max_tokens=500
    )

    record = await ctx.sample(
        messages=f'Normalize this into valid JSON under key "record":\n\n{draft_record.text}',
        system_prompt="Return strictly valid JSON only.",
        result_type=ResultType,
    )

    # await ctx.info(f"generated record: {record.text}")
    console.print(f"    [bold cyan]SERVER[/] {str(record.result)}")
    return record.result



@mcp.tool()
async def insert_record(root_sobject: str, record: dict) -> dict:
    """inserts a record or nested records into the salesforce scratch org according to the provided record.
        The root_sobject parameter specifies the sObject type of the top-level record in the provided record, which is required for the Salesforce Composite Tree API endpoint.
    """
    endpoint = f"composite/tree/{root_sobject}/"
    sf = get_sf_client()
   
    response = sf.restful(
        endpoint,
        method='POST',
        json=record
    )
    return response

def example_nested_record() -> str:
    """example of a nested record structure that is compatible with the Salesforce Composite Tree API """
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
   
    handler = OpenAISamplingHandler(default_model="gpt-5")

    async with Client(mcp, sampling_handler=handler) as client:
        request = "create a salesforce nested record for a case where an old lady has trouble with her wlan router. "
        result = await client.call_tool("generate_nested_record", {"request": request})
        console.print("LLM Response:", result)

        
       
      


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

    # https://gofastmcp.com/servers/tools