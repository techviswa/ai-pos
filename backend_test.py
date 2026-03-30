import requests
import sys
import json
from datetime import datetime

class POSAPITester:
    def __init__(self, base_url="https://cashflow-lite-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.owner_token = None
        self.cashier_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def run_test(self, name, method, endpoint, expected_status, data=None, cookies=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=test_headers, cookies=cookies)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers, cookies=cookies)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers, cookies=cookies)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers, cookies=cookies)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_owner_login(self):
        """Test owner login and store cookies"""
        print("\n=== TESTING OWNER AUTHENTICATION ===")
        success, response = self.run_test(
            "Owner Login",
            "POST",
            "auth/login",
            200,
            data={"email": "owner@pos.com", "password": "admin123"}
        )
        if success:
            print(f"   Owner logged in: {response.get('name')} ({response.get('role')})")
            return True
        return False

    def test_owner_me(self):
        """Test getting current owner user info"""
        success, response = self.run_test(
            "Owner /auth/me",
            "GET",
            "auth/me",
            200
        )
        if success and response.get('role') == 'Owner':
            print(f"   Owner verified: {response.get('email')}")
            return True
        return False

    def test_dashboard_stats(self):
        """Test dashboard stats (owner only)"""
        print("\n=== TESTING DASHBOARD ===")
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        if success:
            print(f"   Stats: Sales Today: ₹{response.get('total_sales_today', 0)}, Bills: {response.get('bills_count_today', 0)}")
            return True
        return False

    def test_products_crud(self):
        """Test products CRUD operations"""
        print("\n=== TESTING PRODUCTS MANAGEMENT ===")
        
        # Get initial products
        success, products = self.run_test("Get Products", "GET", "products", 200)
        if not success:
            return False
        
        initial_count = len(products)
        print(f"   Initial products count: {initial_count}")
        
        # Create a test product
        test_product = {
            "name": "Test Product",
            "price": 99.99,
            "stock": 50,
            "category": "Test Category"
        }
        
        success, created_product = self.run_test(
            "Create Product", "POST", "products", 200, data=test_product
        )
        if not success:
            return False
        
        product_id = created_product.get('id')
        print(f"   Created product ID: {product_id}")
        
        # Update the product
        update_data = {"name": "Updated Test Product", "price": 149.99}
        success, updated_product = self.run_test(
            "Update Product", "PUT", f"products/{product_id}", 200, data=update_data
        )
        if not success:
            return False
        
        # Verify products list increased
        success, products_after = self.run_test("Get Products After Create", "GET", "products", 200)
        if success and len(products_after) == initial_count + 1:
            print(f"   Products count increased to: {len(products_after)}")
        
        # Delete the test product
        success, _ = self.run_test(
            "Delete Product", "DELETE", f"products/{product_id}", 200
        )
        if not success:
            return False
        
        # Verify products list back to original
        success, products_final = self.run_test("Get Products After Delete", "GET", "products", 200)
        if success and len(products_final) == initial_count:
            print(f"   Products count back to: {len(products_final)}")
            return True
        
        return False

    def test_billing_flow(self):
        """Test billing flow"""
        print("\n=== TESTING BILLING FLOW ===")
        
        # First ensure we have at least one product
        success, products = self.run_test("Get Products for Billing", "GET", "products", 200)
        if not success or len(products) == 0:
            # Create a test product for billing
            test_product = {
                "name": "Billing Test Product",
                "price": 25.50,
                "stock": 100,
                "category": "Test"
            }
            success, created_product = self.run_test(
                "Create Product for Billing", "POST", "products", 200, data=test_product
            )
            if not success:
                return False
            products = [created_product]
        
        # Create a test bill
        product = products[0]
        bill_data = {
            "items": [
                {
                    "id": product["id"],
                    "name": product["name"],
                    "quantity": 2,
                    "price": product["price"]
                }
            ],
            "total": product["price"] * 2,
            "payment_type": "Cash"
        }
        
        success, created_bill = self.run_test(
            "Create Bill", "POST", "bills", 200, data=bill_data
        )
        if not success:
            return False
        
        bill_id = created_bill.get('id')
        print(f"   Created bill ID: {bill_id}")
        
        # Get bills list
        success, bills = self.run_test("Get Bills", "GET", "bills", 200)
        if not success:
            return False
        
        print(f"   Total bills: {len(bills)}")
        
        # Get specific bill details
        success, bill_details = self.run_test(
            "Get Bill Details", "GET", f"bills/{bill_id}", 200
        )
        if success:
            print(f"   Bill total: ₹{bill_details.get('total')}, Payment: {bill_details.get('payment_type')}")
            return True
        
        return False

    def test_staff_management(self):
        """Test staff management"""
        print("\n=== TESTING STAFF MANAGEMENT ===")
        
        # Get initial staff
        success, staff = self.run_test("Get Staff", "GET", "staff", 200)
        if not success:
            return False
        
        initial_count = len(staff)
        print(f"   Initial staff count: {initial_count}")
        
        # Create a test cashier
        timestamp = datetime.now().strftime("%H%M%S")
        test_staff = {
            "name": f"Test Cashier {timestamp}",
            "email": f"cashier{timestamp}@test.com",
            "password": "testpass123",
            "phone": "1234567890"
        }
        
        success, created_staff = self.run_test(
            "Create Staff", "POST", "staff", 200, data=test_staff
        )
        if not success:
            return False
        
        print(f"   Created staff: {created_staff.get('name')} ({created_staff.get('email')})")
        
        # Verify staff list increased
        success, staff_after = self.run_test("Get Staff After Create", "GET", "staff", 200)
        if success and len(staff_after) == initial_count + 1:
            print(f"   Staff count increased to: {len(staff_after)}")
            return True
        
        return False

    def test_cashier_login_and_access(self):
        """Test cashier login and role-based access"""
        print("\n=== TESTING CASHIER AUTHENTICATION & ACCESS ===")
        
        # First create a cashier if none exists
        timestamp = datetime.now().strftime("%H%M%S")
        test_staff = {
            "name": f"Test Cashier {timestamp}",
            "email": f"cashier{timestamp}@test.com",
            "password": "testpass123",
            "phone": "1234567890"
        }
        
        success, created_staff = self.run_test(
            "Create Cashier for Login Test", "POST", "staff", 200, data=test_staff
        )
        if not success:
            return False
        
        # Create new session for cashier
        cashier_session = requests.Session()
        
        # Login as cashier
        success, response = self.run_test(
            "Cashier Login",
            "POST",
            "auth/login",
            200,
            data={"email": test_staff["email"], "password": test_staff["password"]}
        )
        if not success:
            return False
        
        print(f"   Cashier logged in: {response.get('name')} ({response.get('role')})")
        
        # Test cashier can access billing endpoints
        success, products = self.run_test("Cashier Get Products", "GET", "products", 200)
        if not success:
            return False
        
        # Test cashier cannot access owner-only endpoints
        success, _ = self.run_test("Cashier Dashboard Access (Should Fail)", "GET", "dashboard/stats", 403)
        if success:
            print("   ✅ Cashier correctly denied dashboard access")
        
        success, _ = self.run_test("Cashier Staff Access (Should Fail)", "GET", "staff", 403)
        if success:
            print("   ✅ Cashier correctly denied staff access")
            return True
        
        return False

    def test_logout(self):
        """Test logout functionality"""
        print("\n=== TESTING LOGOUT ===")
        success, _ = self.run_test("Logout", "POST", "auth/logout", 200)
        if success:
            # Try to access protected endpoint after logout
            success, _ = self.run_test("Access After Logout (Should Fail)", "GET", "auth/me", 401)
            if success:
                print("   ✅ Logout successful - access denied after logout")
                return True
        return False

def main():
    print("🚀 Starting POS System API Testing...")
    print("=" * 50)
    
    tester = POSAPITester()
    
    # Test sequence
    tests = [
        tester.test_owner_login,
        tester.test_owner_me,
        tester.test_dashboard_stats,
        tester.test_products_crud,
        tester.test_billing_flow,
        tester.test_staff_management,
        tester.test_cashier_login_and_access,
        tester.test_logout
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            if not test():
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {str(e)}")
            failed_tests.append(test.__name__)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if failed_tests:
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print("✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())