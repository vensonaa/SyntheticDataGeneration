#!/usr/bin/env python3
"""
Example: Generate synthetic e-commerce data with relationships
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SchemaDefinition, FieldDefinition, DataType
from src.synthetic_data_generator import SyntheticDataGenerator
import pandas as pd
import random


def create_product_schema() -> SchemaDefinition:
    """Create a schema for product data"""
    
    fields = [
        FieldDefinition(
            name="product_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=1000
        ),
        FieldDefinition(
            name="product_name",
            data_type=DataType.STRING,
            required=True,
            min_length=5,
            max_length=100
        ),
        FieldDefinition(
            name="category",
            data_type=DataType.STRING,
            required=True,
            choices=["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Beauty", "Toys"]
        ),
        FieldDefinition(
            name="price",
            data_type=DataType.FLOAT,
            required=True,
            min_value=1.0,
            max_value=1000.0
        ),
        FieldDefinition(
            name="stock_quantity",
            data_type=DataType.INTEGER,
            required=True,
            min_value=0,
            max_value=1000
        ),
        FieldDefinition(
            name="is_active",
            data_type=DataType.BOOLEAN,
            required=True
        ),
        FieldDefinition(
            name="created_date",
            data_type=DataType.DATE,
            required=True
        )
    ]
    
    return SchemaDefinition(
        name="product_data",
        description="Synthetic product data for e-commerce",
        fields=fields,
        record_count=50
    )


def create_customer_schema() -> SchemaDefinition:
    """Create a schema for customer data"""
    
    fields = [
        FieldDefinition(
            name="customer_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=2000
        ),
        FieldDefinition(
            name="first_name",
            data_type=DataType.NAME,
            required=True,
            min_length=2,
            max_length=50
        ),
        FieldDefinition(
            name="last_name",
            data_type=DataType.NAME,
            required=True,
            min_length=2,
            max_length=50
        ),
        FieldDefinition(
            name="email",
            data_type=DataType.EMAIL,
            required=True
        ),
        FieldDefinition(
            name="phone",
            data_type=DataType.PHONE,
            required=False
        ),
        FieldDefinition(
            name="address",
            data_type=DataType.ADDRESS,
            required=False
        ),
        FieldDefinition(
            name="registration_date",
            data_type=DataType.DATE,
            required=True
        ),
        FieldDefinition(
            name="customer_segment",
            data_type=DataType.STRING,
            required=True,
            choices=["Bronze", "Silver", "Gold", "Platinum"]
        ),
        FieldDefinition(
            name="is_active",
            data_type=DataType.BOOLEAN,
            required=True
        )
    ]
    
    return SchemaDefinition(
        name="customer_data",
        description="Synthetic customer data for e-commerce",
        fields=fields,
        record_count=100
    )


def create_order_schema() -> SchemaDefinition:
    """Create a schema for order data"""
    
    fields = [
        FieldDefinition(
            name="order_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=5000
        ),
        FieldDefinition(
            name="customer_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=2000
        ),
        FieldDefinition(
            name="order_date",
            data_type=DataType.DATE,
            required=True
        ),
        FieldDefinition(
            name="order_status",
            data_type=DataType.STRING,
            required=True,
            choices=["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
        ),
        FieldDefinition(
            name="total_amount",
            data_type=DataType.FLOAT,
            required=True,
            min_value=10.0,
            max_value=5000.0
        ),
        FieldDefinition(
            name="shipping_address",
            data_type=DataType.ADDRESS,
            required=True
        ),
        FieldDefinition(
            name="payment_method",
            data_type=DataType.STRING,
            required=True,
            choices=["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "Cash on Delivery"]
        )
    ]
    
    return SchemaDefinition(
        name="order_data",
        description="Synthetic order data for e-commerce",
        fields=fields,
        record_count=200
    )


def create_order_item_schema() -> SchemaDefinition:
    """Create a schema for order item data"""
    
    fields = [
        FieldDefinition(
            name="order_item_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=10000
        ),
        FieldDefinition(
            name="order_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=5000
        ),
        FieldDefinition(
            name="product_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=1000
        ),
        FieldDefinition(
            name="quantity",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=10
        ),
        FieldDefinition(
            name="unit_price",
            data_type=DataType.FLOAT,
            required=True,
            min_value=1.0,
            max_value=1000.0
        ),
        FieldDefinition(
            name="total_price",
            data_type=DataType.FLOAT,
            required=True,
            min_value=1.0,
            max_value=10000.0
        )
    ]
    
    return SchemaDefinition(
        name="order_item_data",
        description="Synthetic order item data for e-commerce",
        fields=fields,
        record_count=500
    )


def generate_related_data():
    """Generate related e-commerce data"""
    
    print("🛒 Starting E-commerce Data Generation")
    print("=" * 50)
    
    generator = SyntheticDataGenerator(graph_type="parallel")
    
    # Generate products
    print("📦 Generating product data...")
    product_schema = create_product_schema()
    product_results = generator.generate_data(product_schema)
    
    if "error" in product_results:
        print(f"❌ Product generation failed: {product_results['error']}")
        return
    
    products_df = pd.DataFrame([record["data"] for record in product_results["generated_records"]])
    
    # Generate customers
    print("👥 Generating customer data...")
    customer_schema = create_customer_schema()
    customer_results = generator.generate_data(customer_schema)
    
    if "error" in customer_results:
        print(f"❌ Customer generation failed: {customer_results['error']}")
        return
    
    customers_df = pd.DataFrame([record["data"] for record in customer_results["generated_records"]])
    
    # Generate orders
    print("📋 Generating order data...")
    order_schema = create_order_schema()
    order_results = generator.generate_data(order_schema)
    
    if "error" in order_results:
        print(f"❌ Order generation failed: {order_results['error']}")
        return
    
    orders_df = pd.DataFrame([record["data"] for record in order_results["generated_records"]])
    
    # Generate order items with relationships
    print("🛍️ Generating order item data...")
    order_item_schema = create_order_item_schema()
    order_item_results = generator.generate_data(order_item_schema)
    
    if "error" in order_item_results:
        print(f"❌ Order item generation failed: {order_item_results['error']}")
        return
    
    order_items_df = pd.DataFrame([record["data"] for record in order_item_results["generated_records"]])
    
    # Create relationships by ensuring referential integrity
    print("🔗 Creating relationships...")
    
    # Ensure order items reference valid orders and products
    valid_order_ids = set(orders_df['order_id'].tolist())
    valid_product_ids = set(products_df['product_id'].tolist())
    
    # Filter order items to only include valid references
    order_items_df = order_items_df[
        order_items_df['order_id'].isin(valid_order_ids) &
        order_items_df['product_id'].isin(valid_product_ids)
    ]
    
    # If no valid order items, create some manually
    if len(order_items_df) == 0:
        print("⚠️ No valid order items found, creating sample relationships...")
        order_items_list = []
        order_item_id = 1
        
        for order_id in list(valid_order_ids)[:50]:  # Create items for first 50 orders
            num_items = random.randint(1, 3)  # 1-3 items per order
            for _ in range(num_items):
                product_id = random.choice(list(valid_product_ids))
                quantity = random.randint(1, 5)
                unit_price = products_df[products_df['product_id'] == product_id]['price'].iloc[0]
                total_price = quantity * unit_price
                
                order_items_list.append({
                    'order_item_id': order_item_id,
                    'order_id': order_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
                order_item_id += 1
        
        order_items_df = pd.DataFrame(order_items_list)
    
    # Calculate total price for order items
    order_items_df['total_price'] = order_items_df['quantity'] * order_items_df['unit_price']
    
    # Update order totals based on order items
    order_totals = order_items_df.groupby('order_id')['total_price'].sum().reset_index()
    order_totals.columns = ['order_id', 'calculated_total']
    
    # Merge with orders and update total_amount
    orders_df = orders_df.merge(order_totals, on='order_id', how='left')
    orders_df['total_amount'] = orders_df['calculated_total'].fillna(orders_df['total_amount'])
    orders_df = orders_df.drop('calculated_total', axis=1)
    
    # Save all data
    print("💾 Saving data to files...")
    products_df.to_csv("generated_products.csv", index=False)
    customers_df.to_csv("generated_customers.csv", index=False)
    orders_df.to_csv("generated_orders.csv", index=False)
    order_items_df.to_csv("generated_order_items.csv", index=False)
    
    # Generate summary report
    print("\n📊 E-commerce Data Summary:")
    print(f"   - Products: {len(products_df)}")
    print(f"   - Customers: {len(customers_df)}")
    print(f"   - Orders: {len(orders_df)}")
    print(f"   - Order Items: {len(order_items_df)}")
    
    # Show sample data
    print(f"\n📄 Sample Products:")
    print(products_df.head(3).to_string(index=False))
    
    print(f"\n📄 Sample Orders:")
    print(orders_df.head(3).to_string(index=False))
    
    print(f"\n📄 Sample Order Items:")
    print(order_items_df.head(5).to_string(index=False))
    
    # Calculate some business metrics
    print(f"\n📈 Business Metrics:")
    total_revenue = orders_df['total_amount'].sum()
    avg_order_value = orders_df['total_amount'].mean()
    total_orders = len(orders_df)
    
    print(f"   - Total Revenue: ${total_revenue:,.2f}")
    print(f"   - Average Order Value: ${avg_order_value:.2f}")
    print(f"   - Total Orders: {total_orders}")
    
    print("\n🎉 E-commerce data generation completed successfully!")


if __name__ == "__main__":
    generate_related_data()
