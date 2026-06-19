"""
Phase 1 & 2: AWS Configuration + DynamoDB Table Setup
HomeMade Pickles & Snacks Platform
"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Phase 1: AWS / boto3 Connection
# ─────────────────────────────────────────────

def get_dynamodb():
    """Returns a DynamoDB resource connected via boto3."""
    return boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'ap-south-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

def get_dynamodb_client():
    """Returns a low-level DynamoDB client."""
    return boto3.client(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'ap-south-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

# ─────────────────────────────────────────────
# Phase 2: DynamoDB Table Creation
# ─────────────────────────────────────────────

def create_tables():
    """Create all DynamoDB tables for the platform."""
    dynamodb = get_dynamodb()
    client = get_dynamodb_client()

    existing = client.list_tables()['TableNames']

    tables_config = [
        # Products Table
        {
            "TableName": os.getenv("PRODUCTS_TABLE", "PicklesProducts"),
            "KeySchema": [{"AttributeName": "ProductID", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "ProductID", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST"
        },
        # Users Table
        {
            "TableName": os.getenv("USERS_TABLE", "PicklesUsers"),
            "KeySchema": [{"AttributeName": "UserID", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "UserID", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST"
        },
        # Orders Table
        {
            "TableName": os.getenv("ORDERS_TABLE", "PicklesOrders"),
            "KeySchema": [
                {"AttributeName": "OrderID", "KeyType": "HASH"},
                {"AttributeName": "UserID", "KeyType": "RANGE"}
            ],
            "AttributeDefinitions": [
                {"AttributeName": "OrderID", "AttributeType": "S"},
                {"AttributeName": "UserID", "AttributeType": "S"}
            ],
            "BillingMode": "PAY_PER_REQUEST"
        },
        # Inventory Table
        {
            "TableName": os.getenv("INVENTORY_TABLE", "PicklesInventory"),
            "KeySchema": [{"AttributeName": "ProductID", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "ProductID", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST"
        },
        # Subscriptions Table
        {
            "TableName": os.getenv("SUBSCRIPTIONS_TABLE", "PicklesSubscriptions"),
            "KeySchema": [{"AttributeName": "UserID", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "UserID", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST"
        },
    ]

    for config in tables_config:
        if config["TableName"] in existing:
            print(f"[SKIP] Table already exists: {config['TableName']}")
            continue
        table = dynamodb.create_table(**config)
        table.wait_until_exists()
        print(f"[OK] Created table: {config['TableName']}")

    print("\n✅ All DynamoDB tables are ready!")


# ─────────────────────────────────────────────
# Seed Sample Products
# ─────────────────────────────────────────────

def seed_products():
    """Insert sample products into DynamoDB."""
    dynamodb = get_dynamodb()
    table = dynamodb.Table(os.getenv("PRODUCTS_TABLE", "PicklesProducts"))
    inv_table = dynamodb.Table(os.getenv("INVENTORY_TABLE", "PicklesInventory"))

    products = [
        {
            "ProductID": "P001",
            "Name": "Mango Pickle",
            "Category": "Pickles",
            "Price": "120",
            "Description": "Traditional sun-dried mango pickle with mustard oil.",
            "Image": "mango_pickle.jpg",
            "Tags": ["spicy", "traditional", "bestseller"],
            "Rating": "4.8"
        },
        {
            "ProductID": "P002",
            "Name": "Lemon Pickle",
            "Category": "Pickles",
            "Price": "90",
            "Description": "Tangy lemon pickle with aromatic spices.",
            "Image": "lemon_pickle.jpg",
            "Tags": ["tangy", "light"],
            "Rating": "4.5"
        },
        {
            "ProductID": "P003",
            "Name": "Garlic Pickle",
            "Category": "Pickles",
            "Price": "150",
            "Description": "Bold garlic pickle, perfect with dal-rice.",
            "Image": "garlic_pickle.jpg",
            "Tags": ["bold", "garlic", "spicy"],
            "Rating": "4.7"
        },
        {
            "ProductID": "P004",
            "Name": "Murukku",
            "Category": "Snacks",
            "Price": "60",
            "Description": "Crispy rice flour murukku, handmade with sesame seeds.",
            "Image": "murukku.jpg",
            "Tags": ["crunchy", "traditional"],
            "Rating": "4.6"
        },
        {
            "ProductID": "P005",
            "Name": "Mixture",
            "Category": "Snacks",
            "Price": "80",
            "Description": "South Indian spicy mixture with fried lentils.",
            "Image": "mixture.jpg",
            "Tags": ["spicy", "crunchy", "bestseller"],
            "Rating": "4.9"
        },
        {
            "ProductID": "P006",
            "Name": "Avakaya Pickle",
            "Category": "Pickles",
            "Price": "180",
            "Description": "Authentic Andhra-style raw mango pickle.",
            "Image": "avakaya.jpg",
            "Tags": ["andhra", "spicy", "traditional"],
            "Rating": "5.0"
        },
        {
            "ProductID": "P007",
            "Name": "Gongura Pickle",
            "Category": "Pickles",
            "Price": "130",
            "Description": "Famous Andhra sorrel leaves pickle, tangy and spicy.",
            "Image": "P007.jpg",
            "Tags": ["andhra", "tangy", "bestseller"],
            "Rating": "4.9"
        },
        {
            "ProductID": "P008",
            "Name": "Chakli",
            "Category": "Snacks",
            "Price": "70",
            "Description": "Crispy spiral snack made from rice and lentil flour.",
            "Image": "P008.jpg",
            "Tags": ["crunchy", "traditional"],
            "Rating": "4.5"
        },
    ]

    for product in products:
        table.put_item(Item=product)
        inv_table.put_item(Item={
            "ProductID": product["ProductID"],
            "Stock": 100,
            "LastUpdated": "2025-01-01"
        })
        print(f"[SEEDED] {product['Name']}")

    print("\n✅ Sample products seeded!")


if __name__ == "__main__":
    print("=== Setting up HomeMade Pickles & Snacks on AWS ===\n")
    create_tables()
    seed_products()
