"""
Recipe Generation for Naija Nutri Hub

This module generates comprehensive Nigerian food recipes using AI and local databases.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
import openai

# Import local tools
from .recipe_tools import (
    generate_recipe,
    get_recipe_suggestions,
    get_cooking_tips,
    get_available_recipes,
    search_recipes_by_ingredient,
    recipe_generator
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecipeGenerator:
    """
    Main class for generating recipes using Azure OpenAI and local databases.
    """
    
    def __init__(self):
        """Initialize the recipe generator."""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        # Initialize tools
        self.recipe_tools = recipe_generator
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts from YAML file."""
        try:
            prompt_file = os.path.join(os.path.dirname(__file__), "recipe_prompt.yml")
            with open(prompt_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            return {}
    
    def generate_recipe(self, food_name: str) -> Dict[str, Any]:
        """
        Generate a comprehensive recipe for a Nigerian food.
        
        Args:
            food_name: Name of the Nigerian food
            
        Returns:
            Complete recipe with AI enhancements
        """
        try:
            # Get local recipe data first
            local_recipe = generate_recipe(food_name)
            
            # Generate AI-enhanced recipe
            ai_recipe = self._generate_ai_recipe(food_name, local_recipe)
            
            # Combine local and AI data
            result = {
                "food_name": food_name,
                "local_recipe": local_recipe,
                "ai_enhanced_recipe": ai_recipe,
                "data_sources": {
                    "local_database": local_recipe is not None,
                    "ai_generated": ai_recipe is not None,
                    "external_api": False
                },
                "cooking_tips": self._get_enhanced_cooking_tips(food_name, local_recipe, ai_recipe),
                "cultural_insights": self._get_cultural_insights(food_name, local_recipe, ai_recipe)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating recipe for {food_name}: {e}")
            return {
                "food_name": food_name,
                "error": f"Failed to generate recipe: {str(e)}"
            }
    
    def _generate_ai_recipe(self, food_name: str, local_recipe: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Generate AI-enhanced recipe using Azure OpenAI."""
        try:
            # Prepare context
            context = f"Food: {food_name}"
            if local_recipe:
                context += f"\nLocal recipe available: {json.dumps(local_recipe, indent=2)}"
            
            # Get prompt
            recipe_prompt = self.prompts.get("recipe_generation_prompt", "").format(food_name=food_name)
            system_prompt = self.prompts.get("system_prompt", "")
            
            # Generate AI response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{recipe_prompt}\n\nContext:\n{context}"}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Parse structured response if JSON fails
                return self._parse_ai_response(content)
                
        except Exception as e:
            logger.error(f"Error in AI recipe generation: {e}")
            return None
    
    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        lines = content.strip().split('\n')
        result = {
            "recipe_name": "AI Generated Recipe",
            "description": "",
            "ingredients": [],
            "instructions": [],
            "cooking_tips": [],
            "raw_response": content
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if "ingredient" in line.lower() or "recipe_name" in line.lower():
                current_section = "ingredients"
            elif "instruction" in line.lower() or "step" in line.lower():
                current_section = "instructions"
            elif "tip" in line.lower():
                current_section = "cooking_tips"
            elif "description" in line.lower():
                current_section = "description"
            
            # Add content to appropriate section
            if current_section and (line.startswith('-') or line.startswith('*') or line.startswith('1.')):
                cleaned_line = line[1:].strip() if line.startswith(('-', '*')) else line
                if current_section == "description" and not result["description"]:
                    result["description"] = cleaned_line
                elif current_section in ["ingredients", "instructions", "cooking_tips"]:
                    result[current_section].append(cleaned_line)
        
        return result
    
    def _get_enhanced_cooking_tips(self, food_name: str, local_recipe: Optional[Dict], ai_recipe: Optional[Dict]) -> List[str]:
        """Combine cooking tips from multiple sources."""
        tips = []
        
        # Add local tips
        if local_recipe and "cooking_tips" in local_recipe:
            tips.extend(local_recipe["cooking_tips"])
        
        # Add AI tips
        if ai_recipe and "cooking_tips" in ai_recipe:
            tips.extend(ai_recipe["cooking_tips"])
        
        # Add general tips
        general_tips = get_cooking_tips(food_name)
        tips.extend(general_tips)
        
        # Remove duplicates and return unique tips
        return list(dict.fromkeys(tips))
    
    def _get_cultural_insights(self, food_name: str, local_recipe: Optional[Dict], ai_recipe: Optional[Dict]) -> Dict[str, Any]:
        """Extract cultural insights about the dish."""
        insights = {
            "cultural_context": "",
            "regional_variations": [],
            "traditional_occasions": [],
            "modern_adaptations": []
        }
        
        if local_recipe:
            insights["cultural_context"] = local_recipe.get("cultural_context", "")
            insights["regional_variations"] = local_recipe.get("variations", [])
        
        if ai_recipe:
            if "cultural_context" in ai_recipe:
                insights["cultural_context"] = ai_recipe["cultural_context"]
        
        return insights
    
    def generate_multiple_recipes(self, food_names: List[str]) -> Dict[str, Any]:
        """
        Generate recipes for multiple Nigerian foods.
        
        Args:
            food_names: List of food names
            
        Returns:
            Combined recipe collection with meal planning suggestions
        """
        try:
            recipes = {}
            for food_name in food_names:
                recipes[food_name] = self.generate_recipe(food_name)
            
            # Generate meal planning suggestions
            meal_planning = self._generate_meal_planning(food_names, recipes)
            
            result = {
                "recipes": recipes,
                "meal_planning": meal_planning,
                "total_recipes": len(recipes)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating multiple recipes: {e}")
            return {"error": f"Failed to generate recipes: {str(e)}"}
    
    def _generate_meal_planning(self, food_names: List[str], recipes: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meal planning suggestions for multiple dishes."""
        try:
            foods_str = ", ".join(food_names)
            prompt = self.prompts.get("recipe_pairing_prompt", "").format(food_name=foods_str)
            system_prompt = self.prompts.get("system_prompt", "")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            return {
                "pairing_suggestions": content,
                "complementary_dishes": self._find_complementary_dishes(food_names),
                "cooking_sequence": self._suggest_cooking_sequence(recipes)
            }
            
        except Exception as e:
            logger.error(f"Error generating meal planning: {e}")
            return {"pairing_suggestions": "Consider traditional Nigerian meal combinations"}
    
    def _find_complementary_dishes(self, food_names: List[str]) -> List[str]:
        """Find dishes that complement the given foods."""
        complements = {
            "jollof rice": ["fried plantain", "moi moi", "chicken", "coleslaw"],
            "egusi soup": ["pounded yam", "eba", "fufu", "amala"],
            "suya": ["bread", "onions", "tomatoes", "beer"],
            "pounded yam": ["egusi soup", "ogbono soup", "bitter leaf soup"],
            "fried rice": ["chicken", "plantain", "moi moi", "salad"]
        }
        
        suggestions = []
        for food in food_names:
            if food.lower() in complements:
                suggestions.extend(complements[food.lower()])
        
        return list(set(suggestions))
    
    def _suggest_cooking_sequence(self, recipes: Dict[str, Any]) -> List[str]:
        """Suggest optimal cooking sequence for multiple dishes."""
        # Simple heuristic based on cooking times
        sequence = []
        
        for food_name, recipe_data in recipes.items():
            if recipe_data.get("local_recipe"):
                cook_time = recipe_data["local_recipe"].get("cook_time", "30 minutes")
                # Extract numeric value for sorting
                try:
                    minutes = int(''.join(filter(str.isdigit, cook_time)))
                    sequence.append((food_name, minutes))
                except:
                    sequence.append((food_name, 30))  # Default
        
        # Sort by cooking time (longest first)
        sequence.sort(key=lambda x: x[1], reverse=True)
        
        return [f"Start with {food} (longest cooking time)" for food, _ in sequence]
    
    def get_recipe_modifications(self, food_name: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recipe modifications based on dietary preferences.
        
        Args:
            food_name: Name of the dish
            preferences: Dictionary with dietary preferences
            
        Returns:
            Modified recipe suggestions
        """
        try:
            # Get base recipe
            base_recipe = self.generate_recipe(food_name)
            
            # Generate AI modifications
            modification_prompt = self.prompts.get("recipe_modification_prompt", "").format(
                food_name=food_name,
                dietary_restrictions=preferences.get("dietary_restrictions", "None"),
                serving_size=preferences.get("serving_size", 4),
                time_limit=preferences.get("time_limit", 60),
                available_ingredients=", ".join(preferences.get("available_ingredients", []))
            )
            
            system_prompt = self.prompts.get("system_prompt", "")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": modification_prompt}
                ],
                max_tokens=1500,
                temperature=0.4
            )
            
            modifications = response.choices[0].message.content
            
            return {
                "original_recipe": base_recipe,
                "modifications": modifications,
                "preferences_applied": preferences
            }
            
        except Exception as e:
            logger.error(f"Error generating recipe modifications: {e}")
            return {"error": f"Failed to generate modifications: {str(e)}"}


# Global instance
recipe_generator_ai = RecipeGenerator()


def generate_nigerian_recipe(food_name: str) -> Dict[str, Any]:
    """
    Generate a comprehensive recipe for a Nigerian food.
    
    Args:
        food_name: Name of the food
        
    Returns:
        Complete recipe with AI enhancements
    """
    return recipe_generator_ai.generate_recipe(food_name)


def generate_multiple_nigerian_recipes(food_names: List[str]) -> Dict[str, Any]:
    """
    Generate recipes for multiple Nigerian foods with meal planning.
    
    Args:
        food_names: List of food names
        
    Returns:
        Collection of recipes with meal planning suggestions
    """
    return recipe_generator_ai.generate_multiple_recipes(food_names)


def get_recipe_modifications(food_name: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get recipe modifications based on dietary preferences.
    
    Args:
        food_name: Name of the dish
        preferences: Dietary preferences and constraints
        
    Returns:
        Modified recipe suggestions
    """
    return recipe_generator_ai.get_recipe_modifications(food_name, preferences)


def get_available_nigerian_recipes() -> List[str]:
    """Get list of Nigerian recipes available in the database."""
    return get_available_recipes()


def search_recipes_by_ingredients(ingredient: str) -> List[str]:
    """
    Search for recipes containing a specific ingredient.
    
    Args:
        ingredient: Ingredient to search for
        
    Returns:
        List of recipe names
    """
    return search_recipes_by_ingredient(ingredient)
