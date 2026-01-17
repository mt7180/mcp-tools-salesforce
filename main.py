from fastmcp import FastMCP
import requests

mcp = FastMCP("Test Data")

@mcp.tool()
def get_sobject_list(scratch_org_alias: str) -> dict:
    """gets a list of sobjects from a specific scratch org"""
    sObjects_url = f"https://{scratch_org_alias}.trailblaze.my.salesforce.com/services/data/v65.0/sobjects/"
    headers = {'Content-Type': 'application/json'}
    response = requests.get(sObjects_url, headers=headers)
    sobjects=  response.json()
    return sobjects if sobjects else {"error": "No sObjects found"}

if __name__ == "__main__":
    mcp.run()
