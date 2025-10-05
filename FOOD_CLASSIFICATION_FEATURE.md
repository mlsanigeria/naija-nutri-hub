# Food Classification Feature

## Overview
This document describes the newly implemented Food Classification feature for the Naija Nutri Hub project. This feature allows users to upload images of Nigerian food and receive AI-powered classification results.

## New Features Added

### 1. Food Classification Module (`src/food-classifier/image_classification.py`)
- **FoodClassifier Class**: A comprehensive class that handles Nigerian food identification using OpenAI Vision API
- **Image Preprocessing**: Automatic image resizing, format conversion, and validation
- **AI-Powered Classification**: Uses Azure OpenAI's GPT-4o-mini with vision capabilities to identify Nigerian foods
- **Food Suggestions**: Provides related food recommendations based on detected items
- **Error Handling**: Robust error handling for various edge cases

### 2. API Endpoints

#### POST `/classify-food`
- **Purpose**: Upload and classify food images
- **Authentication**: Requires JWT token
- **Input**: Image file (JPG, PNG, etc.)
- **Output**: Detailed classification results with confidence scores
- **Features**:
  - File type validation
  - File size limits (10MB max)
  - Comprehensive error handling
  - Related food suggestions

#### GET `/food-categories`
- **Purpose**: Get information about Nigerian food categories
- **Authentication**: None required
- **Output**: List of food categories with examples
- **Categories Included**:
  - Main dishes (Jollof Rice, Fried Rice, etc.)
  - Soups (Egusi, Ogbono, Pepper Soup, etc.)
  - Snacks (Suya, Akara, Moi Moi, etc.)
  - Side dishes (Plantain, Bole, Yam, etc.)
  - Drinks (Palm Wine, Zobo, Kunu, etc.)

### 3. Enhanced Data Models (`schemas/schema.py`)
- **FoodItem**: Model for individual food detection results
- **FoodClassificationResponse**: Complete response model for classification
- **FoodSuggestion**: Model for food recommendations
- **ErrorResponse**: Standardized error response model

### 4. Comprehensive Test Suite (`tests/test_food_classification.py`)
- **Endpoint Testing**: Tests for both API endpoints
- **Authentication Testing**: Validates proper authentication requirements
- **Error Handling Testing**: Tests various error scenarios
- **Module Testing**: Unit tests for the FoodClassifier class
- **Mock Testing**: Uses mocks to avoid external API dependencies during testing

## Nigerian Foods Supported

The system can identify 30+ Nigerian foods including:
- **Rice Dishes**: Jollof Rice, Fried Rice, Coconut Rice, Ofada Rice
- **Soups**: Egusi Soup, Ogbono Soup, Bitter Leaf Soup, Afang Soup, Pepper Soup
- **Staples**: Pounded Yam, Amala, Eba, Fufu
- **Snacks**: Suya, Akara, Moi Moi, Chin Chin, Puff Puff
- **Sides**: Plantain, Bole, Roasted Corn
- **And many more...**

## Environment Variables Required

To use the food classification feature, set up these environment variables in your `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

## Usage Examples

### 1. Classify Food Image
```python
import requests

# Login and get token first
login_response = requests.post("http://localhost:8000/login", data={
    "username": "your_username",
    "password": "your_password"
})
token = login_response.json()["access_token"]

# Upload and classify image
with open("jollof_rice.jpg", "rb") as f:
    files = {"file": f}
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("http://localhost:8000/classify-food", 
                           files=files, headers=headers)
    
print(response.json())
```

### 2. Get Food Categories
```python
import requests

response = requests.get("http://localhost:8000/food-categories")
print(response.json())
```

## Expected Response Format

### Classification Response
```json
{
  "foods_detected": [
    {
      "name": "Jollof Rice",
      "confidence": 0.95,
      "description": "Popular Nigerian rice dish cooked with tomatoes and spices",
      "category": "main_dish"
    }
  ],
  "is_nigerian_food": true,
  "overall_confidence": 0.95,
  "additional_notes": "Clear image of Jollof Rice with typical orange color",
  "related_foods": [
    {
      "name": "Fried Rice",
      "description": "Similar to Jollof Rice, popular Nigerian dish"
    }
  ]
}
```

## Technical Implementation Details

### Architecture
- **Modular Design**: Separate classification logic from API endpoints
- **Error Handling**: Comprehensive error handling at multiple levels
- **Scalability**: Designed to handle multiple concurrent requests
- **Testing**: Full test coverage with mocked external dependencies

### Image Processing Pipeline
1. **Validation**: Check file type and size
2. **Preprocessing**: Resize and convert to optimal format
3. **Encoding**: Convert to base64 for API transmission
4. **Classification**: Send to Azure OpenAI for analysis
5. **Post-processing**: Parse results and add related suggestions

### Security Features
- **Authentication Required**: All classification endpoints require valid JWT
- **File Validation**: Strict validation of uploaded files
- **Size Limits**: Prevent abuse with file size restrictions
- **Error Sanitization**: Safe error messages that don't expose system details

## Future Enhancements

This implementation provides a solid foundation for future enhancements:

1. **Nutritional Information**: Integrate with nutrition APIs
2. **Recipe Suggestions**: Connect to recipe generation features
3. **Location Services**: Link to restaurant finder functionality
4. **Batch Processing**: Support multiple image uploads
5. **Caching**: Add response caching for improved performance
6. **Analytics**: Track usage patterns and accuracy metrics

## Dependencies Added

The following new dependencies were added to support this feature:
- `Pillow==10.4.0` - Image processing
- `requests==2.31.0` - HTTP requests
- `pytest==8.3.3` - Testing framework

## Testing

Run the test suite with:
```bash
python -m pytest tests/test_food_classification.py -v
```

## Contributing

This feature was implemented as part of Hacktoberfest 2024 contributions to the Naija Nutri Hub project. The implementation follows the project's coding standards and contribution guidelines.

### Code Quality
- **Type Hints**: Full type annotation support
- **Documentation**: Comprehensive docstrings and comments
- **Error Handling**: Robust error handling and logging
- **Testing**: Complete test coverage
- **Standards**: Follows FastAPI and Python best practices

This food classification feature significantly enhances the Naija Nutri Hub platform by providing core AI functionality that was previously missing from the codebase.
