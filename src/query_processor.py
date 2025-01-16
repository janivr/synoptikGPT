import logging
from typing import Dict, List, Any
from src.data_models.buildings import BuildingsModel
from src.data_models.financial import FinancialModel
from src.gpt_engine import GPTEngine

class QueryProcessor:
    def __init__(self, buildings_model: BuildingsModel, financial_model: FinancialModel):
        self.buildings_model = buildings_model
        self.financial_model = financial_model
        self.gpt_engine = GPTEngine(system_prompt="You are a real estate query assistant.")
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def process_query(self, user_query: str) -> Dict:
        """Main method to process user queries"""
        self.logger.info(f"Processing query: {user_query}")
        
        try:
            # Get structured query from GPT
            query_structure = self.analyze_natural_language_query(user_query)
            
            # Execute the structured query
            return self.execute_query(query_structure)
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {"error": f"Failed to process query: {str(e)}"}

    def analyze_natural_language_query(self, user_query: str) -> Dict:
        """Convert natural language query to structured format using GPT"""
        self.logger.info(f"Analyzing query: {user_query}")
        try:
            query_structure = self.gpt_engine.structure_query(user_query)
            self.logger.info(f"Generated query structure: {query_structure}")
            return query_structure
        except Exception as e:
            self.logger.error(f"Error analyzing query: {str(e)}")
            return {"error": "Failed to analyze query"}

    def execute_query(self, query_structure: Dict) -> Dict:
        """Execute the structured query on the appropriate dataset"""
        if isinstance(query_structure, str):
            try:
                # If query_structure is a string (from GPT), parse it to dict
                import json
                query_structure = json.loads(query_structure)
            except json.JSONDecodeError:
                return {"error": "Invalid query structure"}

        operation = query_structure.get("operation")
        dataset = query_structure.get("dataset")
        
        if "error" in query_structure:
            return query_structure

        try:
            if dataset == "buildings":
                return self._execute_buildings_query(query_structure)
            elif dataset == "financial":
                return self._execute_financial_query(query_structure)
            else:
                return {"error": f"Unknown dataset: {dataset}"}
        except Exception as e:
            return {"error": f"Query execution failed: {str(e)}"}

    def _execute_buildings_query(self, query_structure: Dict) -> Dict:
        """Execute queries on the buildings dataset"""
        operation = query_structure.get("operation")
        filters = query_structure.get("filters", {})
        
        if operation == "count":
            filtered_buildings = self.buildings_model.filter_buildings(filters)
            return {
                "type": "count",
                "result": len(filtered_buildings),
                "filters_applied": filters
            }
            
        elif operation == "filter":
            filtered_buildings = self.buildings_model.filter_buildings(filters)
            return {
                "type": "filter",
                "result": filtered_buildings.to_dict('records'),
                "count": len(filtered_buildings)
            }
            
        return {"error": f"Unsupported operation for buildings: {operation}"}

    def _execute_financial_query(self, query_structure: Dict) -> Dict:
        """Execute queries on the financial dataset"""
        operation = query_structure.get("operation")
        filters = query_structure.get("filters", {})
        metrics = query_structure.get("metrics", [])
        
        if operation == "aggregate":
            # Get the relevant building's financial data
            building_id = filters.get("Building ID")
            if building_id:
                financial_data = self.financial_model.get_building_financials(building_id)
                return {
                    "type": "financial",
                    "result": financial_data.to_dict('records'),
                    "building_id": building_id
                }
                
        return {"error": f"Unsupported operation for financials: {operation}"}