from typing import Any, DefaultDict
from fastmcp import FastMCP, Context
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from simple_salesforce import Salesforce
from dataclasses import dataclass

import jwt

import os
import time
import requests
from dotenv import load_dotenv


dotenv_loaded = load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
USERNAME = os.getenv('USERNAME')

mcp = FastMCP("Custom Salesforce MCP Server",
    sampling_handler=OpenAISamplingHandler(default_model="gpt-4o-mini"),
    sampling_handler_behavior="always")

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

def extract_relevant_fields(object_description: dict) -> dict:
    if not object_description:
        return {}
    
    return {
        field['name']: {key :field[key] for key in ['type', 'nillable']} 
        for field in object_description['fields'] 
        if field['createable']
    }


@mcp.tool()
async def get_basic_datamodel() -> dict:
    """returns the basic data model of my scratch org as dictionary 
    of the most relevant sObject Types (like Account, Contact, Case and User) with their fields
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
    sf = get_sf_client()

    object_description = sf.__getattr__(sobject_name).describe()

    if not object_description['createable']:
        return {}
    return extract_relevant_fields(object_description)

@dataclass
class ResultType:
    record: dict
    
@mcp.tool()
async def generate_nested_record(request: str, ctx: Context) -> dict:
    """generates a Salesforce nested record according to the request"""
    
    prompt = f"""Generate a nested record as a JSON object, which is compatible 
        with Salesforce Composite Tree API and conforms to the provided request: 
        {request}

        Example nested record: 
        {example_nested_record()}
    """

    record = await ctx.sample(
        prompt,
        result_type=ResultType,  
        tools=[describe_sobject, example_nested_record],
        temperature=0.7,
        max_tokens=300
    )
    # await ctx.info(f"generated record: {record.text}")

    return record.result

@mcp.tool()
async def insert_record(root_sobject: str, record: dict) -> dict:
    """inserts a record or nested records into the salesforce scratch org according to the provided record.
    """
    endpoint = f"composite/tree/{root_sobject}/"
    sf = get_sf_client()
   
    response = sf.restful(
        endpoint,
        method='POST',
        json=record
    )
    return response

@mcp.tool()
def example_nested_record() -> str:
    """example of a nested record structure that is compatible with the Salesforce Composite Tree API """
    return {
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
        }

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
    