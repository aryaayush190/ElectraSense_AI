import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Himachal Pradesh districts and major cities
HP_DISTRICTS = [
    "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", 
    "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", 
    "Sirmaur", "Solan", "Una"
]

# Geographical data of grid substations
def generate_substations(num_substations=30):
    """Generate realistic substation data for Himachal Pradesh"""
    np.random.seed(42)  # For reproducibility
    
    # Himachal Pradesh bounds (approximate)
    lat_min, lat_max = 30.3, 33.3
    lon_min, lon_max = 75.5, 79.0
    
    # Generate data
    substations = []
    for i in range(num_substations):
        substation = {
            'id': f'SUB-{i+1:03d}',
            'name': f'Substation {i+1}',
            'district': np.random.choice(HP_DISTRICTS),
            'latitude': np.random.uniform(lat_min, lat_max),
            'longitude': np.random.uniform(lon_min, lon_max),
            'capacity_mw': np.random.choice([33, 66, 132, 220, 400]),
            'voltage_level': np.random.choice(['11kV', '33kV', '66kV', '132kV', '220kV', '400kV']),
            'year_commissioned': np.random.randint(1980, 2023),
            'transformer_count': np.random.randint(1, 8),
            'health_index': np.random.uniform(0.6, 1.0),  # 0-1 scale
        }
        substations.append(substation)
    
    return pd.DataFrame(substations)

# Generate transmission line data
def generate_transmission_lines(substations, num_lines=50):
    """Generate transmission line data connecting substations"""
    np.random.seed(43)
    
    lines = []
    for i in range(num_lines):
        # Select random substations for each line
        sub_ids = np.random.choice(substations['id'].values, size=2, replace=False)
        sub1 = substations[substations['id'] == sub_ids[0]].iloc[0]
        sub2 = substations[substations['id'] == sub_ids[1]].iloc[0]
        
        # Calculate approximate distance
        dist = np.sqrt((sub1['latitude'] - sub2['latitude'])**2 + 
                       (sub1['longitude'] - sub2['longitude'])**2) * 111  # km
        
        line = {
            'id': f'LINE-{i+1:03d}',
            'from_substation': sub_ids[0],
            'to_substation': sub_ids[1],
            'voltage': np.random.choice(['33kV', '66kV', '132kV', '220kV', '400kV']),
            'length_km': round(dist, 2),
            'capacity_mw': np.random.randint(50, 500),
            'year_commissioned': np.random.randint(1980, 2023),
            'current_load_pct': np.random.uniform(30, 90),
            'health_index': np.random.uniform(0.6, 1.0),
        }
        lines.append(line)
    
    return pd.DataFrame(lines)

# Generate historical weather data
def generate_weather_data(days=365):
    """Generate historical weather data for Himachal Pradesh"""
    np.random.seed(44)
    
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)) for i in range(days)]
    
    weather_data = []
    for date in dates:
        # Seasonal variations
        month = date.month
        # Winter: Nov-Feb, Summer: Mar-Jun, Monsoon: Jul-Oct
        is_winter = month in [11, 12, 1, 2]
        is_summer = month in [3, 4, 5, 6]
        is_monsoon = month in [7, 8, 9, 10]
        
        # Base values with seasonal adjustments
        if is_winter:
            temp_base = np.random.normal(5, 8)
            precip_base = np.random.exponential(5)
            wind_base = np.random.normal(15, 5)
            storm_prob = 0.05
        elif is_summer:
            temp_base = np.random.normal(25, 7)
            precip_base = np.random.exponential(10)
            wind_base = np.random.normal(20, 8)
            storm_prob = 0.15
        else:  # Monsoon
            temp_base = np.random.normal(20, 5)
            precip_base = np.random.exponential(30)
            wind_base = np.random.normal(25, 10)
            storm_prob = 0.30
        
        for district in HP_DISTRICTS:
            # Add district-specific variations
            if district in ["Kinnaur", "Lahaul and Spiti"]:
                temp_adj = -5  # Colder
                precip_adj = 0.7  # Less precipitation in cold desert
                storm_adj = 0.8  # Less storms
            elif district in ["Shimla", "Kullu"]:
                temp_adj = -2
                precip_adj = 1.2
                storm_adj = 1.1
            else:
                temp_adj = 0
                precip_adj = 1.0
                storm_adj = 1.0
            
            temp = max(-15, min(45, temp_base + temp_adj + np.random.normal(0, 2)))
            precip = max(0, precip_base * precip_adj * np.random.uniform(0.8, 1.2))
            wind = max(0, wind_base * np.random.uniform(0.8, 1.2))
            
            # Storm occurrence
            storm = np.random.random() < (storm_prob * storm_adj)
            
            weather_data.append({
                'date': date,
                'district': district,
                'temperature_c': round(temp, 1),
                'precipitation_mm': round(precip, 1),
                'wind_speed_kmh': round(wind, 1),
                'storm_event': storm,
                'humidity_pct': round(np.random.uniform(30, 95), 1),
                'snow_cm': round(max(0, np.random.exponential(2)) if is_winter and temp < 0 else 0, 1)
            })
    
    return pd.DataFrame(weather_data)

# Generate historical outage data
def generate_outage_history(substations, transmission_lines, weather_data, num_outages=200):
    """Generate historical outage data based on infrastructure and weather"""
    np.random.seed(45)
    
    outages = []
    dates = sorted(weather_data['date'].unique())
    
    # Factors that increase outage probability
    def calc_outage_probability(date, substation=None, line=None, weather=None):
        prob = 0.01  # Base probability
        
        # Infrastructure age factor
        year_commissioned = substation['year_commissioned'] if substation is not None else line['year_commissioned']
        age = 2023 - year_commissioned
        prob += 0.001 * age  # Older infrastructure more likely to fail
        
        # Health index factor
        health_index = substation['health_index'] if substation is not None else line['health_index']
        prob += 0.05 * (1 - health_index)  # Lower health = higher probability
        
        # Weather factors if available
        if weather is not None:
            if weather['storm_event']:
                prob += 0.2  # Significant increase during storms
            
            # Snow affects substations
            if substation is not None and weather['snow_cm'] > 5:
                prob += 0.15
            
            # High winds affect lines
            if line is not None and weather['wind_speed_kmh'] > 30:
                prob += 0.1
            
            # Heavy rain affects both
            if weather['precipitation_mm'] > 50:
                prob += 0.1
        
        return min(prob, 0.5)  # Cap probability
    
    for _ in range(num_outages):
        # Randomly choose a date
        date = np.random.choice(dates)
        
        # Randomly choose affected component (substation or line)
        component_type = np.random.choice(['substation', 'line'])
        
        if component_type == 'substation':
            component = substations.sample(1).iloc[0]
            component_id = component['id']
            district = component['district']
            
            # Get weather data for that district and date
            weather = weather_data[(weather_data['date'] == date) & 
                                   (weather_data['district'] == district)].iloc[0]
            
            # Calculate duration based on factors
            base_duration = np.random.exponential(3)  # Base hours
            
            # Adjust duration based on weather and infrastructure
            duration_multiplier = 1.0
            if weather['storm_event']:
                duration_multiplier *= 2.0
            if weather['snow_cm'] > 5:
                duration_multiplier *= 1.5
            if component['health_index'] < 0.8:
                duration_multiplier *= 1.3
            
            duration_hours = base_duration * duration_multiplier
            
            cause = np.random.choice([
                "Equipment Failure", "Weather Related", "Scheduled Maintenance", 
                "Animal/Bird Contact", "Tree Contact", "Unknown"
            ], p=[0.3, 0.25, 0.2, 0.1, 0.1, 0.05])
            
        else:  # line
            component = transmission_lines.sample(1).iloc[0]
            component_id = component['id']
            
            # Get from substation's district for weather
            from_sub_id = component['from_substation']
            from_sub = substations[substations['id'] == from_sub_id].iloc[0]
            district = from_sub['district']
            
            # Get weather data
            weather = weather_data[(weather_data['date'] == date) & 
                                   (weather_data['district'] == district)].iloc[0]
            
            # Calculate duration
            base_duration = np.random.exponential(4)  # Lines typically take longer
            
            # Adjust duration based on factors
            duration_multiplier = 1.0
            if weather['wind_speed_kmh'] > 30:
                duration_multiplier *= 1.8
            if weather['precipitation_mm'] > 40:
                duration_multiplier *= 1.4
            if component['health_index'] < 0.8:
                duration_multiplier *= 1.3
            
            duration_hours = base_duration * duration_multiplier
            
            cause = np.random.choice([
                "Line Damage", "Weather Related", "Scheduled Maintenance", 
                "Tree Contact", "Tower/Pole Damage", "Unknown"
            ], p=[0.35, 0.3, 0.15, 0.1, 0.05, 0.05])
        
        outage = {
            'outage_id': f'OUT-{len(outages)+1:04d}',
            'date': date,
            'component_type': component_type,
            'component_id': component_id,
            'district': district,
            'start_time': datetime.combine(date, datetime.min.time()).replace(
                hour=np.random.randint(0, 24),
                minute=np.random.choice([0, 15, 30, 45])
            ),
            'duration_hours': max(0.5, min(72, round(duration_hours, 1))),
            'cause': cause,
            'customers_affected': np.random.randint(100, 10000),
            'resolved': True,
        }
        outages.append(outage)
    
    # Sort by date
    outage_df = pd.DataFrame(outages)
    outage_df = outage_df.sort_values('date')
    
    # Add end time
    outage_df['end_time'] = outage_df['start_time'] + pd.to_timedelta(outage_df['duration_hours'], unit='h')
    
    return outage_df

def initialize_data():
    """Initialize all datasets"""
    # Generate or load data
    print("Generating infrastructure data...")
    substations = generate_substations(30)
    transmission_lines = generate_transmission_lines(substations, 50)
    
    # Combine as grid data
    grid_data = {
        'substations': substations,
        'transmission_lines': transmission_lines
    }
    
    print("Generating weather data...")
    weather_data = generate_weather_data(365)  # Last year
    
    print("Generating outage history...")
    outage_history = generate_outage_history(substations, transmission_lines, weather_data, 200)
    
    # Create infrastructure condition data
    infrastructure_data = substations.copy()
    infrastructure_data['component_type'] = 'substation'
    infrastructure_data['last_maintenance'] = pd.to_datetime(
        [f"2023-{np.random.randint(1, 12):02d}-{np.random.randint(1, 28):02d}" for _ in range(len(infrastructure_data))]
    )
    infrastructure_data['maintenance_frequency_days'] = np.random.randint(30, 365, size=len(infrastructure_data))
    infrastructure_data['condition_score'] = np.random.uniform(60, 98, size=len(infrastructure_data))
    
    return grid_data, weather_data, outage_history, infrastructure_data

if __name__ == "__main__":
    # Test data generation
    grid_data, weather_data, outage_history, infrastructure_data = initialize_data()
    print("Data generation complete.")
    print(f"Generated {len(grid_data['substations'])} substations")
    print(f"Generated {len(grid_data['transmission_lines'])} transmission lines")
    print(f"Generated {len(weather_data)} weather data points")
    print(f"Generated {len(outage_history)} historical outage records")
