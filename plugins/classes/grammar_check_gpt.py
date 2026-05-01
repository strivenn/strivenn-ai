from flask import jsonify  # jsonify is used elsewhere in the code
import logging
from openai import OpenAI,OpenAIError
import os
from classes.params import GRAMMAR_INSTRUCTION,MODEL_GPT_TURBO

logger = logging.getLogger(__name__)

class GrammarCheck():
    """
    A class for performing grammar check and correction.

    Args:
        prompt (str): The text to be checked for grammar errors.

    Methods:
        grammar_check_and_correct: Performs grammar check and correction on the given text.
    """

    def grammar_check_and_correct(prompt):
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                    model=MODEL_GPT_TURBO,
                    messages=[
                        {"role": "user", "content": GRAMMAR_INSTRUCTION},
                        {"role": "user", "content": prompt}
                    ]
                )
            # print(response.text)
            content = response.choices[0].message.content
            logger.info("article gpt content: %s", content)

            return {"message": content}
        except OpenAIError as e:
            logger.info(f"error{e}")
            return jsonify(e)