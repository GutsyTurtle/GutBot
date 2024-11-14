import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to PostgreSQL
def initialize_database():
    # Establish the database connection
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Define the SQL command to create the starboard_configs table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS starboard_configs (
        guild_id BIGINT PRIMARY KEY,
        channel_id BIGINT NOT NULL,
        emoji TEXT NOT NULL,
        threshold INT NOT NULL
    );
    """

    # Execute the command
    cur.execute(create_table_query)
    conn.commit()  # Commit the transaction

    print("Database initialized. Table 'starboard_configs' created if it did not exist.")

    # Close the cursor and connection
    cur.close()
    conn.close()

if __name__ == "__main__":
    initialize_database()
