import os
from openai import OpenAI
from typing import Dict, List, Any

class GPTEngine:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def structure_query(self, user_message: str) -> Dict:
        """Convert natural language query to structured format"""
        prompt = f"""Convert this real estate query into a structured format.
        Query: {user_message}
        
        Return a JSON with these fields:
        - operation: [count, filter, aggregate, compare]
        - dataset: [buildings, financial]
        - filters: dictionary of field:value pairs
        - metrics: list of what to calculate
        - grouping: list of fields to group by
        
        Example 1: "How many buildings in New York?"
        {{
            "operation": "count",
            "dataset": "buildings",
            "filters": {{"Location": "New York"}},
            "metrics": ["count"],
            "grouping": []
        }}
        
        Example 2: "What were the energy costs for B002 in 2023?"
        {{
            "operation": "aggregate",
            "dataset": "financial",
            "filters": {{"Building ID": "B002", "year": 2023}},
            "metrics": ["Energy Costs (USD)"],
            "grouping": ["month"]
        }}"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            return {"error": f"Query structuring failed: {str(e)}"}

    def process_query(self, user_message: str) -> Dict:
        """Process a user query and return structured results"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3
            )

            return {
                "result": response.choices[0].message.content,
                "query": user_message
            }
        except Exception as e:
            return {"error": f"Query processing failed: {str(e)}"}

    def enhance_response(self, data_result: str, user_message: str) -> str:
        """Enhance a data result into a natural language response"""
        enhancement_prompt = f"""Based on this factual response:
"{data_result}"

Please enhance this response to make it more natural while:
1. Maintaining all numerical values exactly as provided
2. Not adding any information not present in the original
3. Not using generic phrases like "feel free to ask"
4. Keeping the same factual content"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": enhancement_prompt},
            {"role": "assistant", "content": data_result}
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Response enhancement failed: {str(e)}"