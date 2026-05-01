from flask import jsonify
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
load_dotenv()
import os


# nltk.download('punkt')
# nltk.download('stopwords')

class SEOGpt():
    def generate_keywords(prompt):
        """
        Generate relevant keywords using OpenAI GPT-3.

        Args:
            prompt (str): The text prompt to generate keywords from.

        Returns:
            dict: A dictionary containing the generated keywords.

        Raises:
            Exception: If there is an error generating keywords.
            OpenAIError: If there is an error with the OpenAI API.

        """
        # Customize the prompt to ask for keywords
        prompt += "\n\nFind relevant keywords in the text."
        
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Generate a completion using OpenAI GPT-3
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150
            )
            
            # Extract and return the generated keywords
            content = response.choices[0].message.content
            return {"message": content}
        
        except Exception as e:
            print(e)
            return {"message": "Error generating keywords"}
        
        except OpenAIError as e:
            print(e.http_status)
            print(e.error)
            return jsonify(e)
    # def analyze_seo(content):
    #     # Tokenize the content into words
    #     words = word_tokenize(content.lower())

    #     # Remove stopwords and non-alphabetic words
    #     stop_words = set(stopwords.words('english'))
    #     print("stop_words",stop_words)
    #     words = [word for word in words if word.isalpha() and word not in stop_words]

    #     # Calculate keyword frequency
    #     keyword_frequency = Counter(words)

    #     # Calculate sentence count and average words per sentence
    #     sentences = sent_tokenize(content)
    #     sentence_count = len(sentences)
    #     words_per_sentence = len(words) / sentence_count if sentence_count > 0 else 0

    #     # Check meta description length
    #     meta_description_length = len(content) if len(content) <= 160 else 0

    #     return {
    #         'keyword_frequency': keyword_frequency,
    #         'sentence_count': sentence_count,
    #         'words_per_sentence': words_per_sentence,
    #         'meta_description_length': meta_description_length
    #     }

    # def print_seo_analysis(seo_analysis):
    #     print("Keyword Frequency:")
    #     for word, count in seo_analysis['keyword_frequency'].most_common(10):
    #         print(f"{word}: {count}")
    #     top_10_keywords = seo_analysis['keyword_frequency'].most_common(10)
    #     all_words_appended = ' '.join([f"{word}" for word, count in top_10_keywords])

    #     print(all_words_appended)
    #     # print("\nSentence Count:", seo_analysis['sentence_count'])
    #     # print("Words per Sentence:", seo_analysis['words_per_sentence'])
        
    #     # if seo_analysis['meta_description_length'] > 0:
    #     #     print("Meta Description Length is within recommended limit.")
    #     # else:
    #     #     print("Meta Description Length exceeds recommended limit (160 characters).")

    #     return {'message':all_words_appended}