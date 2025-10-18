"""
Purchase Location Module

This module provides functionality to search for purchase locations
of food items using AI-powered web search and structured output.
"""

import yaml
import os
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from location_tools import search_purchase_options
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI
# Load environment variables
load_dotenv()


class PurchaseLocation(BaseModel):
    """Structured information about where to purchase a food item."""
    item_name: str = Field(description="Name of the food item")
    price: str = Field(description="Price if available, otherwise 'N/A'")
    location: str = Field(description="Store name or address")
    website: str = Field(description="Online store link if applicable, otherwise 'N/A'")


# Load prompt from YAML
try:
    with open("purchase_location/location_prompt.yml", "r") as f:
        prompt_data = yaml.safe_load(f)
    CUSTOM_PROMPT = prompt_data["prompt_template"]
except FileNotFoundError:
    CUSTOM_PROMPT = """You are an AI agent that helps users find where to purchase food items locally or online.

The user provides:
  - item_name: {item_name}
  - location: {user_location}
  - retrieved_info: {retrieved_info}

Based on this information, extract and return the purchase details."""


# Configure Google Gemini with structured output
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash-exp",
#     temperature=0.2,
#     google_api_key=os.getenv("GOOGLE_API_KEY")
# )

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    temperature=0.2
)

structured_llm = llm.with_structured_output(PurchaseLocation)


def get_purchase_locations(items: List[str], user_location: str) -> Dict[str, Dict[str, str]]:
    """
    Find purchase locations for food items.
    
    Args:
        items: List of food item names (e.g., ["avocado", "banana", "rice"])
               For single item, pass as list with one element: ["avocado"]
        user_location: User's location (e.g., "Lagos, Nigeria")
    
    Returns:
        Dictionary mapping item names to their purchase information in JSON format:
        {
            "avocado": {
                "item_name": "Avocado",
                "price": "₦500",
                "location": "Shoprite Lagos",
                "website": "https://example.com"
            },
            "banana": {
                "item_name": "Banana",
                "price": "₦200",
                "location": "Market Square",
                "website": "N/A"
            }
        }
    
    Examples:
        >>> # Single item
        >>> result = get_purchase_locations(["avocado"], "Lagos, Nigeria")
        >>> print(result["avocado"]["price"])
        
        >>> # Multiple items
        >>> results = get_purchase_locations(["rice", "beans", "yam"], "Lagos, Nigeria")
        >>> print(results["rice"]["price"])
    """
    results = {}
    
    for item_name in items:
        try:
            search_results = search_purchase_options.invoke({
                "item_name": item_name,
                "user_location": user_location
            })
            
            query = f"""Extract purchase information for {item_name} in {user_location} from these search results:

{search_results}

Provide structured data with item name, price, location, and website."""
            
            result = structured_llm.invoke(query)
            results[item_name] = result.model_dump()
                
        except Exception as e:
            results[item_name] = {
                "item_name": item_name,
                "price": "N/A",
                "location": "N/A",
                "website": "N/A",
                "error": str(e)
            }
    
    return results