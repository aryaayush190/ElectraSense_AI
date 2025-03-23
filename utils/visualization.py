import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def plot_grid_map(grid_data, outage_data=None, risk_scores=None):
    """
    Create an interactive map of the power grid with substations and transmission lines
    
    Parameters:
    - grid_data: Dictionary containing substations and transmission lines data
    - outage_data: Optional dataframe with current outages
    - risk_scores: Optional dictionary mapping component IDs to risk scores
    
    Returns:
    - Folium map object
    """
    substations = grid_data['substations']
    lines = grid_data['transmission_lines']
    
    # Calculate center point for map
    center_lat = substations['latitude'].mean()
    center_lon = substations['longitude'].mean()
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='OpenStreetMap')
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Create marker clusters for substations
    marker_cluster = MarkerCluster().add_to(m)
    
    # Create a dictionary to map substation IDs to their coordinates
    substation_coords = {}
    
    # Add substations to map
    for _, sub in substations.iterrows():
        sub_id = sub['id']
        lat, lon = sub['latitude'], sub['longitude']
        substation_coords[sub_id] = (lat, lon)
        
        # Determine color based on risk score if available
        color = 'blue'
        popup_text = f"<b>{sub['name']}</b><br>ID: {sub_id}<br>District: {sub['district']}<br>Capacity: {sub['capacity_mw']} MW"
        
        if risk_scores is not None and sub_id in risk_scores:
            risk = risk_scores[sub_id]
            if risk > 0.7:
                color = 'red'
                popup_text += f"<br><b>Risk Score: {risk:.2f} (High)</b>"
            elif risk > 0.4:
                color = 'orange'
                popup_text += f"<br><b>Risk Score: {risk:.2f} (Medium)</b>"
            else:
                color = 'green'
                popup_text += f"<br><b>Risk Score: {risk:.2f} (Low)</b>"
        
        # Check if there's an outage for this substation
        if outage_data is not None and not outage_data.empty and 'component_type' in outage_data.columns and 'component_id' in outage_data.columns:
            outage = outage_data[
                (outage_data['component_type'] == 'substation') & 
                (outage_data['component_id'] == sub_id)
            ]
            if not outage.empty:
                color = 'red'
                popup_text += "<br><b>OUTAGE</b>"
        
        # Create marker
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=sub['name'],
            icon=folium.Icon(color=color, icon='flash', prefix='fa')
        ).add_to(marker_cluster)
    
    # Add transmission lines
    for _, line in lines.iterrows():
        from_sub = line['from_substation']
        to_sub = line['to_substation']
        
        if from_sub in substation_coords and to_sub in substation_coords:
            color = 'blue'
            weight = 2
            line_id = line['id']
            
            # Determine color based on risk score if available
            if risk_scores is not None and line_id in risk_scores:
                risk = risk_scores[line_id]
                if risk > 0.7:
                    color = 'red'
                    weight = 4
                elif risk > 0.4:
                    color = 'orange'
                    weight = 3
                else:
                    color = 'green'
            
            # Check if there's an outage for this line
            if outage_data is not None and not outage_data.empty and 'component_type' in outage_data.columns and 'component_id' in outage_data.columns:
                outage = outage_data[
                    (outage_data['component_type'] == 'line') & 
                    (outage_data['component_id'] == line_id)
                ]
                if not outage.empty:
                    color = 'red'
                    weight = 4
            
            # Add line to map
            folium.PolyLine(
                [substation_coords[from_sub], substation_coords[to_sub]],
                color=color,
                weight=weight,
                opacity=0.7,
                popup=f"Line ID: {line_id}<br>Capacity: {line['capacity_mw']} MW<br>Current Load: {line['current_load_pct']}%"
            ).add_to(m)
    
    return m

def plot_outage_history(outage_history, district=None, component_type=None, last_n_days=None):
    """
    Create interactive charts of outage history
    
    Parameters:
    - outage_history: DataFrame with outage history data
    - district: Optional filter for specific district
    - component_type: Optional filter for component type ('substation' or 'line')
    - last_n_days: Optional filter for data from the last n days
    
    Returns:
    - Plotly figure objects
    """
    # Apply filters
    df = outage_history.copy()
    
    if district:
        df = df[df['district'] == district]
    
    if component_type:
        df = df[df['component_type'] == component_type]
    
    if last_n_days:
        cutoff_date = datetime.now().date() - timedelta(days=last_n_days)
        df = df[df['date'] >= cutoff_date]
    
    if df.empty:
        return None, None
    
    # Create time series chart of outage counts
    df_grouped = df.groupby('date').size().reset_index(name='count')
    fig_time = px.bar(
        df_grouped, 
        x='date', 
        y='count',
        title='Outages Over Time',
        labels={'date': 'Date', 'count': 'Number of Outages'}
    )
    
    # Create pie chart of outage causes
    cause_counts = df['cause'].value_counts().reset_index()
    cause_counts.columns = ['cause', 'count']
    fig_cause = px.pie(
        cause_counts, 
        values='count', 
        names='cause',
        title='Outage Causes'
    )
    
    return fig_time, fig_cause

def plot_weather_correlation(outage_history, weather_data):
    """
    Create scatter plots showing correlation between weather factors and outage duration
    
    Parameters:
    - outage_history: DataFrame with outage history
    - weather_data: DataFrame with weather data
    
    Returns:
    - Plotly figure object
    """
    # Merge outage and weather data
    merged_data = pd.merge(
        outage_history,
        weather_data,
        on=['date', 'district'],
        how='inner'
    )
    
    if merged_data.empty:
        return None
    
    # Create scatter plot for temperature vs. outage duration
    fig_temp = px.scatter(
        merged_data,
        x='temperature_c',
        y='duration_hours',
        color='storm_event',
        hover_data=['district', 'cause'],
        title='Temperature vs. Outage Duration',
        labels={
            'temperature_c': 'Temperature (°C)',
            'duration_hours': 'Outage Duration (hours)',
            'storm_event': 'Storm Event'
        },
        size='precipitation_mm',
        size_max=15
    )
    
    return fig_temp

def plot_outage_prediction(features, prediction, prediction_intervals=None):
    """
    Create a visualization of outage prediction results
    
    Parameters:
    - features: Dict of input features
    - prediction: The predicted outage duration
    - prediction_intervals: Optional confidence intervals
    
    Returns:
    - Plotly figure object
    """
    # Create gauge chart for predicted duration
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=prediction,
        title={'text': "Predicted Outage Duration (hours)"},
        gauge={
            'axis': {'range': [0, max(24, prediction * 1.5)]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 4], 'color': "lightgreen"},
                {'range': [4, 12], 'color': "yellow"},
                {'range': [12, 24], 'color': "orange"},
                {'range': [24, max(24, prediction * 1.5)], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': prediction
            }
        }
    ))
    
    return fig

def plot_load_balance_results(load_balance_results):
    """
    Create visualizations for load balancing simulation results
    
    Parameters:
    - load_balance_results: Dict of simulation results
    
    Returns:
    - Plotly figure objects
    """
    line_status = load_balance_results.get('line_status', {})
    
    if not line_status:
        return None
    
    # Convert to DataFrame
    lines_df = pd.DataFrame([
        {
            'line_id': line_id,
            'from_to': f"{data['from_substation']} → {data['to_substation']}",
            'load_percentage': data['load_percentage'],
            'capacity_mw': data['capacity_mw'],
            'current_load_mw': data['current_load_mw'],
            'status': data['status']
        }
        for line_id, data in line_status.items()
    ])
    
    # Sort by load percentage descending
    lines_df = lines_df.sort_values('load_percentage', ascending=False)
    
    # Create bar chart of line loads
    fig = px.bar(
        lines_df,
        x='line_id',
        y='load_percentage',
        color='status',
        hover_data=['from_to', 'capacity_mw', 'current_load_mw'],
        title='Transmission Line Load Distribution',
        labels={
            'line_id': 'Transmission Line',
            'load_percentage': 'Load (%)',
            'status': 'Status'
        },
        color_discrete_map={
            'Normal': 'green',
            'Warning': 'orange',
            'Overloaded': 'red'
        }
    )
    
    return fig

def plot_disaster_scenario_results(disaster_results):
    """
    Create visualizations for disaster scenario simulation results
    
    Parameters:
    - disaster_results: Dict of simulation results
    
    Returns:
    - Plotly figure objects
    """
    if not disaster_results:
        return None, None
    
    # Create bar chart for resilience metrics
    metrics = disaster_results.get('resilience_metrics', {})
    if metrics:
        metrics_df = pd.DataFrame([
            {'Metric': 'Fragmentation', 'Value': metrics.get('fragmentation', 0)},
            {'Metric': 'Connectivity Loss (%)', 'Value': metrics.get('connectivity_loss', 0)},
            {'Metric': 'Impact Severity (%)', 'Value': metrics.get('impact_severity', 0)}
        ])
        
        fig_metrics = px.bar(
            metrics_df,
            x='Metric',
            y='Value',
            title='Grid Resilience Metrics',
            labels={'Value': 'Score'},
            color='Metric',
            color_discrete_map={
                'Fragmentation': 'blue',
                'Connectivity Loss (%)': 'orange',
                'Impact Severity (%)': 'red'
            }
        )
    else:
        fig_metrics = None
    
    # Create pie chart for impacted component distribution
    impacted_substations = len(disaster_results.get('impacted_substations', []))
    impacted_lines = len(disaster_results.get('impacted_lines', []))
    
    if impacted_substations > 0 or impacted_lines > 0:
        impact_df = pd.DataFrame([
            {'Component': 'Substations', 'Count': impacted_substations},
            {'Component': 'Transmission Lines', 'Count': impacted_lines}
        ])
        
        fig_impact = px.pie(
            impact_df,
            values='Count',
            names='Component',
            title='Impacted Components Distribution',
            color='Component',
            color_discrete_map={
                'Substations': 'blue',
                'Transmission Lines': 'orange'
            }
        )
    else:
        fig_impact = None
    
    return fig_metrics, fig_impact
