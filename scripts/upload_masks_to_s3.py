import os
from PIL import Image
import io
import boto3
from botocore.client import Config
from dotenv import load_dotenv
from numpy import imag
from sqlalchemy.future import select
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker
load_dotenv() 


from app.models import PhoneBrand, PhoneModel

class MaskUploader:

    def __init__(self) -> None:
        self.s3 = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION"),  
            config=Config(signature_version="s3v4")
        )
        DATABASE_URL = os.getenv("EC2_SYNC_DATABASE_URL")
        assert DATABASE_URL is not None, "Database url missing"
        engine = create_engine(DATABASE_URL)
        self.session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    def get_all_phone_models(self):
        with self.session() as session:
            query_result  = session.execute(
                select(PhoneModel.name, 
                       PhoneModel.id, 
                       PhoneBrand.name, 
                       PhoneBrand.id
                       ).join(PhoneBrand, PhoneModel.brand_id == PhoneBrand.id)
            )
            phone_models = query_result.all()
        
        return phone_models
    
    def upload_to_s3(self):
        mask_folder = os.getenv("MASK_FOLDER")
        phone_models = self.get_all_phone_models()
        mask_uploaded = []
        for model in phone_models:
            model_name = model[0]
            model_id = str(model[1])
            brand_name = model[2]
            brand_id = str(model[3])
            mask_path = os.path.join(mask_folder, brand_name, f"{model_name}.png") #type: ignore
            if os.path.exists(mask_path):
                print(f"Uploading {model_name} Mask") 
                image = Image.open(mask_path)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)
                self.s3.upload_fileobj(
                Fileobj=buffer,
                Bucket=os.getenv("AWS_S3_BUCKET"),
                Key=f"Masks/{brand_id}/{model_id}",
                ExtraArgs={'ContentType': 'image/png'}
                )
                mask_uploaded.append(model_id)
            else:
                print(f"Skipping {model_name}")
        self.update_db(mask_uploaded)
    
    def update_db(self, mask_uploaded):
        with self.session() as session:
            session.execute(
                update(PhoneModel).where(PhoneModel.id.in_(mask_uploaded)).values(mask_available = True)
            )
            session.commit()

MaskUploader().upload_to_s3()




