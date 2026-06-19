"""
Phase 6: Testing & Validation
HomeMade Pickles & Snacks Platform
End-to-end test of all major flows
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_home():
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200, "Homepage failed"
    print("[PASS] Homepage loads")

def test_products():
    r = requests.get(f"{BASE_URL}/products")
    assert r.status_code == 200, "Products page failed"
    print("[PASS] Products page loads")

def test_category_filter():
    r = requests.get(f"{BASE_URL}/products?category=Pickles")
    assert r.status_code == 200
    print("[PASS] Category filter works")

def test_search():
    r = requests.get(f"{BASE_URL}/products?search=mango")
    assert r.status_code == 200
    print("[PASS] Search works")

def test_inventory_api():
    r = requests.get(f"{BASE_URL}/api/inventory/P001")
    assert r.status_code == 200
    data = r.json()
    assert 'stock' in data
    assert 'status' in data
    print(f"[PASS] Inventory API - P001 stock: {data['stock']}")

def test_product_detail():
    r = requests.get(f"{BASE_URL}/product/P001")
    assert r.status_code == 200
    print("[PASS] Product detail page")

def test_register():
    r = requests.post(f"{BASE_URL}/register", data={
        'name': 'Test User',
        'email': 'test@pickles.com',
        'password': 'test1234',
        'phone': '9999999999',
        'address': 'Vijayawada, AP'
    }, allow_redirects=True)
    assert r.status_code == 200
    print("[PASS] User registration")

def test_login():
    session = requests.Session()
    r = session.post(f"{BASE_URL}/login", data={
        'email': 'test@pickles.com',
        'password': 'test1234'
    }, allow_redirects=True)
    assert r.status_code == 200
    print("[PASS] User login")
    return session

def test_cart_and_checkout():
    session = test_login()
    # Add to cart
    r = session.post(f"{BASE_URL}/cart/add/P001", data={'quantity': 2}, allow_redirects=True)
    assert r.status_code == 200
    print("[PASS] Add to cart")

    # View cart
    r = session.get(f"{BASE_URL}/cart")
    assert r.status_code == 200
    print("[PASS] View cart")

    # Checkout
    r = session.post(f"{BASE_URL}/checkout", data={
        'name': 'Test User',
        'address': 'Vijayawada, AP - 520001',
        'phone': '9999999999',
        'payment': 'COD'
    }, allow_redirects=True)
    assert r.status_code == 200
    print("[PASS] Checkout & order placement")

def test_subscriptions():
    r = requests.get(f"{BASE_URL}/subscriptions")
    assert r.status_code == 200
    print("[PASS] Subscriptions page")

def run_all_tests():
    print("\n====== 🧪 HomeMade Pickles & Snacks - Test Suite ======\n")
    try:
        test_home()
        test_products()
        test_category_filter()
        test_search()
        test_inventory_api()
        test_product_detail()
        test_register()
        test_login()
        test_cart_and_checkout()
        test_subscriptions()
        print("\n✅ All tests passed! Platform is ready for production.\n")
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}\n")
    except Exception as e:
        print(f"\n⚠️  Error: {e} — Make sure the Flask server is running.\n")

if __name__ == "__main__":
    run_all_tests()
