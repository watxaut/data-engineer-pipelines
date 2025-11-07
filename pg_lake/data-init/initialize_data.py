#!/usr/bin/env python3
"""
Initialize fake data for the reverse ETL pipeline:
- 1000 orders
- 5000 bought_products with 0-3 customizations each
"""

import time
import random
from datetime import datetime, timedelta
from trino.dbapi import connect
from trino.auth import BasicAuthentication

def wait_for_trino(host, port, max_retries=30):
    """Wait for Trino to be ready"""
    print(f"Waiting for Trino at {host}:{port}...")
    for i in range(max_retries):
        try:
            conn = connect(
                host=host,
                port=port,
                user='admin',
                catalog='iceberg',
                schema='default'
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            cursor.close()
            conn.close()
            print("Trino is ready!")
            return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries}: Trino not ready yet... ({e})")
            time.sleep(10)
    raise Exception("Trino did not become ready in time")

def create_iceberg_tables(conn):
    """Create Iceberg tables for orders and bought_products"""
    cursor = conn.cursor()
    
    print("Creating Iceberg schema...")
    try:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS iceberg.raw WITH (location = 's3://warehouse/raw')")
    except Exception as e:
        print(f"Schema creation note: {e}")
    
    print("Dropping existing tables if any...")
    try:
        cursor.execute("DROP TABLE IF EXISTS iceberg.raw.orders")
    except Exception as e:
        print(f"Drop orders table note: {e}")
    
    try:
        cursor.execute("DROP TABLE IF EXISTS iceberg.raw.bought_products")
    except Exception as e:
        print(f"Drop bought_products table note: {e}")
    
    print("Creating orders table...")
    cursor.execute("""
        CREATE TABLE iceberg.raw.orders (
            order_id BIGINT,
            customer_id BIGINT,
            order_date TIMESTAMP,
            order_status VARCHAR
        )
        WITH (
            format = 'PARQUET',
            location = 's3://warehouse/raw/orders'
        )
    """)
    
    print("Creating bought_products table...")
    cursor.execute("""
        CREATE TABLE iceberg.raw.bought_products (
            bought_product_id BIGINT,
            product_id BIGINT,
            product_customizations ARRAY(INTEGER),
            order_id BIGINT
        )
        WITH (
            format = 'PARQUET',
            location = 's3://warehouse/raw/bought_products'
        )
    """)
    
    cursor.close()
    print("Tables created successfully!")

def generate_fake_data(conn):
    """Generate and insert fake data"""
    cursor = conn.cursor()
    
    # Generate orders data (1000 orders)
    print("Generating 1000 orders...")
    orders_data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for order_id in range(1, 1001):
        customer_id = random.randint(1, 200)  # 200 unique customers
        order_date = base_date + timedelta(days=random.randint(0, 365))
        order_status = random.choice(['completed', 'processing', 'shipped', 'delivered'])
        orders_data.append((order_id, customer_id, order_date, order_status))
    
    # Insert orders in batches
    batch_size = 100
    for i in range(0, len(orders_data), batch_size):
        batch = orders_data[i:i+batch_size]
        values = ', '.join([
            f"({order_id}, {customer_id}, TIMESTAMP '{order_date.strftime('%Y-%m-%d %H:%M:%S')}', '{order_status}')"
            for order_id, customer_id, order_date, order_status in batch
        ])
        cursor.execute(f"INSERT INTO iceberg.raw.orders VALUES {values}")
    
    print("Orders inserted successfully!")
    
    # Generate bought_products data (5000 products)
    print("Generating 5000 bought_products...")
    bought_products_data = []
    
    for bought_product_id in range(1, 5001):
        product_id = random.randint(1, 50)  # 50 unique products
        order_id = random.randint(1, 1000)  # Link to orders
        
        # Generate 0-3 customizations
        num_customizations = random.randint(0, 3)
        customizations = [random.randint(1, 20) for _ in range(num_customizations)]
        
        bought_products_data.append((bought_product_id, product_id, customizations, order_id))
    
    # Insert bought_products in batches
    for i in range(0, len(bought_products_data), batch_size):
        batch = bought_products_data[i:i+batch_size]
        values = ', '.join([
            f"({bought_product_id}, {product_id}, ARRAY{customizations}, {order_id})"
            for bought_product_id, product_id, customizations, order_id in batch
        ])
        cursor.execute(f"INSERT INTO iceberg.raw.bought_products VALUES {values}")
    
    print("Bought products inserted successfully!")
    cursor.close()

def verify_data(conn):
    """Verify the inserted data"""
    cursor = conn.cursor()
    
    print("\nVerifying data...")
    cursor.execute("SELECT COUNT(*) FROM iceberg.raw.orders")
    orders_count = cursor.fetchone()[0]
    print(f"Orders count: {orders_count}")
    
    cursor.execute("SELECT COUNT(*) FROM iceberg.raw.bought_products")
    products_count = cursor.fetchone()[0]
    print(f"Bought products count: {products_count}")
    
    cursor.execute("SELECT * FROM iceberg.raw.orders LIMIT 5")
    print("\nSample orders:")
    for row in cursor.fetchall():
        print(row)
    
    cursor.execute("SELECT * FROM iceberg.raw.bought_products LIMIT 5")
    print("\nSample bought products:")
    for row in cursor.fetchall():
        print(row)
    
    cursor.close()

def main():
    trino_host = 'trino'
    trino_port = 8080
    
    # Wait for Trino to be ready
    wait_for_trino(trino_host, trino_port)
    
    # Connect to Trino
    print("Connecting to Trino...")
    conn = connect(
        host=trino_host,
        port=trino_port,
        user='admin',
        catalog='iceberg',
        schema='default'
    )
    
    try:
        # Create tables
        create_iceberg_tables(conn)
        
        # Generate and insert fake data
        generate_fake_data(conn)
        
        # Verify data
        verify_data(conn)
        
        print("\n✅ Data initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during data initialization: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()

