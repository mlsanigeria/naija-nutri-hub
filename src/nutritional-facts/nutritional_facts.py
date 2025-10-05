"""
Nutritional Facts Generation for Naija Nutri Hub

This module generates comprehensive nutritional information for Nigerian foods
using Azure OpenAI and local nutrition databases.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
import openai

# Import local tools
from .nutrition_tools import (
    get_food_nutrition,
    analyze_meal_nutrition,
    get_health_analysis,
    get_available_foods,
    nutrition_calculator,
    health_analyzer
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NutritionalFactsGenerator:
    """
    Main class for generating nutritional facts using Azure OpenAI and local databases.
    """
    
    def __init__(self):
        """Initialize the nutritional facts generator."""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        # Initialize tools
        self.nutrition_calculator = nutrition_calculator
        self.health_analyzer = health_analyzer
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts from YAML file."""
        try:
            prompt_file = os.path.join(os.path.dirname(__file__), "nutrition_prompt.yml")
            with open(prompt_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            return {}
    
    def generate_nutritional_facts(self, food_name: str, serving_size: float = 100) -> Dict[str, Any]:
        """
        Generate comprehensive nutritional facts for a Nigerian food.
        
        Args:
            food_name: Name of the Nigerian food
            serving_size: Serving size in grams (default: 100g)
            
        Returns:
            Comprehensive nutritional analysis
        """
        try:
            # Get local nutrition data first
            local_nutrition = get_food_nutrition(food_name, serving_size)
            
            # Get health analysis
            health_info = get_health_analysis(food_name)
            
            # Generate AI-enhanced analysis
            ai_analysis = self._generate_ai_analysis(food_name, local_nutrition, serving_size)
            
            # Combine all information
            result = {
                "food_name": food_name,
                "serving_size": f"{serving_size}g",
                "basic_nutrition": local_nutrition,
                "health_analysis": health_info,
                "ai_insights": ai_analysis,
                "data_sources": {
                    "local_database": local_nutrition is not None,
                    "ai_enhanced": ai_analysis is not None,
                    "health_database": bool(health_info)
                },
                "recommendations": self._generate_recommendations(food_name, local_nutrition, health_info)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating nutritional facts for {food_name}: {e}")
            return {
                "food_name": food_name,
                "error": f"Failed to generate nutritional facts: {str(e)}",
                "serving_size": f"{serving_size}g"
            }
    
    def _generate_ai_analysis(self, food_name: str, local_nutrition: Optional[Dict], serving_size: float) -> Optional[Dict[str, Any]]:
        """Generate AI-enhanced nutritional analysis using Azure OpenAI."""
        try:
            # Prepare context
            context = f"Food: {food_name}\nServing size: {serving_size}g"
            if local_nutrition:
                context += f"\nLocal nutrition data available: {json.dumps(local_nutrition, indent=2)}"
            
            # Get prompt
            analysis_prompt = self.prompts.get("nutrition_analysis_prompt", "").format(food_name=food_name)
            system_prompt = self.prompts.get("system_prompt", "")
            
            # Generate AI response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{analysis_prompt}\n\nContext:\n{context}"}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Parse structured response
                return self._parse_ai_response(content)
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None
    
    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        lines = content.strip().split('\n')
        result = {
            "analysis": content,
            "key_nutrients": [],
            "health_benefits": [],
            "preparation_notes": [],
            "dietary_considerations": []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if "nutrient" in line.lower():
                current_section = "key_nutrients"
            elif "benefit" in line.lower() or "health" in line.lower():
                current_section = "health_benefits"
            elif "preparation" in line.lower() or "cooking" in line.lower():
                current_section = "preparation_notes"
            elif "dietary" in line.lower() or "diet" in line.lower():
                current_section = "dietary_considerations"
            
            # Add content to appropriate section
            if current_section and line.startswith('-') or line.startswith('*'):
                result[current_section].append(line[1:].strip())
        
        return result
    
    def _generate_recommendations(self, food_name: str, nutrition: Optional[Dict], health_info: Dict) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        if nutrition:
            # Calorie-based recommendations
            calories = nutrition.get("calories", 0)
            if calories > 200:
                recommendations.append("Consider smaller portions for weight management")
            if calories < 100:
                recommendations.append("Good choice for low-calorie diets")
            
            # Protein recommendations
            protein = nutrition.get("protein", 0)
            if protein > 15:
                recommendations.append("Excellent source of protein - good for muscle building")
            
            # Sodium recommendations
            sodium = nutrition.get("sodium", 0)
            if sodium > 300:
                recommendations.append("High in sodium - limit if you have hypertension")
        
        # Health-based recommendations
        if health_info:
            benefits = health_info.get("benefits", [])
            if benefits:
                recommendations.extend([f"Health benefit: {benefit}" for benefit in benefits[:2]])
        
        # Default recommendations
        if not recommendations:
            recommendations.extend([
                "Enjoy as part of a balanced Nigerian diet",
                "Pair with vegetables for optimal nutrition"
            ])
        
        return recommendations
    
    def analyze_meal_nutrition(self, foods: List[Dict[str, Union[str, float]]]) -> Dict[str, Any]:
        """
        Analyze nutritional content of a complete Nigerian meal.
        
        Args:
            foods: List of food items with serving sizes
            
        Returns:
            Complete meal nutritional analysis
        """
        try:
            # Get basic meal analysis
            meal_analysis = analyze_meal_nutrition(foods)
            
            # Generate AI insights for the meal
            food_names = [food["name"] for food in foods]
            meal_insights = self._generate_meal_ai_insights(food_names)
            
            result = {
                "meal_composition": [food["name"] for food in foods],
                "total_nutrition": meal_analysis.get("total_nutrition", {}),
                "individual_foods": meal_analysis.get("individual_foods", []),
                "meal_summary": meal_analysis.get("meal_summary", {}),
                "ai_insights": meal_insights,
                "meal_recommendations": self._generate_meal_recommendations(meal_analysis),
                "cultural_context": self._get_cultural_context(food_names)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing meal nutrition: {e}")
            return {"error": f"Failed to analyze meal: {str(e)}"}
    
    def _generate_meal_ai_insights(self, food_names: List[str]) -> Optional[Dict[str, Any]]:
        """Generate AI insights for a complete meal."""
        try:
            foods_str = ", ".join(food_names)
            prompt = self.prompts.get("multi_food_analysis_prompt", "").format(food_list=foods_str)
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
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"analysis": content}
                
        except Exception as e:
            logger.error(f"Error generating meal AI insights: {e}")
            return None
    
    def _generate_meal_recommendations(self, meal_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the complete meal."""
        recommendations = []
        
        meal_summary = meal_analysis.get("meal_summary", {})
        total_calories = meal_summary.get("total_calories", 0)
        
        if total_calories > 800:
            recommendations.append("High-calorie meal - consider for main meals only")
        elif total_calories < 300:
            recommendations.append("Light meal - perfect for snacks or small portions")
        
        # Macronutrient balance
        breakdown = meal_summary.get("macronutrient_breakdown", {})
        protein_pct = breakdown.get("protein_percentage", 0)
        carbs_pct = breakdown.get("carbs_percentage", 0)
        fat_pct = breakdown.get("fat_percentage", 0)
        
        if protein_pct > 25:
            recommendations.append("High-protein meal - excellent for muscle building")
        if carbs_pct > 60:
            recommendations.append("Carb-rich meal - good for energy, consider portion sizes")
        if fat_pct > 35:
            recommendations.append("High-fat content - balance with vegetables")
        
        return recommendations
    
    def _get_cultural_context(self, food_names: List[str]) -> Dict[str, Any]:
        """Provide cultural context for the meal combination."""
        context = {
            "meal_type": "Nigerian combination",
            "typical_occasions": [],
            "regional_notes": [],
            "traditional_pairings": True
        }
        
        # Identify common Nigerian meal patterns
        has_rice = any("rice" in food.lower() for food in food_names)
        has_soup = any("soup" in food.lower() for food in food_names)
        has_swallow = any(food.lower() in ["pounded yam", "amala", "eba", "fufu"] for food in food_names)
        
        if has_rice:
            context["meal_type"] = "Rice-based meal"
            context["typical_occasions"] = ["Family dinners", "Celebrations", "Sunday meals"]
        
        if has_soup and has_swallow:
            context["meal_type"] = "Traditional soup and swallow combination"
            context["typical_occasions"] = ["Traditional meals", "Family gatherings"]
            context["regional_notes"] = ["Common across all Nigerian regions"]
        
        return context
    
    def get_comparative_analysis(self, food_names: List[str]) -> Dict[str, Any]:
        """
        Compare nutritional profiles of multiple Nigerian foods.
        
        Args:
            food_names: List of food names to compare
            
        Returns:
            Comparative nutritional analysis
        """
        try:
            # Get nutrition data for all foods
            foods_nutrition = {}
            for food in food_names:
                nutrition = get_food_nutrition(food)
                if nutrition:
                    foods_nutrition[food] = nutrition
            
            if not foods_nutrition:
                return {"error": "No nutritional data found for the specified foods"}
            
            # Generate AI comparison
            foods_str = ", ".join(food_names)
            comparison_prompt = self.prompts.get("comparative_analysis_prompt", "").format(food_names=foods_str)
            
            ai_comparison = self._generate_ai_analysis(foods_str, foods_nutrition, 100)
            
            # Calculate comparisons
            comparisons = self._calculate_nutritional_comparisons(foods_nutrition)
            
            result = {
                "foods_compared": food_names,
                "individual_nutrition": foods_nutrition,
                "comparisons": comparisons,
                "ai_analysis": ai_comparison,
                "recommendations": self._generate_comparison_recommendations(comparisons)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comparative analysis: {e}")
            return {"error": f"Failed to generate comparison: {str(e)}"}
    
    def _calculate_nutritional_comparisons(self, foods_nutrition: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate nutritional comparisons between foods."""
        comparisons = {
            "highest_calories": "",
            "highest_protein": "",
            "lowest_calories": "",
            "highest_fiber": "",
            "lowest_sodium": ""
        }
        
        if not foods_nutrition:
            return comparisons
        
        # Find highest/lowest values
        calories = {food: data.get("calories", 0) for food, data in foods_nutrition.items()}
        proteins = {food: data.get("protein", 0) for food, data in foods_nutrition.items()}
        fibers = {food: data.get("fiber", 0) for food, data in foods_nutrition.items()}
        sodiums = {food: data.get("sodium", 0) for food, data in foods_nutrition.items()}
        
        if calories:
            comparisons["highest_calories"] = max(calories, key=calories.get)
            comparisons["lowest_calories"] = min(calories, key=calories.get)
        
        if proteins:
            comparisons["highest_protein"] = max(proteins, key=proteins.get)
        
        if fibers:
            comparisons["highest_fiber"] = max(fibers, key=fibers.get)
        
        if sodiums:
            comparisons["lowest_sodium"] = min(sodiums, key=sodiums.get)
        
        return comparisons
    
    def _generate_comparison_recommendations(self, comparisons: Dict[str, str]) -> List[str]:
        """Generate recommendations based on comparisons."""
        recommendations = []
        
        if comparisons.get("highest_protein"):
            recommendations.append(f"For protein: Choose {comparisons['highest_protein']}")
        
        if comparisons.get("lowest_calories"):
            recommendations.append(f"For weight management: Choose {comparisons['lowest_calories']}")
        
        if comparisons.get("highest_fiber"):
            recommendations.append(f"For digestive health: Choose {comparisons['highest_fiber']}")
        
        if comparisons.get("lowest_sodium"):
            recommendations.append(f"For low-sodium diet: Choose {comparisons['lowest_sodium']}")
        
        return recommendations


# Global instance
nutritional_facts_generator = NutritionalFactsGenerator()


def generate_nutrition_facts(food_name: str, serving_size: float = 100) -> Dict[str, Any]:
    """
    Generate comprehensive nutritional facts for a Nigerian food.
    
    Args:
        food_name: Name of the food
        serving_size: Serving size in grams
        
    Returns:
        Complete nutritional analysis
    """
    return nutritional_facts_generator.generate_nutritional_facts(food_name, serving_size)


def analyze_complete_meal(foods: List[Dict[str, Union[str, float]]]) -> Dict[str, Any]:
    """
    Analyze nutritional content of a complete meal.
    
    Args:
        foods: List of food items with serving sizes
        
    Returns:
        Complete meal analysis
    """
    return nutritional_facts_generator.analyze_meal_nutrition(foods)


def compare_foods(food_names: List[str]) -> Dict[str, Any]:
    """
    Compare nutritional profiles of multiple foods.
    
    Args:
        food_names: List of food names to compare
        
    Returns:
        Comparative analysis
    """
    return nutritional_facts_generator.get_comparative_analysis(food_names)


def get_nutrition_database_foods() -> List[str]:
    """Get list of foods available in the nutrition database."""
    return get_available_foods()
