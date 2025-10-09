#!/usr/bin/env python3

import requests
import json
import time

# Configuration
BACKEND_URL = "https://event-reg-hub-1.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN_EMAIL = "yash@earnaura.com"
SUPER_ADMIN_PASSWORD = "YaSh@4517"

class CampusFeaturesTest:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.tests_passed = 0
        self.tests_run = 0
        self.failed_tests = []

    def login_super_admin(self):
        """Login as super admin to get token"""
        print("🔐 Logging in as Super Admin...")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token") or data.get("token")
                self.user_id = data.get("user", {}).get("id")
                print(f"   ✅ Super admin logged in successfully")
                return True
            else:
                print(f"   ❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

    def test_endpoint(self, name, method, endpoint, expected_status=200, data=None):
        """Test an API endpoint"""
        print(f"\n🔍 Testing {name}...")
        self.tests_run += 1
        
        url = f"{BACKEND_URL}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            
            print(f"   URL: {url}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == expected_status:
                self.tests_passed += 1
                print(f"   ✅ PASSED")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        if 'events' in response_data:
                            print(f"   Events found: {len(response_data['events'])}")
                        elif 'competitions' in response_data:
                            print(f"   Competitions found: {len(response_data['competitions'])}")
                        elif 'challenges' in response_data:
                            print(f"   Challenges found: {len(response_data['challenges'])}")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Error: {response.json()}")
                except:
                    print(f"   Error: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.failed_tests.append(f"{name}: {str(e)}")
            print(f"   ❌ ERROR: {e}")
            return False, {}

    def test_college_events(self):
        """Test College Events endpoints"""
        print("\n" + "="*50)
        print("📅 TESTING COLLEGE EVENTS")
        print("="*50)
        
        # Test fetching college events
        self.test_endpoint("Get College Events", "GET", "college-events")
        
        # Test fetching a specific event (if any exist)
        success, data = self.test_endpoint("Get College Events List", "GET", "college-events")
        if success and data.get('events') and len(data['events']) > 0:
            event_id = data['events'][0]['id']
            self.test_endpoint(f"Get Event Details", "GET", f"college-events/{event_id}")

    def test_inter_college_competitions(self):
        """Test Inter-College Competitions endpoints"""
        print("\n" + "="*50)
        print("🏆 TESTING INTER-COLLEGE COMPETITIONS")
        print("="*50)
        
        # Test fetching competitions
        self.test_endpoint("Get Inter-College Competitions", "GET", "inter-college/competitions")

    def test_prize_challenges(self):
        """Test Prize Challenges endpoints"""
        print("\n" + "="*50)
        print("🎁 TESTING PRIZE CHALLENGES")
        print("="*50)
        
        # Test fetching challenges
        self.test_endpoint("Get Prize Challenges", "GET", "prize-challenges")

    def run_all_tests(self):
        """Run all campus features tests"""
        print("🚀 Starting Campus Features Testing...")
        print("="*60)
        
        # Login first
        if not self.login_super_admin():
            print("❌ Cannot proceed without authentication")
            return
        
        # Test all campus features
        self.test_college_events()
        self.test_inter_college_competitions()
        self.test_prize_challenges()
        
        # Print results
        print("\n" + "="*60)
        print("📊 FINAL RESULTS")
        print("="*60)
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   • {test}")
        else:
            print(f"\n🎉 All tests passed!")

if __name__ == "__main__":
    tester = CampusFeaturesTest()
    tester.run_all_tests()
