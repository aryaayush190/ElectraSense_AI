import pandas as pd
import numpy as np

# Define high priority areas in Himachal Pradesh including hospitals and schools
def generate_high_priority_areas():
    """Generate realistic high priority area data for Himachal Pradesh"""
    
    # List of districts in Himachal Pradesh
    HP_DISTRICTS = [
        "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", 
        "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", 
        "Sirmaur", "Solan", "Una"
    ]
    
    # Generate data
    high_priority_areas = []
    
    # Hospitals
    hospitals = [
        # Shimla
        {"name": "Indira Gandhi Medical College", "type": "Hospital", "district": "Shimla", "latitude": 31.1048, "longitude": 77.1734, "criticality": "High"},
        {"name": "Deen Dayal Upadhyay Hospital", "type": "Hospital", "district": "Shimla", "latitude": 31.1033, "longitude": 77.1819, "criticality": "High"},
        # Kangra
        {"name": "Dr. Rajendra Prasad Medical College", "type": "Hospital", "district": "Kangra", "latitude": 32.0999, "longitude": 76.2999, "criticality": "High"},
        {"name": "Tanda Medical College", "type": "Hospital", "district": "Kangra", "latitude": 32.1046, "longitude": 76.2882, "criticality": "High"},
        # Mandi
        {"name": "Zonal Hospital Mandi", "type": "Hospital", "district": "Mandi", "latitude": 31.7089, "longitude": 76.9311, "criticality": "High"},
        {"name": "ESI Hospital Mandi", "type": "Hospital", "district": "Mandi", "latitude": 31.7102, "longitude": 76.9329, "criticality": "Medium"},
        # Kullu
        {"name": "Regional Hospital Kullu", "type": "Hospital", "district": "Kullu", "latitude": 31.9581, "longitude": 77.1077, "criticality": "High"},
        # Solan
        {"name": "District Hospital Solan", "type": "Hospital", "district": "Solan", "latitude": 30.9045, "longitude": 77.0967, "criticality": "High"},
        # Bilaspur
        {"name": "Regional Hospital Bilaspur", "type": "Hospital", "district": "Bilaspur", "latitude": 31.3344, "longitude": 76.7565, "criticality": "High"},
        # Hamirpur
        {"name": "Regional Hospital Hamirpur", "type": "Hospital", "district": "Hamirpur", "latitude": 31.6858, "longitude": 76.5213, "criticality": "High"},
        # Una
        {"name": "Regional Hospital Una", "type": "Hospital", "district": "Una", "latitude": 31.4685, "longitude": 76.2708, "criticality": "High"},
        # Chamba
        {"name": "Regional Hospital Chamba", "type": "Hospital", "district": "Chamba", "latitude": 32.5533, "longitude": 76.1258, "criticality": "High"},
        # Kinnaur
        {"name": "District Hospital Kinnaur", "type": "Hospital", "district": "Kinnaur", "latitude": 31.5686, "longitude": 78.2645, "criticality": "High"},
        # Lahaul and Spiti
        {"name": "Regional Hospital Keylong", "type": "Hospital", "district": "Lahaul and Spiti", "latitude": 32.5710, "longitude": 77.0347, "criticality": "High"},
        # Sirmaur
        {"name": "District Hospital Nahan", "type": "Hospital", "district": "Sirmaur", "latitude": 30.5597, "longitude": 77.2942, "criticality": "High"}
    ]
    
    # Schools and Educational Institutions
    schools = [
        # Shimla
        {"name": "Himachal Pradesh University", "type": "Educational", "district": "Shimla", "latitude": 31.1033, "longitude": 77.1417, "criticality": "High"},
        {"name": "St. Edward's School", "type": "Educational", "district": "Shimla", "latitude": 31.1065, "longitude": 77.1709, "criticality": "Medium"},
        {"name": "Bishop Cotton School", "type": "Educational", "district": "Shimla", "latitude": 31.1045, "longitude": 77.1777, "criticality": "Medium"},
        # Kangra
        {"name": "Central University of Himachal Pradesh", "type": "Educational", "district": "Kangra", "latitude": 32.1029, "longitude": 76.2675, "criticality": "High"},
        {"name": "IIT Mandi", "type": "Educational", "district": "Mandi", "latitude": 31.7809, "longitude": 76.9865, "criticality": "High"},
        {"name": "NIT Hamirpur", "type": "Educational", "district": "Hamirpur", "latitude": 31.7084, "longitude": 76.5274, "criticality": "High"},
        # Add more educational institutions for each district
        {"name": "Government Degree College Kullu", "type": "Educational", "district": "Kullu", "latitude": 31.9598, "longitude": 77.1113, "criticality": "Medium"},
        {"name": "Government College Solan", "type": "Educational", "district": "Solan", "latitude": 30.9086, "longitude": 77.0977, "criticality": "Medium"},
        {"name": "Government College Bilaspur", "type": "Educational", "district": "Bilaspur", "latitude": 31.3360, "longitude": 76.7585, "criticality": "Medium"},
        {"name": "Government College Una", "type": "Educational", "district": "Una", "latitude": 31.4689, "longitude": 76.2711, "criticality": "Medium"},
        {"name": "Government College Chamba", "type": "Educational", "district": "Chamba", "latitude": 32.5535, "longitude": 76.1272, "criticality": "Medium"},
        {"name": "Government College Recong Peo", "type": "Educational", "district": "Kinnaur", "latitude": 31.5693, "longitude": 78.2647, "criticality": "Medium"},
        {"name": "Government College Keylong", "type": "Educational", "district": "Lahaul and Spiti", "latitude": 32.5715, "longitude": 77.0350, "criticality": "Medium"},
        {"name": "Government College Nahan", "type": "Educational", "district": "Sirmaur", "latitude": 30.5610, "longitude": 77.2935, "criticality": "Medium"}
    ]
    
    # Add all hospitals and schools to high priority areas
    high_priority_areas.extend(hospitals)
    high_priority_areas.extend(schools)
    
    # Add emergency services (fire stations, police stations)
    emergency_services = []
    for district in HP_DISTRICTS:
        # Add a fire station and police station for each district
        emergency_services.append({
            "name": f"{district} Fire Station",
            "type": "Emergency Service",
            "district": district,
            # Generate approximate coordinates (in a real app these would be precise)
            "latitude": hospitals[0]["latitude"] + np.random.uniform(-0.05, 0.05),
            "longitude": hospitals[0]["longitude"] + np.random.uniform(-0.05, 0.05),
            "criticality": "High"
        })
        
        emergency_services.append({
            "name": f"{district} Police Headquarters",
            "type": "Emergency Service",
            "district": district,
            # Generate approximate coordinates
            "latitude": hospitals[0]["latitude"] + np.random.uniform(-0.05, 0.05),
            "longitude": hospitals[0]["longitude"] + np.random.uniform(-0.05, 0.05),
            "criticality": "High"
        })
    
    high_priority_areas.extend(emergency_services)
    
    # Add district-specific electricity risk metrics
    district_risk_metrics = [
        {"district": "Shimla", "risk_score": 0.75, "risk_level": "High", "major_risk_factors": "Heavy snowfall, dense forest areas, tourism load"},
        {"district": "Kangra", "risk_score": 0.65, "risk_level": "Medium", "major_risk_factors": "Monsoon flooding, older infrastructure"},
        {"district": "Kullu", "risk_score": 0.70, "risk_level": "High", "major_risk_factors": "Landslides, flash floods, high seasonal load variation"},
        {"district": "Mandi", "risk_score": 0.60, "risk_level": "Medium", "major_risk_factors": "Flooding, transmission line vulnerability"},
        {"district": "Kinnaur", "risk_score": 0.85, "risk_level": "Very High", "major_risk_factors": "Extreme weather, remote location, avalanches, difficult terrain"},
        {"district": "Lahaul and Spiti", "risk_score": 0.80, "risk_level": "Very High", "major_risk_factors": "Extreme cold, snowfall, isolation, difficult terrain"},
        {"district": "Chamba", "risk_score": 0.65, "risk_level": "Medium", "major_risk_factors": "Mountainous terrain, line damage from storms"},
        {"district": "Hamirpur", "risk_score": 0.50, "risk_level": "Low", "major_risk_factors": "Better infrastructure, fewer geographical challenges"},
        {"district": "Bilaspur", "risk_score": 0.45, "risk_level": "Low", "major_risk_factors": "Lower altitude, better connectivity"},
        {"district": "Una", "risk_score": 0.40, "risk_level": "Low", "major_risk_factors": "Plain areas, better connectivity"},
        {"district": "Solan", "risk_score": 0.55, "risk_level": "Medium", "major_risk_factors": "Industrial load, seasonal variations"},
        {"district": "Sirmaur", "risk_score": 0.60, "risk_level": "Medium", "major_risk_factors": "Industrial areas, agricultural load variations"}
    ]
    
    return pd.DataFrame(high_priority_areas), pd.DataFrame(district_risk_metrics)