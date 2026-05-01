from openai import OpenAI, OpenAIError
from flask import jsonify
from dotenv import load_dotenv
import os
import logging
from classes.params import GPT_ERROR_MESSAGE

load_dotenv()
logger = logging.getLogger(__name__)

class TitleGpt():
    """
    A class for generating articles using OpenAI's GPT-3.5 Turbo model.
    """

   
    def generate_title(ideaprompt):
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            logger.info("client: %s", client)
            keyword = "Give me an suitable title for the below topic\t"
            prompt = keyword + ideaprompt 
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                    ],
                max_tokens=150
            )
            content = response.choices[0].message.content
            logger.info("idea gpt response: %s", content)

            return {"message": content}
            
        except OpenAIError as e:
           
            return {"message":GPT_ERROR_MESSAGE}