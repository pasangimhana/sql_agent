import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random


def create_database():
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect("analytics.db")
    cursor = conn.cursor()

    # Create tables
    create_tables(cursor)

    # Generate data with trends
    products_df = generate_products(40)
    customers_df = generate_customers(20)
    marketing_df = generate_marketing(5)
    sales_df = generate_sales(100, products_df, customers_df, marketing_df)

    # Insert data into tables
    products_df.to_sql("products", conn, if_exists="replace", index=False)
    customers_df.to_sql("customers", conn, if_exists="replace", index=False)
    marketing_df.to_sql("marketing", conn, if_exists="replace", index=False)
    sales_df.to_sql("sales", conn, if_exists="replace", index=False)

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Database created successfully with sample data.")


def create_tables(cursor):
    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS sales")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS marketing")

    # Create products table
    cursor.execute(
        """
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT NOT NULL,
        cost REAL NOT NULL,
        price REAL NOT NULL
    )
    """
    )

    # Create customers table
    cursor.execute(
        """
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        segment TEXT NOT NULL,
        join_date DATE NOT NULL
    )
    """
    )

    # Create marketing table
    cursor.execute(
        """
    CREATE TABLE marketing (
        id INTEGER PRIMARY KEY,
        campaign TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        spend REAL NOT NULL,
        channel TEXT NOT NULL,
        target_region TEXT,
        target_segment TEXT
    )
    """
    )

    # Create sales table
    cursor.execute(
        """
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY,
        date DATE NOT NULL,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    """
    )


def generate_products(num_products):
    categories = ["Electronics", "Furniture", "Office Supplies", "Clothing"]
    electronics_subcategories = ["Phones", "Computers", "Tablets", "Accessories"]
    furniture_subcategories = ["Chairs", "Tables", "Storage", "Furnishings"]
    office_subcategories = ["Paper", "Binders", "Art", "Supplies"]
    clothing_subcategories = ["Men", "Women", "Children", "Accessories"]

    category_map = {
        "Electronics": electronics_subcategories,
        "Furniture": furniture_subcategories,
        "Office Supplies": office_subcategories,
        "Clothing": clothing_subcategories,
    }

    # Base price ranges for different categories (establishes a trend)
    category_price_ranges = {
        "Electronics": (100, 1500),
        "Furniture": (50, 800),
        "Office Supplies": (5, 100),
        "Clothing": (15, 150),
    }

    products = []
    for i in range(1, num_products + 1):
        category = random.choice(categories)
        subcategory = random.choice(category_map[category])
        price_range = category_price_ranges[category]

        base_cost = round(random.uniform(price_range[0], price_range[1]), 2)

        # Higher margin for Electronics and Furniture (another trend)
        if category in ["Electronics", "Furniture"]:
            margin = random.uniform(0.4, 0.6)  # 40% to 60% margin
        else:
            margin = random.uniform(0.2, 0.4)  # 20% to 40% margin

        price = round(base_cost * (1 + margin), 2)

        # Add some product naming pattern
        if category == "Electronics":
            name = f"{subcategory[:-1]} Pro {random.randint(1, 10)}"
        elif category == "Furniture":
            styles = ["Modern", "Classic", "Executive", "Ergonomic"]
            name = f"{random.choice(styles)} {subcategory[:-1]}"
        elif category == "Office Supplies":
            name = f"{subcategory} Set {chr(65 + random.randint(0, 25))}"
        else:  # Clothing
            styles = ["Casual", "Formal", "Premium", "Basic"]
            name = f"{random.choice(styles)} {subcategory} Item {random.randint(1, 20)}"

        products.append(
            {
                "id": i,
                "name": name,
                "category": category,
                "subcategory": subcategory,
                "cost": base_cost,
                "price": price,
            }
        )

    return pd.DataFrame(products)


def generate_customers(num_customers):
    regions = ["North", "South", "East", "West", "Central"]
    segments = ["Consumer", "Corporate", "Home Office", "Small Business"]

    # Regional dominance of certain segments (trend)
    region_segment_bias = {
        "North": "Corporate",
        "South": "Consumer",
        "East": "Small Business",
        "West": "Home Office",
        "Central": "Consumer",
    }

    # Create end date as today
    end_date = datetime.now()
    # Create start date as 3 years ago
    start_date = end_date - timedelta(days=3 * 365)

    customers = []
    for i in range(1, num_customers + 1):
        region = random.choice(regions)

        # Apply regional segment bias (70% chance of the dominant segment)
        if random.random() < 0.7:
            segment = region_segment_bias[region]
        else:
            other_segments = [s for s in segments if s != region_segment_bias[region]]
            segment = random.choice(other_segments)

        # Generate join date
        days_between = (end_date - start_date).days
        join_date = start_date + timedelta(days=random.randint(0, days_between))

        # Generate customer name
        first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Jones",
            "Brown",
            "Davis",
            "Miller",
            "Wilson",
            "Moore",
            "Taylor",
        ]
        name = f"{random.choice(first_names)} {random.choice(last_names)}"

        customers.append(
            {
                "id": i,
                "name": name,
                "region": region,
                "segment": segment,
                "join_date": join_date.strftime("%Y-%m-%d"),
            }
        )

    return pd.DataFrame(customers)


def generate_marketing(num_campaigns):
    channels = ["Social Media", "Email", "Search", "Display", "TV", "Print"]
    regions = ["North", "South", "East", "West", "Central", None]  # None for nationwide
    segments = [
        "Consumer",
        "Corporate",
        "Home Office",
        "Small Business",
        None,
    ]  # None for all segments

    # End date as today
    end_date = datetime.now()
    # Start date as 2 years ago
    start_date = end_date - timedelta(days=2 * 365)

    campaigns = []
    for i in range(1, num_campaigns + 1):
        # Generate campaign dates
        campaign_start = start_date + timedelta(days=random.randint(0, 365))
        # Campaign duration between 7 and 60 days
        duration = random.randint(7, 60)
        campaign_end = campaign_start + timedelta(days=duration)

        # Channel affects spend (trend)
        channel = random.choice(channels)
        if channel in ["TV", "Print"]:
            base_spend = random.uniform(20000, 50000)
        elif channel in ["Social Media", "Display"]:
            base_spend = random.uniform(5000, 20000)
        else:
            base_spend = random.uniform(2000, 10000)

        # Longer campaigns cost more
        spend = round(base_spend * (duration / 30), 2)

        # Some campaigns target specific regions/segments
        target_region = random.choice(regions)
        target_segment = random.choice(segments)

        # Campaign name with quarter/year
        quarter = (campaign_start.month - 1) // 3 + 1
        campaign_name = f"Q{quarter} {campaign_start.year} {channel} Campaign"

        campaigns.append(
            {
                "id": i,
                "campaign": campaign_name,
                "start_date": campaign_start.strftime("%Y-%m-%d"),
                "end_date": campaign_end.strftime("%Y-%m-%d"),
                "spend": spend,
                "channel": channel,
                "target_region": target_region,
                "target_segment": target_segment,
            }
        )

    return pd.DataFrame(campaigns)


def generate_sales(num_sales, products_df, customers_df, marketing_df):
    # Set date range for sales data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 2)  # 2 years of data

    # Convert marketing dates to datetime for comparison
    marketing_data = []
    for _, campaign in marketing_df.iterrows():
        marketing_data.append(
            {
                "id": campaign["id"],
                "start_date": datetime.strptime(campaign["start_date"], "%Y-%m-%d"),
                "end_date": datetime.strptime(campaign["end_date"], "%Y-%m-%d"),
                "channel": campaign["channel"],
                "target_region": campaign["target_region"],
                "target_segment": campaign["target_segment"],
            }
        )

    sales = []
    for i in range(1, num_sales + 1):
        # Generate random date within range
        days_between = (end_date - start_date).days
        sale_date = start_date + timedelta(days=random.randint(0, days_between))

        # Introduce seasonality - more sales in Q4 (Oct-Dec)
        month = sale_date.month
        if month in [10, 11, 12]:  # Q4 boost
            if random.random() < 0.3:  # 30% chance to regenerate date to fall in Q4
                q4_start = datetime(sale_date.year, 10, 1)
                q4_end = min(datetime(sale_date.year, 12, 31), end_date)
                if q4_end > q4_start:  # Ensure valid date range
                    days_in_q4 = (q4_end - q4_start).days
                    sale_date = q4_start + timedelta(days=random.randint(0, days_in_q4))

        # Random select customer and product
        customer_id = random.choice(customers_df["id"].tolist())
        product_id = random.choice(products_df["id"].tolist())

        # Get customer and product details
        customer = customers_df[customers_df["id"] == customer_id].iloc[0]
        product = products_df[products_df["id"] == product_id].iloc[0]

        # Apply trends:
        # 1. Certain regions prefer certain product categories
        region_category_boost = {
            "North": "Electronics",
            "South": "Furniture",
            "East": "Clothing",
            "West": "Office Supplies",
            "Central": "Electronics",
        }

        # 2. Customer segments have different quantity patterns
        segment_quantity = {
            "Consumer": (1, 3),
            "Corporate": (3, 10),
            "Home Office": (1, 5),
            "Small Business": (2, 8),
        }

        # Base quantity
        quantity_range = segment_quantity[customer["segment"]]
        base_quantity = random.randint(quantity_range[0], quantity_range[1])

        # Apply region-category boost
        if product["category"] == region_category_boost[customer["region"]]:
            quantity = int(base_quantity * random.uniform(1.2, 1.5))  # 20-50% boost
        else:
            quantity = base_quantity

        # Check if sale happened during a marketing campaign
        campaign_boost = 1.0
        for campaign in marketing_data:
            if (
                sale_date >= campaign["start_date"]
                and sale_date <= campaign["end_date"]
            ):

                # Check if campaign targets this customer's region/segment
                region_match = (
                    campaign["target_region"] is None
                    or campaign["target_region"] == customer["region"]
                )
                segment_match = (
                    campaign["target_segment"] is None
                    or campaign["target_segment"] == customer["segment"]
                )

                # If campaign targets this customer, boost quantity
                if region_match and segment_match:
                    # Different channels have different effectiveness
                    channel_boost = {
                        "Social Media": 1.3,
                        "Email": 1.2,
                        "Search": 1.25,
                        "Display": 1.15,
                        "TV": 1.4,
                        "Print": 1.1,
                    }
                    campaign_boost = max(
                        campaign_boost, channel_boost[campaign["channel"]]
                    )

        # Apply campaign boost
        quantity = int(quantity * campaign_boost)

        # Calculate total price
        unit_price = product["price"]
        total_price = round(quantity * unit_price, 2)

        sales.append(
            {
                "id": i,
                "date": sale_date.strftime("%Y-%m-%d"),
                "product_id": product_id,
                "customer_id": customer_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            }
        )

    return pd.DataFrame(sales)


if __name__ == "__main__":
    create_database()
