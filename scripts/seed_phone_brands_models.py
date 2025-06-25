import asyncio
import csv
from collections import defaultdict
from pathlib import Path

from app.db import SessionLocal
from app.models import PhoneBrand, PhoneModel


CSV_FILE = Path("C:\\Users\\Rakshat Shetty\\Downloads\\phone_models.csv")


async def seed_from_csv():
    async with SessionLocal() as session:
        brand_map = {}  # Map brand name to brand_id

        with open(CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows_by_brand = defaultdict(list)

            for row in reader:
                brand = row["brand"].strip()
                rows_by_brand[brand].append(row)

            # Insert brands and get their IDs
            for brand_name in rows_by_brand:
                brand_obj = PhoneBrand(name=brand_name)
                session.add(brand_obj)
                await session.flush()  # Get brand ID
                brand_map[brand_name] = brand_obj.id

            # Insert models
            for brand, rows in rows_by_brand.items():
                for row in rows:
                    model = PhoneModel(
                        name=row["model"].strip(),
                        brand_id=brand_map[brand],
                        phone_width=float(row["phone_width"]),
                        phone_height=float(row["phone_height"]),
                        s3_path=row["s3_path"].strip()
                    )
                    session.add(model)

        await session.commit()
        print("✅ CSV seed completed.")


if __name__ == "__main__":
    asyncio.run(seed_from_csv())
