from typing import Dict, Callable

class ResponseGenerator:
    def __init__(self):
        self.formatters = {
            'capacity': self._format_capacity_response,
            'energy_target': self._format_energy_target_response,
            'utility_costs': self._format_utility_costs_response,
            'count': self._format_count_response,
            'age': self._format_age_response,
            'built_in_year': self._format_built_in_year_response,
            'location': self._format_location_response,
            'comparison': self._format_comparison_response,
            'operating_expense': self._format_operating_expense_response,
            'size': self._format_size_response
        }

    def generate_response(self, query_result: Dict) -> str:
        """Generate a natural language response from the query result"""
        if 'error' in query_result:
            return f"I apologize, but {query_result['error']}."
            
        response_type = query_result.get('type')
        if response_type in self.formatters:
            return self.formatters[response_type](query_result)
        
        return "I apologize, but I couldn't generate a response for this query type."

    def _format_capacity_response(self, result: Dict) -> str:
        data = result['data']
        subtype = result['subtype']
        capacity = data['Employee Capacity']
        
        response = f"Building {data['Building ID']} in {data['Location']} has the {subtype} "
        response += f"capacity, accommodating {capacity:,} employees. "
        response += f"This is a {data['Purpose']} building with {data['Size']:,} square feet "
        response += f"and {data['Floors']} floors."
        
        if data.get('LEED Certified') == 'checked':
            response += " The building is LEED certified."
            
        return response

    def _format_energy_target_response(self, result: Dict) -> str:
        data = result['data']
        target = data['Energy Target (kWh/sqft/yr)']
        
        response = f"Building {data['Building ID']} in {data['Location']} has the highest "
        response += f"energy target at {target} kWh per square foot per year. "
        response += f"This {data['Purpose']} building has {data['Size']:,} square feet "
        response += f"and was built in {data['Year Built']}."
        
        return response

    def _format_utility_costs_response(self, result: Dict) -> str:
        building_id = result.get('building_id', 'Unknown')
        year = result.get('year')
        monthly_data = result.get('data', {})
        
        if not building_id or not year or not monthly_data:
            return "Unable to retrieve utility costs data. Some required information is missing."
            
        response = f"Monthly utility costs for Building {building_id} in {year}:\n"
        for month, cost in sorted(monthly_data.items()):
            month_name = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }[month]
            response += f"- {month_name}: ${cost:,.2f}\n"
        
        return response

    def _format_count_response(self, result: Dict) -> str:
        subtype = result['subtype']
        
        if subtype == 'leed':
            return f"There are {result['count']} LEED certified buildings in the portfolio."
        elif subtype == 'ownership':
            return (f"In the portfolio, {result['lease_count']} buildings are leased and "
                   f"{result['own_count']} buildings are owned.")
        else:
            return f"The portfolio consists of {result['count']} buildings."

    def _format_age_response(self, result: Dict) -> str:
        data = result['data']
        age = result['age']
        subtype = result['subtype']
        
        response = f"The {subtype} building is {data['Building ID']} in {data['Location']}, "
        response += f"built in {data['Year Built']} ({age} years old). "
        response += f"It is a {data['Purpose']} building with {data['Size']:,} square feet."
        
        if data.get('LEED Certified') == 'checked':
            response += " The building is LEED certified."
        
        return response

    def _format_built_in_year_response(self, result: Dict) -> str:
        year = result['year']
        count = result['count']
        buildings = result['buildings']
        
        if count == 0:
            return f"No buildings were constructed in {year}."
        
        response = f"{count} building{'s' if count > 1 else ''} "
        response += f"{'were' if count > 1 else 'was'} built in {year}: "
        response += ", ".join(buildings)
        return response

    def _format_location_response(self, result: Dict) -> str:
        data = result['data']
        response = "Regional distribution of buildings:\n"
        for region, count in data.items():
            response += f"- {region}: {count} buildings\n"
        return response

    def _format_comparison_response(self, result: Dict) -> str:
        buildings_data = result['data']
        building_ids = result['buildings']
        
        response = f"Comparison between buildings {' and '.join(building_ids)}:\n"
        for building in buildings_data:
            response += f"\n{building['Building ID']} ({building['Location']}):\n"
            response += f"- Size: {building['Size']:,} square feet\n"
            response += f"- Purpose: {building['Purpose']}\n"
            response += f"- Built in: {building['Year Built']}\n"
            response += f"- Employee Capacity: {building['Employee Capacity']:,}\n"
        
        return response

    def _format_operating_expense_response(self, result: Dict) -> str:
        if result['subtype'] == 'total':
            amount = result['amount']
            year = result['year']
            return f"The total operating expense for all buildings in {year} is ${amount:,.2f}."
        
        return "Operating expense information is not available in the requested format."

    def _format_size_response(self, result: Dict) -> str:
        data = result['data']
        size = data['Size']
        
        response = f"Building {data['Building ID']} in {data['Location']} is the largest, "
        response += f"with {size:,} square feet. "
        response += f"It is a {data['Purpose']} building with {data['Floors']} floors "
        response += f"and can accommodate {data['Employee Capacity']:,} employees."
        
        if data.get('LEED Certified') == 'checked':
            response += " The building is LEED certified."
        
        return response

    def register_formatter(self, response_type: str, formatter_func: Callable):
        """Register a new response formatter for custom modules"""
        self.formatters[response_type] = formatter_func