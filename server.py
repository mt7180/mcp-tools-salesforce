from typing import DefaultDict
from fastmcp import FastMCP
from simple_salesforce import Salesforce

import jwt

import os
import time
import requests
from dotenv import load_dotenv



mcp = FastMCP("Custom Salesforce MCP Server")

dotenv_loaded = load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
USERNAME = os.getenv('USERNAME')

if dotenv_loaded:
    with open(os.getenv('PRIVATE_KEY_FILE'), 'r') as f:
        PRIVATE_KEY = f.read()
else:
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')

assert PRIVATE_KEY is not None, "Private key must be provided either in .env file or as an environment variable."

class TokenError(Exception):
    pass

def _get_jwt_token(
        client_id=CLIENT_ID, 
        username=USERNAME, 
        private_key=PRIVATE_KEY, 
        domain='login'
    ) -> str:

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

    return response_json

def get_field_definitions(object_description: dict) -> dict:
    if not object_description:
        return {}
    
    return {
        field['name']: {key :field[key] for key in ['type', 'nillable']} 
        for field in object_description['fields'] 
        if field['createable']
    }


@mcp.tool()
def get_salesforce_basic_datamodel() -> dict:
    """returns the basic data model of my scratch org as dictionary 
    of the most relevant sObject Types with their fields
    """

    oAuth_info = _get_jwt_token()
    sf = Salesforce(
        instance_url = oAuth_info['instance_url'], 
        session_id = oAuth_info['access_token']
    )

    basic_sobject_types = [
        'Account', 'Asset', 'Contact', 'Contract', 'Lead', 'Opportunity', 'Order' 'Case', 
        'Task', 'User', 'Product2'
    ]

    # data_model = DefaultDict(dict)
    data_model = {}

    for sobject in basic_sobject_types:
        object_description = sf.__getattr__(sobject).describe()
        if object_description['createable']:
            data_model[sobject] = get_field_definitions(object_description)
    return data_model

    
@mcp.tool()
def get_sobject_fields(sobject_name: str) -> dict:
    """returns the fields of a specific sObject in the scratch org"""
    oAuth_info = _get_jwt_token()
    sf = Salesforce(
        instance_url = oAuth_info['instance_url'], 
        session_id = oAuth_info['access_token']
    )
    object_description = sf.__getattr__(sobject_name).describe()
    if not object_description['createable']:
        return {}
    return get_field_definitions(object_description)

