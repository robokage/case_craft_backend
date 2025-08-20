import sys
import asyncio
import csv
import json
from dotenv import load_dotenv
from collections import defaultdict
from sqlalchemy.future import select

load_dotenv()

from app.db import SessionLocal
from app.models import PhoneBrand, PhoneModel


async def seed_from_csv(csv_path):
    async with SessionLocal() as session:
        brand_map = {}  # Map brand name to brand_id

        with open(csv_path, newline='') as csvfile:
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


async def seed_from_json_metadata(json_path):
    async with SessionLocal() as session:
        with open(json_path, "r") as jf:
            metadata = json.load(jf) 
        for model_name, model_data in metadata.items():
            print("model_name:", model_name)
            model_result = await session.execute(select(PhoneModel).where(PhoneModel.name == model_name))
            if model_result.scalar_one_or_none():
                print(f"{model_name} already present in database")
                continue
            brand_name = model_data.get("Designer")
            result = await session.execute(select(PhoneBrand).where(PhoneBrand.name == brand_name))
            brand = result.scalar_one_or_none()
            if not brand:
                brand = PhoneBrand(name=brand_name)
                session.add(brand)
                await session.flush()
            model_height = model_data.get("Height", "").split("|")[-1].split("mm")[0].replace(" ", "")
            model_width = model_data.get("Width", "").split("|")[-1].split("mm")[0].replace(" ", "")
            try:
                model_height = float(model_height)
                model_width = float(model_width)
            except ValueError:
                print(f"Invalid dimensions Height: {model_height} or Width: {model_width} for {model_name}")
                continue
            model = PhoneModel(
                name=model_name,
                brand_id=brand.id,
                phone_width=model_width,
                phone_height=model_height,
            )
            session.add(model)       
        await session.commit()
        print("✅ JSON seed completed.")

            


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kindly pass file path as an arg")
        sys.exit(1)
    print("File path:", sys.argv[1])
    asyncio.run(seed_from_json_metadata(sys.argv[1]))
