import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read floor capacities
floor_capacities_df = pd.read_csv('data/floors_occupancy.csv')

# Common parameters
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 1, 21)
time_interval = timedelta(minutes=30)

# Holidays for USA 2024-2025
holidays = [
    # 2024 Holidays
    datetime(2024, 1, 1),   # New Year's Day
    datetime(2024, 1, 15),  # Martin Luther King Jr. Day
    datetime(2024, 2, 19),  # Presidents' Day
    datetime(2024, 5, 27),  # Memorial Day
    datetime(2024, 7, 4),   # Independence Day
    datetime(2024, 9, 2),   # Labor Day
    datetime(2024, 10, 14), # Columbus Day
    datetime(2024, 11, 11), # Veterans Day
    datetime(2024, 11, 28), # Thanksgiving Day
    datetime(2024, 12, 25), # Christmas Day
    
    # 2025 Holidays
    datetime(2025, 1, 1),   # New Year's Day
    datetime(2025, 1, 20),  # Martin Luther King Jr. Day
]

def generate_realistic_occupancy(building_id, building_floors, start_date, end_date, 
                               time_interval, holidays, occupancy_rate):
    data = []
    floor_max_capacities = dict(zip(building_floors['Floor'], building_floors['Max Capacity']))
    
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends and holidays
        if current_date.weekday() < 5 and current_date not in holidays:
            # For each floor
            for floor in building_floors['Floor'].sort_values():
                # Get all times for this floor
                for time in pd.date_range(
                    start=current_date.replace(hour=7, minute=0),
                    end=current_date.replace(hour=20, minute=0),
                    freq=time_interval
                ):
                    floor_max_cap = floor_max_capacities[floor]
                    
                    # Base occupancy calculation
                    if 6 <= time.hour < 9:  # Morning arrival
                        base_rate = (time.hour - 6) / 3
                    elif 9 <= time.hour < 12:  # Peak morning
                        base_rate = 0.8
                    elif 12 <= time.hour < 13:  # Lunchtime dip
                        base_rate = 0.6
                    elif 13 <= time.hour < 17:  # Afternoon peak
                        base_rate = 0.9
                    elif 17 <= time.hour < 20:  # Evening departure
                        base_rate = (20 - time.hour) / 3
                    else:  # Late evening
                        base_rate = 0.05

                    # Calculate floor occupancy
                    max_floor_occupancy = floor_max_cap * occupancy_rate[floor]
                    floor_occupancy = int(max_floor_occupancy * base_rate + 
                                       np.random.randint(-3, 4))
                    
                    # Ensure floor occupancy is within bounds
                    floor_occupancy = max(0, min(floor_occupancy, floor_max_cap))

                    # Format datetime as string
                    time_str = time.strftime('%d/%m/%Y %H:%M')
                    
                    data.append([building_id, floor, time_str, floor_occupancy])

        current_date += timedelta(days=1)

    # Create DataFrame with specific column names
    return pd.DataFrame(data, columns=["Building ID", "Floor", "Time", "Occupancy"])

# Define building groups (11 buildings per file, except the last one which will have 10)
building_groups = {
    1: range(1, 12),    # Buildings 1-11
    2: range(12, 23),   # Buildings 12-22
    3: range(23, 34),   # Buildings 23-33
    4: range(34, 44)    # Buildings 34-43
}

# Process each group
for group_num, building_range in building_groups.items():
    print(f"\nProcessing Group {group_num}...")
    all_group_data = []
    
    for building_number in building_range:
        building_id = f"B{str(building_number).zfill(3)}"
        print(f"Processing {building_id}...")
        
        # Filter capacities for specific building
        building_floors = floor_capacities_df[floor_capacities_df['Building ID'] == building_id]
        
        if len(building_floors) == 0:
            print(f"No floor data found for {building_id}, skipping...")
            continue
            
        floors = len(building_floors)
        employee_capacity = building_floors['Max Capacity'].sum()

        # Generate random occupancy rates for each floor (10% to 100%)
        occupancy_rate = {floor: np.random.randint(10, 100) / 100 
                         for floor in building_floors['Floor'].values}

        # Print building details
        print(f"Number of Floors: {floors}")
        print(f"Total Building Capacity: {employee_capacity}")

        # Generate data
        building_data = generate_realistic_occupancy(
            building_id, building_floors, start_date, end_date, 
            time_interval, holidays, occupancy_rate
        )
        
        all_group_data.append(building_data)
    
    # Combine all buildings in the group and save to a single file
    if all_group_data:
        group_data = pd.concat(all_group_data, ignore_index=True)
        output_filename = f"Building_Group_{group_num}_Occupancy_2024.csv"
        group_data.to_csv(output_filename, index=False)
        
        print(f"\nGroup {group_num} Statistics:")
        print(f"Total number of records: {len(group_data)}")
        print(f"Date range: from {group_data['Time'].min()} to {group_data['Time'].max()}")
        print(f"Number of buildings: {len(group_data['Building ID'].unique())}")
        print(f"File saved as: {output_filename}")

print("\nAll building groups processed successfully!")