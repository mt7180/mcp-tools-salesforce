
from typing import Any
from fastmcp import Client, FastMCP, Context
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from pydantic import BaseModel
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed, SalesforceExpiredSession
from rich.console import Console

import os
from dotenv import load_dotenv

console = Console()
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
USERNAME = os.getenv('USERNAME')
PRIVATE_KEY_FILE = os.getenv('PRIVATE_KEY_FILE')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

if PRIVATE_KEY_FILE:
    with open(PRIVATE_KEY_FILE, 'r') as f:
        PRIVATE_KEY = f.read()

mcp = FastMCP("Custom Salesforce MCP Server",
    sampling_handler=OpenAISamplingHandler(default_model="gpt-4o-mini"),
    sampling_handler_behavior="fallback")

class TokenError(Exception):
    pass

class SalesforceProvider:
    def __init__(
        self,
        client_id: str | None,
        username: str | None,
        private_key: str | None,
        domain: str = "login",
    ):
        self.client_id = client_id
        self.username = username
        self.private_key = private_key
        self.domain = domain
        self._sf: Salesforce | None = None

    @staticmethod
    def _auth_error_message(exc: SalesforceAuthenticationFailed) -> str:
        details = getattr(exc, "content", str(exc))
        return f"Failed to authenticate with Salesforce OAuth: {details}"

    def _login(self) -> Salesforce:
        if not self.client_id or not self.username or not self.private_key:
            raise TokenError(
                "Missing Salesforce credentials. Set CLIENT_ID, USERNAME and PRIVATE_KEY (or PRIVATE_KEY_FILE)."
            )

        try:
            return Salesforce(
                username=self.username,
                consumer_key=self.client_id,
                privatekey=self.private_key,
                domain=self.domain,
            )
        except SalesforceAuthenticationFailed as exc:
            raise TokenError(self._auth_error_message(exc)) from exc

    def _client(self) -> Salesforce:
        if self._sf is None:
            self._sf = self._login()
        return self._sf

    def _refresh_client(self) -> Salesforce:
        self._sf = self._login()
        return self._sf

    def _call(self, method_name: str, /, *args: Any, **kwargs: Any) -> Any:
        for _ in range(2):
            client = self._client()
            try:
                method = getattr(client, method_name)
                return method(*args, **kwargs)
            except SalesforceExpiredSession:
                self._refresh_client()
            except SalesforceAuthenticationFailed as exc:
                self._sf = None
                raise TokenError(self._auth_error_message(exc)) from exc

        raise TokenError("Salesforce session expired even after refresh.")

    def query(self, soql_query: str) -> dict[str, Any]:
        return self._call("query", soql_query)

    def describe(self, sobject_name: str) -> dict[str, Any]:
        for _ in range(2):
            client = self._client()
            try:
                return getattr(client, sobject_name).describe()
            except SalesforceExpiredSession:
                self._refresh_client()
            except SalesforceAuthenticationFailed as exc:
                self._sf = None
                raise TokenError(self._auth_error_message(exc)) from exc

        raise TokenError("Salesforce session expired even after refresh.")

    def restful(self, endpoint: str, method: str = "GET", **kwargs: Any) -> Any:
        return self._call("restful", endpoint, method=method, **kwargs)


sf_provider = SalesforceProvider(
    client_id=CLIENT_ID,
    username=USERNAME,
    private_key=PRIVATE_KEY,
)


@mcp.tool()
async def query_salesforce(soql_query: str) -> str:
    """Run a SOQL query against the Salesforce org and return results."""
    result = sf_provider.query(soql_query)
    records = result.get("records", [])
    return str(records)


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

    basic_sobject_types = [
        'Account', 'Contact', 'Case', 'User'
    ]

    data_model = {}

    for sobject in basic_sobject_types:
        object_description = sf_provider.describe(sobject)
        if object_description['createable']:
            data_model[sobject] = await extract_relevant_fields(object_description)
    return data_model

    
@mcp.tool()
async def describe_sobject(sobject_name: str) -> dict:
    """returns the fields of a specific sObject in the salesforce scratch org"""
    console.print(f"    [bold cyan]SERVER[/] Describe {sobject_name}...")
    object_description = sf_provider.describe(sobject_name)

    if not object_description['createable']:
        return {}
    return await extract_relevant_fields(object_description)

class ResultType(BaseModel):
    record: dict[str, Any]
    
@mcp.tool()
async def generate_nested_record(user_specification: str, ctx: Context) -> ResultType:
    """ generate a Salesforce nested record according to the user_specification. 
    Available tools for sampling:
    - describe_sobject: can be used to look up sObject schemas and their fields.
    - tree_api_record_example: returns an example of a Composite Tree API compatible nested record.
    """
    
    console.print("    [bold cyan]SERVER[/] Starting to generate record...")
    prompt = f"""Create a nested record, that is compatible 
        with the Salesforce Composite Tree API and conforms to the provided user_specification.
        
        user_specification:\n\n {user_specification}
    """

    draft_record = await ctx.sample(
        messages=prompt,
        system_prompt="You are a Salesforce expert. Use describe_sobject when needed.",
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
    response = sf_provider.restful(endpoint, method='POST', json=record)
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
   
    handler = OpenAISamplingHandler(default_model="gpt-5")

    async with Client(mcp, sampling_handler=handler) as client:
        user_specification = "create a salesforce nested record for a case where an old lady has trouble with her wlan router. "
        result = await client.call_tool("generate_nested_record", {"user_specification": user_specification})
        console.print("LLM Response:", result)

       # result = await client.call_tool("query_salesforce", {"soql": "SELECT Id, Name FROM Account"})
       # console.print("LLM Response:", result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())