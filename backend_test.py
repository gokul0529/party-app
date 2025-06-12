import requests
import unittest
import json
import sys

class PartyDrinkCalculatorAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://36b9a701-953a-4562-b6a8-cb932b300849.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return success, response.json() if response.text else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "",
            200
        )
        self.assertTrue(success)
        self.assertIn("message", response)
        return success

    def test_drink_options(self):
        """Test the drink options endpoint"""
        success, response = self.run_test(
            "Drink Options",
            "GET",
            "drink-options",
            200
        )
        self.assertTrue(success)
        self.assertIn("drink_types", response)
        self.assertIn("mixers", response)
        self.assertIn("intensities", response)
        return success

    def test_calculate_party_drinks(self):
        """Test the calculate endpoint with valid data"""
        data = {
            "guests": 10,
            "drinker_type": "medium",
            "duration": 4,
            "drink_types": ["beer", "wine"],
            "mixers": []
        }
        success, response = self.run_test(
            "Calculate Party Drinks",
            "POST",
            "calculate",
            200,
            data=data
        )
        self.assertTrue(success)
        self.assertIn("drinks", response)
        self.assertIn("extras", response)
        self.assertIn("total_cost_estimate", response)
        self.assertIn("fun_message", response)
        
        # Verify calculation results
        self.assertEqual(len(response["drinks"]), 2)  # beer and wine
        self.assertEqual(len(response["extras"]), 2)  # cups and ice
        
        # Print calculation details for verification
        print("\nCalculation Results:")
        print(f"Total Cost: ${response['total_cost_estimate']}")
        for drink in response["drinks"]:
            print(f"{drink['drink_type']}: {drink['amount']} {drink['unit']} - {drink['description']}")
        
        return success

    def test_calculate_with_spirits_and_mixers(self):
        """Test the calculate endpoint with spirits and mixers"""
        data = {
            "guests": 10,
            "drinker_type": "medium",
            "duration": 4,
            "drink_types": ["vodka", "rum"],
            "mixers": ["soda", "juice"]
        }
        success, response = self.run_test(
            "Calculate with Spirits and Mixers",
            "POST",
            "calculate",
            200,
            data=data
        )
        self.assertTrue(success)
        self.assertIn("drinks", response)
        self.assertIn("mixers", response)
        self.assertIn("extras", response)
        
        # Verify mixers are included
        self.assertTrue(len(response["mixers"]) > 0)
        
        # Print mixer details
        print("\nMixer Results:")
        for mixer in response["mixers"]:
            print(f"{mixer['drink_type']}: {mixer['amount']} {mixer['unit']} - {mixer['description']}")
        
        return success

    def test_calculate_edge_cases(self):
        """Test the calculate endpoint with edge cases"""
        # Test with minimum values
        data = {
            "guests": 1,
            "drinker_type": "light",
            "duration": 1,
            "drink_types": ["beer"],
            "mixers": []
        }
        success1, response1 = self.run_test(
            "Calculate with Minimum Values",
            "POST",
            "calculate",
            200,
            data=data
        )
        
        # Test with high values
        data = {
            "guests": 50,
            "drinker_type": "heavy",
            "duration": 8,
            "drink_types": ["beer", "wine", "vodka", "whiskey", "rum", "gin"],
            "mixers": ["soda", "juice", "tonic"]
        }
        success2, response2 = self.run_test(
            "Calculate with High Values",
            "POST",
            "calculate",
            200,
            data=data
        )
        
        return success1 and success2

    def test_invalid_request(self):
        """Test the calculate endpoint with invalid data"""
        # Missing required field
        data = {
            "guests": 10,
            "duration": 4,
            "drink_types": ["beer"]
            # Missing drinker_type
        }
        success, _ = self.run_test(
            "Calculate with Invalid Data",
            "POST",
            "calculate",
            422,  # Validation error
            data=data
        )
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 Running Party Drink Calculator API Tests 🧪")
        
        tests = [
            self.test_health_check,
            self.test_drink_options,
            self.test_calculate_party_drinks,
            self.test_calculate_with_spirits_and_mixers,
            self.test_calculate_edge_cases,
            self.test_invalid_request
        ]
        
        for test in tests:
            test()
        
        # Print results
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = PartyDrinkCalculatorAPITest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
