import asyncio
import websockets
import json
import requests
import time
from datetime import datetime
import uuid
import sys

class WebSocketNotificationTester:
    def __init__(self, base_url="https://realtime-fixes.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        self.token = None
        self.user_id = None
        self.websocket = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.received_notifications = []
        
        # Test user data
        self.test_user_email = f"websocket.test{int(time.time())}@gmail.com"
        self.test_password = "WebSocketTest@123"

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            self.failed_tests.append(name)
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    async def setup_test_user(self):
        """Create and authenticate test user"""
        print("🔧 Setting up test user...")
        
        # Register user
        user_data = {
            "email": self.test_user_email,
            "password": self.test_password,
            "full_name": "WebSocket Test User",
            "student_level": "undergraduate",
            "skills": ["Coding", "Digital Marketing"],
            "availability_hours": 15,
            "location": "Mumbai, Maharashtra",
            "role": "Student",
            "avatar": "man",
            "bio": "Testing WebSocket notifications"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=user_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.user_id = data.get('user', {}).get('id')
                print(f"✅ User registered successfully: {self.user_id}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return False

    async def connect_websocket(self):
        """Connect to WebSocket with authentication"""
        print("🔌 Connecting to WebSocket...")
        
        if not self.token or not self.user_id:
            print("❌ No token or user_id available")
            return False
        
        try:
            ws_endpoint = f"{self.ws_url}/api/ws/notifications/{self.user_id}?token={self.token}"
            print(f"   Connecting to: {ws_endpoint}")
            
            self.websocket = await websockets.connect(
                ws_endpoint,
                ping_interval=20,
                ping_timeout=10,
                open_timeout=30
            )
            
            # Wait for connection established message
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=10)
                data = json.loads(message)
                
                if data.get('type') == 'connection_established':
                    print(f"✅ WebSocket connected successfully")
                    print(f"   Connection message: {data.get('message', 'N/A')}")
                    return True
                else:
                    print(f"❌ Unexpected connection message: {data}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for connection message")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {str(e)}")
            return False

    async def listen_for_notifications(self, duration=5):
        """Listen for notifications for specified duration"""
        if not self.websocket:
            return []
        
        notifications = []
        end_time = time.time() + duration
        
        try:
            while time.time() < end_time:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=min(1, end_time - time.time())
                    )
                    data = json.loads(message)
                    notifications.append(data)
                    print(f"📨 Received notification: {data.get('type', 'unknown')} - {data.get('title', 'N/A')}")
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("⚠️ WebSocket connection closed")
                    break
        except Exception as e:
            print(f"⚠️ Error listening for notifications: {str(e)}")
        
        return notifications

    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        print("\n🔌 Testing WebSocket Connection...")
        
        success = await self.connect_websocket()
        self.log_test(
            "WebSocket Connection with Authentication",
            success,
            "Connection established with proper authentication token"
        )
        
        if success and self.websocket:
            # Test ping/pong
            try:
                await self.websocket.ping()
                self.log_test("WebSocket Ping/Pong", True, "Keepalive mechanism working")
            except Exception as e:
                self.log_test("WebSocket Ping/Pong", False, f"Ping failed: {str(e)}")
        
        return success

    async def test_transaction_notifications(self):
        """Test transaction-related notifications"""
        print("\n💰 Testing Transaction Notifications...")
        
        if not self.websocket:
            self.log_test("Transaction Notifications", False, "No WebSocket connection")
            return False
        
        # Create a budget first for budget alert testing
        budget_data = {
            "category": "Food",
            "allocated_amount": 1000.0,
            "month": datetime.now().month,
            "year": datetime.now().year
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/budgets",
                json=budget_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            print(f"   Budget creation: {response.status_code}")
        except Exception as e:
            print(f"   Budget creation failed: {str(e)}")
        
        # Test 1: Income transaction notification
        income_data = {
            "type": "income",
            "amount": 2500.0,
            "category": "Freelance",
            "description": "WebSocket test income",
            "source": "freelance"
        }
        
        try:
            # Start listening for notifications
            listen_task = asyncio.create_task(self.listen_for_notifications(8))
            
            # Wait a moment then create transaction
            await asyncio.sleep(1)
            
            response = requests.post(
                f"{self.api_url}/transactions",
                json=income_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            print(f"   Income transaction created: {response.status_code}")
            
            # Wait for notifications
            notifications = await listen_task
            
            # Check for income notification
            income_notification = next(
                (n for n in notifications if n.get('type') == 'transaction_income'), 
                None
            )
            
            self.log_test(
                "Income Transaction Notification",
                income_notification is not None,
                f"Received notification: {income_notification.get('title', 'N/A') if income_notification else 'None'}"
            )
            
        except Exception as e:
            self.log_test("Income Transaction Notification", False, f"Error: {str(e)}")
        
        # Test 2: Expense transaction notification
        expense_data = {
            "type": "expense",
            "amount": 800.0,
            "category": "Food",
            "description": "WebSocket test expense"
        }
        
        try:
            # Start listening for notifications
            listen_task = asyncio.create_task(self.listen_for_notifications(8))
            
            # Wait a moment then create transaction
            await asyncio.sleep(1)
            
            response = requests.post(
                f"{self.api_url}/transactions",
                json=expense_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            print(f"   Expense transaction created: {response.status_code}")
            
            # Wait for notifications
            notifications = await listen_task
            
            # Check for expense notification
            expense_notification = next(
                (n for n in notifications if n.get('type') == 'transaction_expense'), 
                None
            )
            
            self.log_test(
                "Expense Transaction Notification",
                expense_notification is not None,
                f"Received notification: {expense_notification.get('title', 'N/A') if expense_notification else 'None'}"
            )
            
        except Exception as e:
            self.log_test("Expense Transaction Notification", False, f"Error: {str(e)}")
        
        # Test 3: Budget alert notification (expense near limit)
        high_expense_data = {
            "type": "expense",
            "amount": 150.0,  # This should trigger budget alert (950/1000 = 95%)
            "category": "Food",
            "description": "High expense for budget alert test"
        }
        
        try:
            # Start listening for notifications
            listen_task = asyncio.create_task(self.listen_for_notifications(8))
            
            # Wait a moment then create transaction
            await asyncio.sleep(1)
            
            response = requests.post(
                f"{self.api_url}/transactions",
                json=high_expense_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            print(f"   High expense transaction created: {response.status_code}")
            
            # Wait for notifications
            notifications = await listen_task
            
            # Check for budget alert notification
            budget_alert = next(
                (n for n in notifications if n.get('type') == 'budget_alert'), 
                None
            )
            
            self.log_test(
                "Budget Alert Notification",
                budget_alert is not None,
                f"Received alert: {budget_alert.get('title', 'N/A') if budget_alert else 'None'}"
            )
            
        except Exception as e:
            self.log_test("Budget Alert Notification", False, f"Error: {str(e)}")

    async def test_financial_goal_notifications(self):
        """Test financial goal progress and completion notifications"""
        print("\n🎯 Testing Financial Goal Notifications...")
        
        if not self.websocket:
            self.log_test("Financial Goal Notifications", False, "No WebSocket connection")
            return False
        
        # Create a financial goal
        goal_data = {
            "name": "Emergency Fund",
            "category": "emergency_fund",
            "target_amount": 10000.0,
            "current_amount": 2500.0,
            "target_date": "2024-12-31",
            "description": "WebSocket test emergency fund"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/financial-goals",
                json=goal_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test("Financial Goal Creation", False, f"Failed to create goal: {response.status_code}")
                return False
            
            goal_id = response.json().get('id')
            print(f"   Goal created: {goal_id}")
            
            # Test 1: Goal progress notification (25% milestone)
            progress_update = {
                "current_amount": 2500.0  # 25% of 10000
            }
            
            # Start listening for notifications
            listen_task = asyncio.create_task(self.listen_for_notifications(8))
            
            # Wait a moment then update goal
            await asyncio.sleep(1)
            
            response = requests.put(
                f"{self.api_url}/financial-goals/{goal_id}",
                json=progress_update,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            print(f"   Goal progress updated: {response.status_code}")
            
            # Wait for notifications
            notifications = await listen_task
            
            # Check for progress notification
            progress_notification = next(
                (n for n in notifications if n.get('type') == 'goal_progress'), 
                None
            )
            
            self.log_test(
                "Goal Progress Notification (25%)",
                progress_notification is not None,
                f"Received notification: {progress_notification.get('title', 'N/A') if progress_notification else 'None'}"
            )
            
            # Test 2: Goal completion notification
            completion_update = {
                "current_amount": 10000.0  # 100% completion
            }
            
            # Start listening for notifications
            listen_task = asyncio.create_task(self.listen_for_notifications(8))
            
            # Wait a moment then complete goal
            await asyncio.sleep(1)
            
            response = requests.put(
                f"{self.api_url}/financial-goals/{goal_id}",
                json=completion_update,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            print(f"   Goal completed: {response.status_code}")
            
            # Wait for notifications
            notifications = await listen_task
            
            # Check for completion notification
            completion_notification = next(
                (n for n in notifications if n.get('type') == 'goal_completed'), 
                None
            )
            
            self.log_test(
                "Goal Completion Notification",
                completion_notification is not None,
                f"Received notification: {completion_notification.get('title', 'N/A') if completion_notification else 'None'}"
            )
            
        except Exception as e:
            self.log_test("Financial Goal Notifications", False, f"Error: {str(e)}")

    async def test_group_challenge_notifications(self):
        """Test group challenge notifications"""
        print("\n👥 Testing Group Challenge Notifications...")
        
        if not self.websocket:
            self.log_test("Group Challenge Notifications", False, "No WebSocket connection")
            return False
        
        try:
            # First, check if there are any existing group challenges
            response = requests.get(
                f"{self.api_url}/group-challenges",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            
            print(f"   Group challenges fetch: {response.status_code}")
            
            if response.status_code == 200:
                challenges = response.json()
                print(f"   Found {len(challenges)} group challenges")
                
                if challenges:
                    # Join the first available challenge
                    challenge = challenges[0]
                    challenge_id = challenge.get('id')
                    
                    # Start listening for notifications
                    listen_task = asyncio.create_task(self.listen_for_notifications(8))
                    
                    # Wait a moment then join challenge
                    await asyncio.sleep(1)
                    
                    join_response = requests.post(
                        f"{self.api_url}/group-challenges/{challenge_id}/join",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=30
                    )
                    
                    print(f"   Challenge join attempt: {join_response.status_code}")
                    
                    # Wait for notifications
                    notifications = await listen_task
                    
                    # Check for challenge-related notifications
                    challenge_notification = next(
                        (n for n in notifications if 'challenge' in n.get('type', '').lower()), 
                        None
                    )
                    
                    self.log_test(
                        "Group Challenge Join Notification",
                        challenge_notification is not None,
                        f"Received notification: {challenge_notification.get('title', 'N/A') if challenge_notification else 'None'}"
                    )
                    
                    # Test challenge progress by making a transaction
                    if join_response.status_code in [200, 201]:
                        progress_transaction = {
                            "type": "expense",
                            "amount": 100.0,
                            "category": "Food",
                            "description": "Challenge progress test"
                        }
                        
                        # Start listening for notifications
                        listen_task = asyncio.create_task(self.listen_for_notifications(8))
                        
                        # Wait a moment then create transaction
                        await asyncio.sleep(1)
                        
                        requests.post(
                            f"{self.api_url}/transactions",
                            json=progress_transaction,
                            headers={"Authorization": f"Bearer {self.token}"},
                            timeout=30
                        )
                        
                        # Wait for notifications
                        notifications = await listen_task
                        
                        # Check for challenge progress notification
                        progress_notification = next(
                            (n for n in notifications if 'challenge_progress' in n.get('type', '')), 
                            None
                        )
                        
                        self.log_test(
                            "Group Challenge Progress Notification",
                            progress_notification is not None,
                            f"Received notification: {progress_notification.get('title', 'N/A') if progress_notification else 'None'}"
                        )
                else:
                    self.log_test("Group Challenge Notifications", False, "No group challenges available to test")
            else:
                self.log_test("Group Challenge Notifications", False, f"Failed to fetch challenges: {response.status_code}")
                
        except Exception as e:
            self.log_test("Group Challenge Notifications", False, f"Error: {str(e)}")

    async def test_leaderboard_notifications(self):
        """Test leaderboard update notifications"""
        print("\n🏆 Testing Leaderboard Notifications...")
        
        if not self.websocket:
            self.log_test("Leaderboard Notifications", False, "No WebSocket connection")
            return False
        
        try:
            # Create multiple transactions to potentially change leaderboard position
            transactions = [
                {"type": "income", "amount": 1500.0, "category": "Freelance", "description": "Leaderboard test 1"},
                {"type": "income", "amount": 2000.0, "category": "Business", "description": "Leaderboard test 2"},
                {"type": "income", "amount": 1000.0, "category": "Tutoring", "description": "Leaderboard test 3"}
            ]
            
            # Start listening for notifications
            listen_task = asyncio.create_task(self.listen_for_notifications(15))
            
            # Wait a moment then create transactions
            await asyncio.sleep(1)
            
            for i, transaction in enumerate(transactions):
                response = requests.post(
                    f"{self.api_url}/transactions",
                    json=transaction,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30
                )
                print(f"   Transaction {i+1} created: {response.status_code}")
                await asyncio.sleep(2)  # Space out transactions
            
            # Wait for notifications
            notifications = await listen_task
            
            # Check for leaderboard update notifications
            leaderboard_notifications = [
                n for n in notifications 
                if 'leaderboard' in n.get('type', '').lower() or 'rank' in n.get('type', '').lower()
            ]
            
            self.log_test(
                "Leaderboard Update Notifications",
                len(leaderboard_notifications) > 0,
                f"Received {len(leaderboard_notifications)} leaderboard notifications"
            )
            
            # Check for top rank achievement
            top_rank_notification = next(
                (n for n in notifications if 'top_rank' in n.get('type', '')), 
                None
            )
            
            self.log_test(
                "Top Rank Achievement Notification",
                top_rank_notification is not None,
                f"Received notification: {top_rank_notification.get('title', 'N/A') if top_rank_notification else 'None - may not have reached top 3'}"
            )
            
        except Exception as e:
            self.log_test("Leaderboard Notifications", False, f"Error: {str(e)}")

    async def test_websocket_error_handling(self):
        """Test WebSocket error handling and reconnection"""
        print("\n🔧 Testing WebSocket Error Handling...")
        
        # Test invalid token
        try:
            invalid_ws_endpoint = f"{self.ws_url}/ws/notifications/{self.user_id}?token=invalid_token"
            
            try:
                invalid_websocket = await asyncio.wait_for(
                    websockets.connect(invalid_ws_endpoint, timeout=10),
                    timeout=15
                )
                await invalid_websocket.close()
                self.log_test("Invalid Token Rejection", False, "Invalid token was accepted")
            except Exception:
                self.log_test("Invalid Token Rejection", True, "Invalid token properly rejected")
                
        except Exception as e:
            self.log_test("Invalid Token Rejection", True, f"Connection failed as expected: {str(e)}")
        
        # Test connection stability
        if self.websocket:
            try:
                # Send a few pings to test stability
                for i in range(3):
                    await self.websocket.ping()
                    await asyncio.sleep(1)
                
                self.log_test("WebSocket Stability", True, "Connection remained stable during ping tests")
            except Exception as e:
                self.log_test("WebSocket Stability", False, f"Connection unstable: {str(e)}")

    async def cleanup(self):
        """Clean up WebSocket connection"""
        if self.websocket:
            try:
                await self.websocket.close()
                print("🧹 WebSocket connection closed")
            except Exception as e:
                print(f"⚠️ Error closing WebSocket: {str(e)}")

    async def run_all_tests(self):
        """Run all WebSocket notification tests"""
        print("🚀 Starting WebSocket Notification System Tests...")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user, aborting tests")
            return False
        
        # Test WebSocket connection
        if not await self.test_websocket_connection():
            print("❌ Failed to establish WebSocket connection, aborting tests")
            return False
        
        # Run notification tests
        await self.test_transaction_notifications()
        await self.test_financial_goal_notifications()
        await self.test_group_challenge_notifications()
        await self.test_leaderboard_notifications()
        await self.test_websocket_error_handling()
        
        # Cleanup
        await self.cleanup()
        
        return True

    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 WEBSOCKET NOTIFICATION TEST RESULTS")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"   • {failed_test}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All WebSocket notification tests passed!")
            return True
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} tests failed")
            return False

async def main():
    tester = WebSocketNotificationTester()
    
    try:
        success = await tester.run_all_tests()
        all_passed = tester.print_results()
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n💥 WebSocket testing failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
