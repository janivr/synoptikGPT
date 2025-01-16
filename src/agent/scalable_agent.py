from typing import Dict, List, Any
from openai import OpenAI
import json
import logging
from src.data_manager.manager import DataManager
from src.query_engine.engine import QueryEngine
from src.utils.response_generator import ResponseGenerator
from src.utils.utils import convert_numpy_types

class ScalableAgent:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.data_manager = DataManager()
        self.query_engine = QueryEngine()
        self.response_generator = ResponseGenerator(self.client)
        self.logger = logging.getLogger(__name__)

    def process_query(self, user_query: str) -> str:
        """Process user query"""
        try:
            # Let GPT understand the query and create a plan
            query_plan = self._create_query_plan(user_query)
            
            # Execute the plan using the query engine
            query_result = self.query_engine.execute_query(query_plan, self.data_manager)
            
            # Convert results to JSON-serializable format
            serialized_result = convert_numpy_types(query_result)
            
            # Generate the response
            return self.response_generator.generate_response(
                user_query,
                serialized_result,
                self.data_manager.get_schema()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def _create_query_plan(self, user_query: str) -> Dict:
        """Create a structured query plan using GPT"""
        schema = self.data_manager.get_schema()
        prompt = self._create_schema_aware_prompt(user_query, schema)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data query planner. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        return json.loads(response.choices[0].message.content)

    def _create_schema_aware_prompt(self, query: str, schema: Dict) -> str:
        """Create a prompt that includes schema information"""
        return f"""Given this user query: "{query}"
And these available data sources and their schemas:
{json.dumps(schema, indent=2)}

Create a query plan as a JSON object with these fields:
- source: which data source to use
- filters: any conditions to apply
- group_by: fields to group by (if needed)
- aggregate: calculations to perform
- operations: list of operations in order

Example format:
{{
    "source": "buildings",
    "filters": {{"field": "value"}},
    "group_by": ["field1", "field2"],
    "aggregate": {{"field": "operation"}}
}}"""