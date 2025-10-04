#!/usr/bin/env python3
"""
Campus Section API Testing Script
Tests the specific campus endpoints mentioned in the review request:
1. Inter-College Competitions: GET /api/inter-college/competitions
2. Prize Challenges: GET /api/prize-challenges  
3. Campus Reputation: GET /api/campus/reputation
"""

import requests
import json
import sys
from datetime import datetime

class CampusEndpointTester:
    def __init__(self):
        self.base_url = "https://campus-engage-5.preview.emergentagent.com/api"
        self.token = None
        self.user_id = None
        self.test_results = []
        
        # Test user credentials
        self.test_email = f"campus.tester{int(datetime.now().timestamp())}@gmail.com"
        self.test_password = "CampusTest@123"

    def log_result(self, test_name, success, details):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def register_and_login(self):
        """Register a test user and get authentication token"""
        print("🔐 Setting up authentication...")
        
        # Register user
        user_data = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Campus Tester",
            "role": "Student",
            "student_level": "undergraduate",
            "location": "Mumbai, Maharashtra",
            "university": "Indian Institute of Technology Bombay",
            "skills": ["Testing", "Analysis"],
            "avatar": "man"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/register", json=user_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                if data.get("user"):
                    self.user_id = data["user"].get("id")
                print(f"✅ Registration successful - Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Registration failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"    Error: {error_data}")
                except:
                    print(f"    Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return False

    def make_authenticated_request(self, endpoint, method="GET", data=None):
        """Make an authenticated API request"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}' if self.token else ''
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            return response
        except Exception as e:
            print(f"❌ Request error for {endpoint}: {str(e)}")
            return None

    def test_inter_college_competitions(self):
        """Test GET /api/inter-college/competitions endpoint"""
        print("\n🏆 Testing Inter-College Competitions Endpoint")
        print("-" * 50)
        
        # Test without authentication
        response = requests.get(f"{self.base_url}/inter-college/competitions", timeout=30)
        if response.status_code == 403:
            self.log_result("Authentication Required", True, "Endpoint properly protected")
        else:
            self.log_result("Authentication Required", False, f"Expected 403, got {response.status_code}")
        
        # Test with authentication
        response = self.make_authenticated_request("inter-college/competitions")
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check response structure
                if isinstance(data, dict):
                    competitions = data.get("competitions", [])
                    user_university = data.get("user_university")
                    
                    self.log_result("Response Structure", True, f"Found {len(competitions)} competitions, User university: {user_university}")
                    
                    # Check competition data structure
                    if competitions:
                        comp = competitions[0]
                        required_fields = ["id", "title", "description", "status"]
                        missing_fields = [field for field in required_fields if field not in comp]
                        
                        if not missing_fields:
                            self.log_result("Competition Data Structure", True, f"Sample competition: {comp.get('title', 'N/A')}")
                        else:
                            self.log_result("Competition Data Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Competition Data", True, "No competitions found (expected if none created)")
                    
                    # Print sample data
                    print(f"    Sample response: {json.dumps(data, indent=2)[:500]}...")
                    
                else:
                    self.log_result("Response Format", False, f"Expected dict, got {type(data)}")
                    
            except json.JSONDecodeError:
                self.log_result("JSON Response", False, "Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            self.log_result("API Call", False, f"Expected 200, got {status}")

    def test_prize_challenges(self):
        """Test GET /api/prize-challenges endpoint"""
        print("\n🏅 Testing Prize Challenges Endpoint")
        print("-" * 50)
        
        # Test without authentication
        response = requests.get(f"{self.base_url}/prize-challenges", timeout=30)
        if response.status_code == 403:
            self.log_result("Authentication Required", True, "Endpoint properly protected")
        else:
            self.log_result("Authentication Required", False, f"Expected 403, got {response.status_code}")
        
        # Test with authentication
        response = self.make_authenticated_request("prize-challenges")
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check response structure
                if isinstance(data, dict):
                    challenges = data.get("challenges", [])
                    user_level = data.get("user_level")
                    user_streak = data.get("user_streak")
                    
                    self.log_result("Response Structure", True, f"Found {len(challenges)} challenges, User level: {user_level}, User streak: {user_streak}")
                    
                    # Check challenge data structure
                    if challenges:
                        challenge = challenges[0]
                        required_fields = ["id", "title", "description", "challenge_type"]
                        missing_fields = [field for field in required_fields if field not in challenge]
                        
                        if not missing_fields:
                            self.log_result("Challenge Data Structure", True, f"Sample challenge: {challenge.get('title', 'N/A')}")
                        else:
                            self.log_result("Challenge Data Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Challenge Data", True, "No challenges found (expected if none created)")
                    
                    # Print sample data
                    print(f"    Sample response: {json.dumps(data, indent=2)[:500]}...")
                    
                else:
                    self.log_result("Response Format", False, f"Expected dict, got {type(data)}")
                    
            except json.JSONDecodeError:
                self.log_result("JSON Response", False, "Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            self.log_result("API Call", False, f"Expected 200, got {status}")

    def test_campus_reputation(self):
        """Test GET /api/campus/reputation endpoint"""
        print("\n🏛️ Testing Campus Reputation Endpoint")
        print("-" * 50)
        
        # Test without authentication
        response = requests.get(f"{self.base_url}/campus/reputation", timeout=30)
        if response.status_code == 403:
            self.log_result("Authentication Required", True, "Endpoint properly protected")
        else:
            self.log_result("Authentication Required", False, f"Expected 403, got {response.status_code}")
        
        # Test with authentication
        response = self.make_authenticated_request("campus/reputation")
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check response structure
                if isinstance(data, dict):
                    campus_leaderboard = data.get("campus_leaderboard", [])
                    user_campus = data.get("user_campus")
                    user_campus_stats = data.get("user_campus_stats")
                    recent_activities = data.get("recent_activities", [])
                    
                    self.log_result("Response Structure", True, f"Found {len(campus_leaderboard)} campuses, User campus: {user_campus}, Recent activities: {len(recent_activities)}")
                    
                    # Check campus data structure
                    if campus_leaderboard:
                        campus = campus_leaderboard[0]
                        required_fields = ["campus", "total_reputation_points"]
                        missing_fields = [field for field in required_fields if field not in campus]
                        
                        if not missing_fields:
                            self.log_result("Campus Data Structure", True, f"Top campus: {campus.get('campus', 'N/A')} ({campus.get('total_reputation_points', 0)} points)")
                        else:
                            self.log_result("Campus Data Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Campus Data", True, "No campus reputation data found (expected if none created)")
                    
                    # Print sample data
                    print(f"    Sample response: {json.dumps(data, indent=2)[:500]}...")
                    
                else:
                    self.log_result("Response Format", False, f"Expected dict, got {type(data)}")
                    
            except json.JSONDecodeError:
                self.log_result("JSON Response", False, "Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            self.log_result("API Call", False, f"Expected 200, got {status}")

    def run_tests(self):
        """Run all campus endpoint tests"""
        print("🚀 Campus Section API Testing")
        print("=" * 60)
        
        # Setup authentication
        if not self.register_and_login():
            print("❌ Failed to setup authentication. Cannot proceed with tests.")
            return False
        
        # Run tests
        self.test_inter_college_competitions()
        self.test_prize_challenges()
        self.test_campus_reputation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Failed tests details
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if passed_tests == total_tests else '⚠️  SOME TESTS FAILED'}")
        
        return passed_tests == total_tests

def main():
    tester = CampusEndpointTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
