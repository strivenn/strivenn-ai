from openai import OpenAI, OpenAIError
from flask import jsonify
import os
from classes.params import MODEL_DALLE_GPT,IMAGE_SIZE,IMAGE_QUALITY,NUMBER_OF_IMAGES
class DalleGpt:
    """
    A class for generating images using the DALL-E GPT model.

    Args:
        prompt (str): The prompt for generating the image.

    Attributes:
        prompt (str): The prompt for generating the image.

    Methods:
        generate_dalle_image: Generates an image using the DALL-E GPT model.

    """

    def __init__(self, prompt):
        self.prompt = prompt
        self.generate_dalle_image()

    def generate_dalle_image(prompt):
        """
        Generates an image using the DALL-E GPT model.

        Returns:
            dict: The generated image response.

        Raises:
            OpenAIError: If there is an error while generating the image.

        """
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.images.generate(
                model=MODEL_DALLE_GPT,
                prompt=prompt,
                size=IMAGE_SIZE,
                quality=IMAGE_QUALITY,
                n=NUMBER_OF_IMAGES,
            )
            # return jsonify(response.data[0])
            return {
                "message": response.data[0].revised_prompt,
                "image_url":response.data[0].url
                }
        except OpenAIError as e:
            return jsonify(e)