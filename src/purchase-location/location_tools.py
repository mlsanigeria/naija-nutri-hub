# Function Calling and API Integration Script
# location_tools.py
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

@tool
def search_purchase_options(item_name: str, user_location: str) -> str:
    """
    Searches for where a food item can be bought near the user location or online.
    Returns summarized web results.
    """
    tavily = TavilySearch(max_results=5)
    query = f"where to buy {item_name} near {user_location}"
    results = tavily.run(query)
    return results
