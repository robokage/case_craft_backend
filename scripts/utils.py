import asyncio
import os


from huggingface_hub import InferenceClient

class Utils:

    def __init__(self) -> None:
        self.client = InferenceClient(
            provider="together",
            api_key=os.environ["HF_TOKEN"],
        )

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

    async def generate_image_async(self, prompt: str, phone_height:float, phone_width:float):
        img_height = self.mm_to_pixels(float(phone_height))
        img_width = self.mm_to_pixels(float(phone_width))

        return await asyncio.to_thread(self.client.text_to_image, 
                                    prompt=prompt, 
                                    model="black-forest-labs/FLUX.1-schnell", 
                                    height=img_height,
                                    width=img_width
                                    )
