from openai import OpenAI, OpenAIError
from flask import jsonify
from dotenv import load_dotenv
import os
import logging


load_dotenv()
logger = logging.getLogger(__name__)

class ArticleGpt():
    """
    A class for generating articles using OpenAI's GPT-3.5 Turbo model.
    """

   
    def generatearticle(prompt):
        """
        Generates an article based on the given prompt.

        Args:
            prompt (str): The prompt for generating the article.

        Returns:
            dict: A dictionary containing the generated article as the value for the "message" key.
        """
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt},
                    # {"role": "user", "content": "Who won the world series in 2020?"},
                    # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                    # {"role": "user", "content": "Where was it played?"}
                ],
                max_tokens=150
            )
            logger.info("article gpt response: %s", response)
            # print(response.text)
            content = response.choices[0].message.content
            logger.info("article gpt content: %s", content)

            return {"message": content}
            
        except OpenAIError as e:
           
            print(e.error)
            return jsonify(e)
        except Exception as e:
            print(e)
            return jsonify(e)
       