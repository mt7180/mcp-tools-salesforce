from fastmcp import FastMCP
import requests

mcp = FastMCP("Test Data")

@mcp.tool()
def get_schema(domain_name: str) -> dict:
    sObjects_url = f"https://{domain_name}.my.salesforce.com/services/data/v65.0/sobjects/"
    response = requests.get(sObjects_url)
    return response.json()

if __name__ == "__main__":
    mcp.run()
