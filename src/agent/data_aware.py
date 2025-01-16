from typing import Dict, List, Any, Optional
import pandas as pd
from openai import OpenAI
import json
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAwareAgent:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.buildings_df = None
        self.financial_df = None
        logger.info("DataAwareAgent initialized")
        
    def load_data(self, buildings_path: str, financial_path: str) -> Dict:
        """Load and validate CSV data files"""
        try:
            self.buildings_df = pd.read_csv(buildings_path)
            self.financial_df = pd.read_csv(financial_path)
            self.financial_df['Date'] = pd.to_datetime(self.financial_df['Date'])
            return {"status": "success", "buildings": len(self.buildings_df)}
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def process_query(self, user_query: str) -> str:
        """Process user query"""
        try:
            # First try direct patterns
            direct_result = self._handle_direct_patterns(user_query.lower())
            if direct_result:
                return direct_result
                
            # Then try specific handlers
            result = self._handle_specific_queries(user_query.lower())
            if result:
                return result
                
            # Finally, fall back to GPT for complex queries
            return self._handle_complex_query(user_query)
            
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            return f"I apologize, but I encountered an error. Please try rephrasing your question."

    def _handle_direct_patterns(self, query: str) -> Optional[str]:
        """Handle common query patterns without GPT"""
        patterns = {
            r'how many (?:buildings|properties) (?:do we have |are there )?in (.+?)\??$':
                lambda m: self._count_buildings_by_location(m.group(1)),
                
            r'how many (.*?) buildings(?:| do we have)(?:| in total)?\??$':
                lambda m: self._count_buildings_by_type(m.group(1)),
                
            r'(?:what is |show me |tell me )the building with (?:the )?highest (.+?)\??$':
                lambda m: self._find_highest_value(m.group(1)),
        }
        
        for pattern, handler in patterns.items():
            match = re.search(pattern, query)
            if match:
                try:
                    return handler(match)
                except Exception as e:
                    logger.error(f"Error in pattern handler: {str(e)}")
                    return None
        return None

    def _handle_specific_queries(self, query: str) -> Optional[str]:
        """Handle specific types of queries"""
        if "less than 3 years old" in query:
            return self._count_recent_buildings()
        elif "average energy cost" in query:
            return self._calculate_average_energy_cost()
        elif "highest capacity" in query:
            return self._find_highest_capacity()
            
        return None

    def _count_buildings_by_location(self, location: str) -> str:
        location = location.strip().lower()
        count = len(self.buildings_df[self.buildings_df['Location'].str.lower() == location])
        return f"There are {count} buildings in {location}."

    def _count_buildings_by_type(self, building_type: str) -> str:
        building_type = building_type.strip().lower()
        df = self.buildings_df
        
        if building_type == "retail":
            count = len(df[df['Purpose'].str.lower() == 'retail'])
            return f"There are {count} retail buildings in the portfolio."
        
        return None

    def _find_highest_capacity(self) -> str:
        row = self.buildings_df.loc[self.buildings_df['Employee Capacity'].idxmax()]
        return (f"Building {row['Building ID']} in {row['Location']} has the highest capacity, "
                f"accommodating {row['Employee Capacity']:,} employees. "
                f"It is a {row['Purpose']} building with {row['Size']:,} square feet.")

    def _count_recent_buildings(self) -> str:
        current_year = datetime.now().year
        recent_buildings = self.buildings_df[self.buildings_df['Year Built'] > (current_year - 3)]
        count = len(recent_buildings)
        return f"There are {count} buildings less than 3 years old."

    def _calculate_average_energy_cost(self) -> str:
        energy_costs = self.financial_df[
            self.financial_df['Date'].dt.year == 2023
        ]['Energy Costs (USD)'].mean()
        
        return f"The average energy cost per building in 2023 was ${energy_costs:,.2f}."

    def _find_highest_value(self, metric: str) -> Optional[str]:
        if "capacity" in metric.lower():
            return self._find_highest_capacity()
        return None

    def _handle_complex_query(self, query: str) -> str:
        """Handle complex queries using GPT but with minimal token usage"""
        prompt = f"""Analyze this real estate query: '{query}'
        Return ONLY a JSON with:
        - metric: what to measure
        - filters: any conditions
        - calculation: [count, sum, average, max, min]
        Example: {{"metric": "capacity", "filters": {{"location": "New York"}}, "calculation": "max"}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a query analyzer. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        try:
            plan = json.loads(response.choices[0].message.content)
            result = self._execute_complex_query(plan)
            return self._format_complex_result(result)
        except json.JSONDecodeError:
            return "I'm sorry, I couldn't understand that query. Could you rephrase it?"