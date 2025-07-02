import asyncio
import os
import replicate
import base64
import redis
import redis.exceptions
import boto3
from botocore.client import Config
import io
import cloudinary
import cloudinary.uploader as cd_uploader
from huggingface_hub import InferenceClient, upload_file
from uuid import uuid4



class Utils:

    def __init__(self) -> None:
        self.client = InferenceClient(
            provider="together",
            api_key=os.environ["HF_TOKEN"],
        )
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True
        )
        self.s3 = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION"),  
            config=Config(signature_version="s3v4")
        )
        try:
            self.r = redis.Redis(host='localhost', port=6379)
            self.r.ping()
            print("✅ Redis server is running.")
        except redis.exceptions.ConnectionError:
            print("❌ Redis server is NOT running.")

    @staticmethod
    def mm_to_pixels(mm: float, dpi: int = 300) -> int:
        """_summary_

        Args:
            mm (float): _description_
            dpi (int, optional): _description_. Defaults to 300.

        Returns:
            int: _description_
        """
        pixel_value =  round((mm / 25.4) * dpi)
        if pixel_value % 16 == 0:
            return pixel_value
        else:
            return ((pixel_value // 16) + 1) * 16

    async def generate_with_hf(self, prompt: str, phone_height:float, phone_width:float):
        """_summary_

        Args:
            prompt (str): _description_
            phone_height (float): _description_
            phone_width (float): _description_

        Returns:
            _type_: _description_
        """
        img_height = self.mm_to_pixels(float(phone_height))
        img_width = self.mm_to_pixels(float(phone_width))

        return await asyncio.to_thread(self.client.text_to_image, 
                                    prompt=prompt, 
                                    model="black-forest-labs/FLUX.1-schnell", 
                                    height=img_height,
                                    width=img_width
                                    )


    async def generate_with_replicate(self, prompt: str, phone_height:float, phone_width:float, num_outputs:int):
        """_summary_

        Args:
            prompt (str): _description_
            phone_height (float): _description_
            phone_width (float): _description_
            num_outputs (int): _description_

        Returns:
            _type_: _description_
        """
        img_height = self.mm_to_pixels(float(phone_height))
        img_width = self.mm_to_pixels(float(phone_width))
        input = {
            "prompt": prompt,
            "aspect_ratio": self.closest_aspect_ratio(img_width, img_height),
            "output_format": "png",
            "num_outputs":num_outputs
        }
        outputs =  await replicate.async_run("black-forest-labs/flux-schnell", 
                                           input=input)
        
        img_data = {}
        if not isinstance(outputs, list):
            print("Generated Output is not a List.")
            return img_data
        for img_bytes in outputs:
            img_base64 = self.convert_img_to_data_uri(img_bytes)
            img_data[uuid4] = {"base64": img_base64,
                                      "bytes": img_bytes}
        return img_data
    

    @staticmethod
    def closest_aspect_ratio(width: int, height: int) -> str:
        aspect_ratios = {
            "1:1": 1 / 1,
            "16:9": 16 / 9,
            "21:9": 21 / 9,
            "3:2": 3 / 2,
            "2:3": 2 / 3,
            "4:5": 4 / 5,
            "5:4": 5 / 4,
            "3:4": 3 / 4,
            "4:3": 4 / 3,
            "9:16": 9 / 16,
            "9:21": 9 / 21
        }

        input_ratio = width / height
        closest = min(aspect_ratios.items(), key=lambda x: abs(x[1] - input_ratio))
        return closest[0]
    
    @staticmethod
    def convert_img_to_data_uri(image_bytes):
        base64_str = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = "image/png"  
        data_uri = f"data:{mime_type};base64,{base64_str}"
        return data_uri

    @staticmethod
    def upload_to_cloudinary(img_bytes):
        upload_result = cd_uploader.upload(img_bytes)
        return upload_result.get('url', "")

    def upload_to_s3(self, img_bytes, file_uuid):
        """_summary_

        Args:
            img_bytes (_type_): _description_
            file_uuid (_type_): _description_

        Returns:
            _type_: _description_
        """
        self.s3.upload_fileobj(
            Fileobj=img_bytes,
            Bucket=os.getenv("AWS_S3_BUCKET"),
            Key=file_uuid,
            ExtraArgs={'ContentType': 'image/png'}
            )
        signed_url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": os.getenv("AWS_S3_BUCKET"), "Key": file_uuid},
        )
        self.r.set(file_uuid, signed_url)
