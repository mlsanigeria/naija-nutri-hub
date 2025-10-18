"""
Purchase Location Module

This module provides functionality to search for purchase locations
of food items using AI-powered web search and structured output.
"""

import yaml
import os
from typing import List, Dict, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from location_tools import search_purchase_options
from langchain_google_genai import ChatGoogleGenerativeAI

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
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.2,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

structured_llm = llm.with_structured_output(PurchaseLocation)


def purchase_location_single(item_name: str, user_location: str) -> Dict[str, str]:
    """
    Find purchase location for a single food item.
    
    Args:
        item_name: Name of the food item
        user_location: User's location (e.g., "Lagos, Nigeria")
    
    Returns:
        Dictionary with purchase information in JSON format:
        {
            "item_name": "Avocado",
            "price": "₦500",
            "location": "Shoprite Lagos",
            "website": "https://example.com"
        }
    """
    search_results = search_purchase_options.invoke({
        "item_name": item_name,
        "user_location": user_location
    })
    
    query = f"""Extract purchase information for {item_name} in {user_location} from these search results:

{search_results}

Provide structured data with item name, price, location, and website."""
    
    result = structured_llm.invoke(query)
    return result.model_dump()







# Backwards compatibility alias
purchase_location_direct = purchase_location_single