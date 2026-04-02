# test_db.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")

# Connect to MySQL
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW()"))
        current_time = result.fetchone()[0]
        print(f"✅ Connected to DB! Current DB time: {current_time}")
except Exception as e:
    print(f"❌ Failed to connect to DB: {e}")
