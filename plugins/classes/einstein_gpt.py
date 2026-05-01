from openai import OpenAI, OpenAIError
from flask import jsonify
import os

import openai


class EinsteinGpt():

    def generate_review(input_article):
        # Customize the prompt to ask for keywords
        keyword = "Give me a five experts name with their explanation on\t"
        prompt = keyword + input_article 
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Make a request to OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            # print(response.choices[0].message.content)
            reviewed_article = response.choices[0].message.content

            return {"message": reviewed_article}
        except OpenAIError as e:
            # print(str(e))
            return jsonify(e)
