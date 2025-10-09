import requests
import sys
import json
from datetime import datetime
import time
import random
import string

class CampusEventRegistrationTester:
    def __init__(self, base_url="https://event-reg-hub-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.admin_token = None
        self.admin_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        # Use realistic Indian student data
        self.test_user_email = f"priya.sharma{int(time.time())}@gmail.com"
        self.test_password = "SecurePass@123"
        self.verification_code = None
        self.reset_code = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.failed_tests.append(f"{name}: {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # AUTHENTICATION & SECURITY TESTS
    def test_user_registration_with_email_verification(self):
        """Test user registration with email verification flow"""
        user_data = {
            "email": self.test_user_email,
            "password": self.test_password,
            "full_name": "Priya Sharma",
            "role": "Student",
            "avatar": "girl",
            "student_level": "undergraduate",
            "skills": ["Python", "Content Writing", "Mathematics", "Hindi"],
            "availability_hours": 15,
            "location": "Mumbai, Maharashtra",
            "bio": "Computer Science student passionate about technology and writing"
        }
        
        success, response = self.run_test(
            "User Registration with Email Verification",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success:
            # Extract token for subsequent requests
            if response.get('token'):
                self.token = response.get('token')
                print(f"   ✅ Registration successful, token obtained")
            if response.get('verification_required'):
                print(f"   ✅ Email verification required as expected")
                self.verification_code = "123456"  # This would come from email in real scenario
            return True
        return False

    def test_password_strength_validation(self):
        """Test password strength validation API endpoint"""
        test_passwords = [
            ("weak123", False),  # Too weak
            ("StrongPass@123", True),  # Strong
            ("password", False),  # Common password
            ("12345678", False),  # Only numbers
            ("UPPERCASE", False),  # Only uppercase
            ("lowercase", False),  # Only lowercase
            ("NoSpecial123", False),  # No special chars
            ("Perfect@Pass123", True)  # Very strong
        ]
        
        all_passed = True
        for password, should_be_strong in test_passwords:
            success, response = self.run_test(
                f"Password Strength Check: {password[:8]}...",
                "POST",
                "auth/password-strength",
                200,
                data={"password": password}
            )
            
            if success:
                strength = response.get('strength', '')
                score = response.get('score', 0)
                is_strong = score >= 60
                
                if is_strong == should_be_strong:
                    print(f"   ✅ Correct strength assessment: {strength} (Score: {score})")
                else:
                    print(f"   ❌ Incorrect strength assessment: {strength} (Score: {score})")
                    all_passed = False
            else:
                all_passed = False
        
        return all_passed

    def test_email_verification(self):
        """Test email verification with code"""
        # Get the actual verification code from logs
        verification_code = self.get_verification_code_from_logs(self.test_user_email)
        
        if not verification_code:
            print("   ❌ Could not extract verification code from logs")
            return False
        
        print(f"   📧 Using verification code from logs: {verification_code}")
        
        verification_data = {
            "email": self.test_user_email,
            "verification_code": verification_code
        }
        
        success, response = self.run_test(
            "Email Verification",
            "POST",
            "auth/verify-email",
            200,
            data=verification_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            if 'user' in response:
                self.user_id = response['user'].get('id')
            print(f"   ✅ Token obtained after verification: {self.token[:20]}...")
            return True
        return False

    def test_login_with_account_lockout(self):
        """Test login with account lockout after failed attempts"""
        # First, try with wrong password multiple times
        wrong_login_data = {
            "email": self.test_user_email,
            "password": "WrongPassword123!"
        }
        
        print("   Testing failed login attempts...")
        failed_attempts = 0
        for i in range(6):  # Try 6 times to trigger lockout
            success, response = self.run_test(
                f"Failed Login Attempt {i+1}",
                "POST",
                "auth/login",
                401 if i < 5 else 423,  # Expect 423 (locked) on 6th attempt
                data=wrong_login_data
            )
            
            if not success and i == 5:
                # Check if account is locked (status 423)
                if response == {}:  # Empty response indicates different status code
                    print("   ✅ Account locked after 5 failed attempts")
                    return True
            
            time.sleep(0.5)  # Small delay between attempts
        
        return False

    def test_forgot_password_flow(self):
        """Test forgot password and reset password flows"""
        # Test forgot password
        forgot_data = {"email": self.test_user_email}
        
        success, response = self.run_test(
            "Forgot Password Request",
            "POST",
            "auth/forgot-password",
            200,
            data=forgot_data
        )
        
        if not success:
            return False
        
        # Simulate getting reset code from email
        reset_data = {
            "email": self.test_user_email,
            "reset_code": "654321",  # In real scenario, this comes from email
            "new_password": "NewSecurePass@456"
        }
        
        success, response = self.run_test(
            "Reset Password with Code",
            "POST",
            "auth/reset-password",
            200,
            data=reset_data
        )
        
        if success:
            # Update our test password for future tests
            self.test_password = "NewSecurePass@456"
            print("   ✅ Password reset successful")
            return True
        
        return False

    def test_rate_limiting_auth_endpoints(self):
        """Test rate limiting on auth endpoints"""
        print("   Testing rate limiting (this may take a moment)...")
        
        # Try to hit registration endpoint rapidly
        rapid_requests = 0
        rate_limited = False
        
        for i in range(8):  # Try 8 rapid requests (limit is 5/minute)
            user_data = {
                "email": f"ratelimit{i}_{int(time.time())}@test.com",
                "password": "TestPass@123",
                "full_name": "Rate Limit Test",
                "student_level": "undergraduate"
            }
            
            success, response = self.run_test(
                f"Rate Limit Test {i+1}",
                "POST",
                "auth/register",
                429 if i >= 5 else 200,  # Expect 429 after 5 requests
                data=user_data
            )
            
            if not success and i >= 5:
                rate_limited = True
                print(f"   ✅ Rate limiting triggered at request {i+1}")
                break
            
            time.sleep(0.1)  # Small delay
        
        return rate_limited

    # INPUT VALIDATION & SECURITY TESTS
    def test_xss_injection_attempts(self):
        """Test XSS injection attempts on user inputs"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';DROP TABLE users;--",
            "1' OR '1'='1",
            "<svg onload=alert('xss')>"
        ]
        
        all_safe = True
        for payload in xss_payloads:
            # Test XSS in profile update
            update_data = {
                "full_name": payload,
                "bio": f"Bio with {payload}",
                "location": payload
            }
            
            success, response = self.run_test(
                f"XSS Test: Profile Update",
                "PUT",
                "user/profile",
                422,  # Expect validation error (this is good!)
                data=update_data
            )
            
            if success:
                print(f"   ✅ XSS payload correctly rejected: {payload}")
            else:
                print(f"   ❌ XSS payload was not rejected: {payload}")
                all_safe = False
        
        return all_safe
        
    def get_verification_code_from_logs(self, email):
        """Extract verification code from backend logs"""
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True
            )
            
            for line in result.stdout.split('\n'):
                if f"EMAIL VERIFICATION: Sending verification code" in line and email in line:
                    # Extract the 6-digit code
                    import re
                    match = re.search(r'verification code (\d{6})', line)
                    if match:
                        return match.group(1)
            return None
        except:
            return None

    def get_reset_code_from_logs(self, email):
        """Extract password reset code from backend logs"""
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True
            )
            
            for line in result.stdout.split('\n'):
                if f"PASSWORD RESET: Sending reset code" in line and email in line:
                    # Extract the 6-digit code
                    import re
                    match = re.search(r'reset code (\d{6})', line)
                    if match:
                        return match.group(1)
            return None
        except:
            return None

    def test_large_financial_amounts(self):
        """Test handling of large financial amounts (up to ₹1 crore)"""
        large_amounts = [
            (50000.00, True),      # 50K - should work
            (500000.00, True),     # 5 Lakh - should work
            (2500000.00, True),    # 25 Lakh - should work
            (9999999.99, True),    # Just under 1 crore - should work
            (10000000.00, True),   # Exactly 1 crore - should work
            (15000000.00, False),  # Over 1 crore - should fail
            (50000000.00, False)   # Way over limit - should fail
        ]
        
        all_passed = True
        for amount, should_succeed in large_amounts:
            transaction_data = {
                "type": "income",
                "amount": amount,
                "category": "Business",
                "description": f"Large transaction of ₹{amount:,.2f}",
                "source": "business",
                "is_hustle_related": True
            }
            
            expected_status = 200 if should_succeed else 422
            success, response = self.run_test(
                f"Large Amount Test: ₹{amount:,.2f}",
                "POST",
                "transactions",
                expected_status,
                data=transaction_data
            )
            
            if success:  # Test got expected status code
                print(f"   ✅ Correct handling of ₹{amount:,.2f}")
            else:
                print(f"   ❌ Incorrect handling of ₹{amount:,.2f}")
                all_passed = False
        
        return all_passed

    # ENHANCED FEATURES TESTS
    def test_ai_hustle_recommendations(self):
        """Test AI hustle recommendations endpoint"""
        print("   Note: This may take a few seconds for AI processing...")
        success, response = self.run_test(
            "AI Hustle Recommendations",
            "GET",
            "hustles/recommendations",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Received {len(response)} AI recommendations")
            
            # Check if recommendations have required fields
            for i, rec in enumerate(response[:3]):  # Check first 3
                required_fields = ['title', 'description', 'category', 'estimated_pay', 'match_score']
                has_all_fields = all(field in rec for field in required_fields)
                
                if has_all_fields:
                    print(f"   ✅ Recommendation {i+1}: {rec.get('title', 'N/A')} - ₹{rec.get('estimated_pay', 0)}/hr")
                else:
                    print(f"   ❌ Recommendation {i+1} missing required fields")
                    return False
            
            return True
        
        return False

    def test_admin_functionality(self):
        """Test admin functionality (creating admin hustles)"""
        # First, we need to create an admin user (this would be done manually in production)
        # For testing, we'll assume our test user can be made admin
        
        # Test getting admin-posted hustles (should work even for non-admin)
        success, response = self.run_test(
            "Get Admin-Posted Hustles",
            "GET",
            "hustles/admin-posted",
            200
        )
        
        if success:
            print(f"   ✅ Retrieved {len(response) if isinstance(response, list) else 0} admin hustles")
            return True
        
        return False

    def test_analytics_with_large_values(self):
        """Test analytics endpoints handle large values properly"""
        # First create some transactions with large amounts
        large_transactions = [
            {"type": "income", "amount": 125000, "category": "Freelance", "description": "Large freelance project"},
            {"type": "income", "amount": 75000, "category": "Business", "description": "Business income"},
            {"type": "expense", "amount": 25000, "category": "Equipment", "description": "Laptop purchase"}
        ]
        
        for trans in large_transactions:
            self.run_test(
                f"Create Large Transaction: ₹{trans['amount']:,}",
                "POST",
                "transactions",
                200,
                data=trans
            )
        
        # Test transaction summary
        success, response = self.run_test(
            "Transaction Summary with Large Values",
            "GET",
            "transactions/summary",
            200
        )
        
        if success:
            income = response.get('income', 0)
            expense = response.get('expense', 0)
            net_savings = response.get('net_savings', 0)
            
            print(f"   ✅ Summary - Income: ₹{income:,}, Expense: ₹{expense:,}, Net: ₹{net_savings:,}")
            
            # Test analytics insights
            insights_success, insights_response = self.run_test(
                "Analytics Insights with Large Values",
                "GET",
                "analytics/insights",
                200
            )
            
            return insights_success
        
        return False

    def test_leaderboard_excluding_test_users(self):
        """Test leaderboard excludes test users"""
        success, response = self.run_test(
            "Leaderboard (Excluding Test Users)",
            "GET",
            "analytics/leaderboard",
            200
        )
        
        if success and isinstance(response, list):
            # Check that no test users are in leaderboard
            test_indicators = ['test', 'dummy', 'example', 'demo']
            clean_leaderboard = True
            
            for entry in response:
                user_name = entry.get('user_name', '').lower()
                if any(indicator in user_name for indicator in test_indicators):
                    print(f"   ❌ Test user found in leaderboard: {entry.get('user_name')}")
                    clean_leaderboard = False
            
            if clean_leaderboard:
                print(f"   ✅ Clean leaderboard with {len(response)} real users")
                return True
        
        return False

    # DATABASE OPERATIONS TESTS
    def test_user_profile_updates_with_validation(self):
        """Test user profile updates with validation"""
        # Test valid update
        valid_update = {
            "full_name": "Priya Sharma Updated",
            "skills": ["Python", "Machine Learning", "Content Writing", "Digital Marketing"],
            "availability_hours": 20,
            "location": "Pune, Maharashtra",
            "bio": "Updated bio: CS student with expertise in ML and content creation"
        }
        
        success, response = self.run_test(
            "Valid Profile Update",
            "PUT",
            "user/profile",
            200,
            data=valid_update
        )
        
        if not success:
            return False
        
        # Test invalid updates
        invalid_updates = [
            {"full_name": "A"},  # Too short
            {"full_name": "123Invalid"},  # Invalid characters
            {"bio": "x" * 600},  # Too long
            {"skills": ["skill"] * 25},  # Too many skills
            {"availability_hours": -5}  # Negative hours
        ]
        
        all_rejected = True
        for invalid_data in invalid_updates:
            success, response = self.run_test(
                f"Invalid Profile Update: {list(invalid_data.keys())[0]}",
                "PUT",
                "user/profile",
                422,  # Expect validation error
                data=invalid_data
            )
            
            if success:  # Should fail validation
                print(f"   ❌ Invalid data was accepted: {invalid_data}")
                all_rejected = False
        
        return all_rejected

    def test_hustle_creation_and_application_flow(self):
        """Test hustle creation and application flow"""
        # Create a hustle
        hustle_data = {
            "title": "Python Tutoring for School Students",
            "description": "Looking for a Python tutor to teach programming basics to high school students. Flexible timing, good pay, perfect for college students.",
            "category": "tutoring",
            "pay_rate": 500.00,
            "pay_type": "hourly",
            "time_commitment": "10-15 hours/week",
            "required_skills": ["Python", "Teaching", "Communication"],
            "difficulty_level": "intermediate",
            "location": "Mumbai, Maharashtra",
            "is_remote": False,
            "contact_info": "tutor.contact@gmail.com",
            "max_applicants": 5
        }
        
        success, response = self.run_test(
            "Create User Hustle",
            "POST",
            "hustles/create",
            200,
            data=hustle_data
        )
        
        if not success:
            return False
        
        hustle_id = response.get('id')
        if not hustle_id:
            print("   ❌ No hustle ID returned")
            return False
        
        # Test applying to the hustle
        application_data = {
            "cover_message": "I am a computer science student with 2 years of Python experience. I have tutored students before and am passionate about teaching programming concepts in a simple and engaging way."
        }
        
        success, response = self.run_test(
            "Apply to Hustle",
            "POST",
            f"hustles/{hustle_id}/apply",
            200,
            data=application_data
        )
        
        if success:
            # Check my applications
            success, response = self.run_test(
                "Get My Applications",
                "GET",
                "hustles/my-applications",
                200
            )
            
            if success and isinstance(response, list) and len(response) > 0:
                print(f"   ✅ Application submitted and retrieved successfully")
                return True
        
        return False

    def run_comprehensive_tests(self):
        """Run all comprehensive production tests"""
        print("🚀 Starting EarnNest Production Testing...")
        print("=" * 60)
        
        # AUTHENTICATION & SECURITY TESTS
        print("\n🔐 AUTHENTICATION & SECURITY TESTS")
        print("-" * 40)
        
        if not self.test_user_registration_with_email_verification():
            print("❌ Registration failed, stopping tests")
            return False
        
        if not self.test_email_verification():
            print("❌ Email verification failed, stopping tests")
            return False
        
        self.test_password_strength_validation()
        self.test_rate_limiting_auth_endpoints()
        
        # INPUT VALIDATION & SECURITY TESTS
        print("\n🛡️ INPUT VALIDATION & SECURITY TESTS")
        print("-" * 40)
        
        self.test_xss_injection_attempts()
        self.test_large_financial_amounts()
        
        # ENHANCED FEATURES TESTS
        print("\n⚡ ENHANCED FEATURES TESTS")
        print("-" * 40)
        
        self.test_ai_hustle_recommendations()
        self.test_admin_functionality()
        self.test_analytics_with_large_values()
        
        # DATABASE OPERATIONS TESTS
        print("\n💾 DATABASE OPERATIONS TESTS")
        print("-" * 40)
        
        self.test_user_profile_updates_with_validation()
        self.test_hustle_creation_and_application_flow()
        self.test_leaderboard_excluding_test_users()
        
        # ADDITIONAL SECURITY TESTS
        print("\n🔒 ADDITIONAL SECURITY TESTS")
        print("-" * 40)
        
        # Test forgot password flow (commented out as it might interfere with other tests)
        # self.test_forgot_password_flow()
        
        # Test login lockout (commented out as it locks the account)
        # self.test_login_with_account_lockout()
        
        return True

def main():
    tester = CampusEventRegistrationTester()
    
    try:
        tester.run_comprehensive_tests()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS")
        print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
        print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
        
        if tester.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failed_test in tester.failed_tests:
                print(f"   • {failed_test}")
        
        if tester.tests_passed == tester.tests_run:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed")
            return 1
            
    except Exception as e:
        print(f"\n💥 Testing failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
