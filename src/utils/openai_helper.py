# src/utils/openai_helper.py
import os
from openai import OpenAI
from dotenv import load_dotenv


class OpenAIHelper:
    def __init__(self):
        """
        Initialize OpenAI client with environment variables
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.client = None
    
    def generate_response(self, messages, model="gpt-3.5-turbo", max_tokens=1000):
        """
        Generate response using OpenAI chat completion
        
        :param messages: List of message dictionaries
        :param model: OpenAI model to use
        :param max_tokens: Maximum tokens in response
        :return: Generated response
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return None