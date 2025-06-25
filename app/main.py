from dotenv import load_dotenv
import os

load_dotenv()  # Loads from .env into environment variables

# Now you can access them
DATABASE_URL = os.getenv("DATABASE_URL")


print(DATABASE_URL)