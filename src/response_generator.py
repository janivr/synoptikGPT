from typing import Dict
from src.gpt_engine import GPTEngine

class ResponseGenerator:
    def __init__(self, system_prompt: str):
        self.gpt_engine = GPTEngine(system_prompt)

    def generate_response(self, data_result: Dict, user_query: str) -> str:
        if 'error' in data_result:
            return data_result['error']
        else:
            initial_response = str(data_result)
            enhanced_response = self.gpt_engine.enhance_response(initial_response, user_query)
            return enhanced_response