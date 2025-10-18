"""
Test suite for purchase_location module
Location: main_folder/tests/test_purchase_location.py
"""

import pytest
import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'purchase-location'))

from purchase_location import get_purchase_locations, PurchaseLocation


class TestBasicFunctionality:
    """Test core functionality"""
    
    def test_returns_dict(self):
        """Test that function returns a dictionary"""
        result = get_purchase_locations(["banana"], "Lagos, Nigeria")
        assert isinstance(result, dict)
    
    def test_single_item(self):
        """Test single item returns correct structure"""
        result = get_purchase_locations(["rice"], "Lagos, Nigeria")
        assert len(result) == 1
        assert "rice" in result
        assert 'item_name' in result["rice"]
        assert 'price' in result["rice"]
        assert 'location' in result["rice"]
        assert 'website' in result["rice"]
    
    def test_multiple_items(self):
        """Test multiple items returns all items"""
        items = ["rice", "beans"]
        result = get_purchase_locations(items, "Lagos, Nigeria")
        assert len(result) == len(items)
        for item in items:
            assert item in result


class TestDataFormat:
    """Test data format and types"""
    
    def test_all_fields_are_strings(self):
        """Test all fields are strings"""
        result = get_purchase_locations(["tomato"], "Lagos, Nigeria")
        info = result["tomato"]
        assert all(isinstance(v, str) for k, v in info.items() if k != 'error')
    
    def test_json_serializable(self):
        """Test results can be serialized to JSON"""
        result = get_purchase_locations(["banana"], "Lagos, Nigeria")
        json_str = json.dumps(result)
        loaded = json.loads(json_str)
        assert loaded == result


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_list(self):
        """Test empty list returns empty dict"""
        result = get_purchase_locations([], "Lagos, Nigeria")
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_special_characters(self):
        """Test special characters in item names"""
        result = get_purchase_locations(["jollof & rice"], "Lagos, Nigeria")
        assert "jollof & rice" in result


class TestPurchaseLocationModel:
    """Test Pydantic model"""
    
    def test_model_creation(self):
        """Test model can be created"""
        data = {
            "item_name": "Avocado",
            "price": "₦500",
            "location": "Shoprite",
            "website": "https://example.com"
        }
        model = PurchaseLocation(**data)
        assert model.item_name == "Avocado"
        assert model.model_dump() == data


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])