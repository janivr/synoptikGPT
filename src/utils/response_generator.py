from typing import Dict, Any
from openai import OpenAI
import json
import logging

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        
    def generate_response(
        self,
        user_query: str,
        query_result: Dict[str, Any],
        schema: Dict
    ) -> str:
        """Generate natural language response from query results"""
        try:
            prompt = self._create_response_prompt(user_query, query_result, schema)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a real estate portfolio analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I apologize, but I encountered an error generating the response: {str(e)}"
            
    def _create_response_prompt(
        self,
        user_query: str,
        query_result: Dict[str, Any],
        schema: Dict
    ) -> str:
        """Create prompt for response generation"""
        return f"""
Given this user query: "{user_query}"

And these query results:
{json.dumps(query_result, indent=2)}

Create a natural language response that:
1. Directly answers the user's question
2. Uses specific numbers and facts from the results
3. Maintains full accuracy
4. Is concise but informative
5. Does not include generic pleasantries

Available data schema:
{json.dumps(schema, indent=2)}
"""