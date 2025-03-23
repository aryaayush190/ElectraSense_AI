import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from utils.visualization import plot_grid_map, plot_outage_history
from utils.llm_integration import AIXplainLLMService

def show():
    st.title("Grid Resilience Dashboard")
    
    # Initialize LLM service
    llm_service = AIXplainLLMService()
    
    # Load data from session state
    grid_data = st.session_state.grid_data
    weather_data = st.session_state.weather_data
    outage_history = st.session_state.outage_history
    
    # Filter recent weather data (last 7 days)
    recent_date = datetime.now().date() - timedelta(days=7)
    recent_weather = weather_data[weather_data['date'] >= recent_date]
    
    # Calculate current outages and at-risk components
    # For demo, we'll calculate recent outages (last 7 days) and simulate current outages
    recent_outages = outage_history[outage_history['date'] >= recent_date]
    
    # Simulate some current outages (unresolved recent outages)
    current_outages = recent_outages.copy().iloc[:5]  # Take first 5 as "current"
    current_outages['resolved'] = False
    
    # Calculate risk scores for components based on various factors
    risk_scores = calculate_risk_scores(grid_data, recent_weather, recent_outages)
    
    # Identify components at risk (risk score > 0.6)
    substations_at_risk = [(sub_id, score) for sub_id, score in risk_scores.items() 
                           if score > 0.6 and sub_id.startswith('SUB-')]
    
    lines_at_risk = [(line_id, score) for line_id, score in risk_scores.items() 
                     if score > 0.6 and line_id.startswith('LINE-')]
    
    # Create layout with multiple columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Grid Status")
        
        # Display interactive map
        st.write("Power Grid Map with Risk Analysis")
        m = plot_grid_map(grid_data, current_outages, risk_scores)
        
        # Display the map using streamlit-folium
        from streamlit_folium import folium_static
        folium_static(m, width=700, height=500)
    
    with col2:
        st.subheader("Summary")
        
        # Display key metrics
        metrics_col1, metrics_col2 = st.columns(2)
        
        with metrics_col1:
            st.metric(label="Active Outages", value=len(current_outages))
            st.metric(label="Substations at Risk", value=len(substations_at_risk))
        
        with metrics_col2:
            st.metric(label="Weather Alerts", value=sum(recent_weather['storm_event']))
            st.metric(label="Lines at Risk", value=len(lines_at_risk))
        
        # Generate weather alerts
        weather_alerts = generate_weather_alerts(recent_weather)
        
        # Display weather alerts
        if weather_alerts:
            st.subheader("Weather Alerts")
            for alert in weather_alerts:
                st.warning(alert['message'])
        
        # Prepare context for LLM recommendation
        dashboard_context = {
            'substations_at_risk': substations_at_risk,
            'lines_at_risk': lines_at_risk,
            'weather_alerts': weather_alerts,
            'active_outages': current_outages.to_dict('records') if not current_outages.empty else []
        }
        
        # Get LLM recommendation
        with st.spinner("Generating recommendations..."):
            recommendation = llm_service.generate_recommendation(
                context=dashboard_context,
                query_type='dashboard'
            )
        
        # Display executive recommendation
        st.subheader("AI Recommendations")
        st.info(recommendation)
    
    # Display outage history and statistics
    st.subheader("Outage History")
    
    # Filters for outage history
    col1, col2, col3 = st.columns(3)
    with col1:
        district_filter = st.selectbox("Filter by District", 
                                     ["All Districts"] + sorted(outage_history['district'].unique().tolist()))
    with col2:
        component_filter = st.selectbox("Filter by Component Type", 
                                      ["All Components", "substation", "line"])
    with col3:
        days_filter = st.slider("Days to Display", 
                              min_value=7, max_value=365, value=90, step=7)
    
    # Apply filters
    filtered_history = outage_history.copy()
    if district_filter != "All Districts":
        filtered_history = filtered_history[filtered_history['district'] == district_filter]
    if component_filter != "All Components":
        filtered_history = filtered_history[filtered_history['component_type'] == component_filter]
    
    cutoff_date = datetime.now().date() - timedelta(days=days_filter)
    filtered_history = filtered_history[filtered_history['date'] >= cutoff_date]
    
    # Create charts
    fig_time, fig_cause = plot_outage_history(filtered_history)
    
    if fig_time and fig_cause:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_time, use_container_width=True)
        with col2:
            st.plotly_chart(fig_cause, use_container_width=True)
    else:
        st.write("No outage data available for the selected filters.")
    
    # Display recent outages in a table
    st.subheader("Recent Outages")
    if not recent_outages.empty:
        # Format for display
        display_df = recent_outages[['date', 'district', 'component_type', 'component_id', 'cause', 'duration_hours']].copy()
        display_df.columns = ['Date', 'District', 'Component Type', 'Component ID', 'Cause', 'Duration (hours)']
        st.dataframe(display_df.sort_values('Date', ascending=False).head(10), use_container_width=True)
    else:
        st.write("No recent outages to display.")

def calculate_risk_scores(grid_data, recent_weather, recent_outages):
    """Calculate risk scores for grid components based on various factors"""
    risk_scores = {}
    
    # Get latest weather data for each district
    latest_weather = recent_weather.sort_values('date').groupby('district').last().reset_index()
    
    # Calculate for substations
    for _, substation in grid_data['substations'].iterrows():
        sub_id = substation['id']
        district = substation['district']
        
        # Base risk from health index (inverted, as lower health = higher risk)
        base_risk = 1 - substation['health_index']
        
        # Age factor (older = higher risk)
        age = 2023 - substation['year_commissioned']
        age_factor = min(1.0, age / 40)  # Cap at 40 years
        
        # Recent outages factor
        recent_sub_outages = recent_outages[
            (recent_outages['component_type'] == 'substation') & 
            (recent_outages['component_id'] == sub_id)
        ]
        outage_factor = min(1.0, len(recent_sub_outages) * 0.2)  # 0.2 per recent outage, max 1.0
        
        # Weather factor
        weather_factor = 0.0
        district_weather = latest_weather[latest_weather['district'] == district]
        if not district_weather.empty:
            weather = district_weather.iloc[0]
            if weather['storm_event']:
                weather_factor += 0.4
            if weather['precipitation_mm'] > 30:
                weather_factor += 0.3
            if weather['wind_speed_kmh'] > 40:
                weather_factor += 0.3
            if weather['snow_cm'] > 5:
                weather_factor += 0.3
            
            # Cap weather factor
            weather_factor = min(1.0, weather_factor)
        
        # Calculate total risk score (weighted sum)
        risk_score = (
            0.3 * base_risk + 
            0.2 * age_factor + 
            0.25 * outage_factor + 
            0.25 * weather_factor
        )
        
        risk_scores[sub_id] = risk_score
    
    # Calculate for transmission lines
    for _, line in grid_data['transmission_lines'].iterrows():
        line_id = line['id']
        
        # Get from substation's district for weather
        from_sub_id = line['from_substation']
        from_sub = grid_data['substations'][grid_data['substations']['id'] == from_sub_id].iloc[0]
        district = from_sub['district']
        
        # Base risk from health index
        base_risk = 1 - line['health_index']
        
        # Age factor
        age = 2023 - line['year_commissioned']
        age_factor = min(1.0, age / 30)  # Cap at 30 years
        
        # Load factor (higher load = higher risk)
        load_factor = min(1.0, line['current_load_pct'] / 100)
        
        # Length factor (longer = higher risk)
        length_factor = min(1.0, line['length_km'] / 100)  # Cap at 100km
        
        # Recent outages factor
        recent_line_outages = recent_outages[
            (recent_outages['component_type'] == 'line') & 
            (recent_outages['component_id'] == line_id)
        ]
        outage_factor = min(1.0, len(recent_line_outages) * 0.25)
        
        # Weather factor
        weather_factor = 0.0
        district_weather = latest_weather[latest_weather['district'] == district]
        if not district_weather.empty:
            weather = district_weather.iloc[0]
            if weather['storm_event']:
                weather_factor += 0.5
            if weather['wind_speed_kmh'] > 35:
                weather_factor += 0.4
            if weather['precipitation_mm'] > 25:
                weather_factor += 0.2
            
            # Cap weather factor
            weather_factor = min(1.0, weather_factor)
        
        # Calculate total risk score
        risk_score = (
            0.2 * base_risk + 
            0.15 * age_factor + 
            0.25 * load_factor + 
            0.1 * length_factor +
            0.15 * outage_factor + 
            0.15 * weather_factor
        )
        
        risk_scores[line_id] = risk_score
    
    return risk_scores

def generate_weather_alerts(recent_weather):
    """Generate weather alerts based on recent weather data"""
    alerts = []
    
    # Get the most recent date
    max_date = recent_weather['date'].max()
    today_weather = recent_weather[recent_weather['date'] == max_date]
    
    # Check for storm events
    storm_districts = today_weather[today_weather['storm_event']]['district'].unique()
    if len(storm_districts) > 0:
        alerts.append({
            'type': 'storm',
            'districts': storm_districts.tolist(),
            'message': f"Storm alerts in {', '.join(storm_districts[:3])}{'...' if len(storm_districts) > 3 else ''}"
        })
    
    # Check for heavy rainfall
    heavy_rain_districts = today_weather[today_weather['precipitation_mm'] > 50]['district'].unique()
    if len(heavy_rain_districts) > 0:
        alerts.append({
            'type': 'rain',
            'districts': heavy_rain_districts.tolist(),
            'message': f"Heavy rainfall in {', '.join(heavy_rain_districts[:3])}{'...' if len(heavy_rain_districts) > 3 else ''}"
        })
    
    # Check for high winds
    high_wind_districts = today_weather[today_weather['wind_speed_kmh'] > 40]['district'].unique()
    if len(high_wind_districts) > 0:
        alerts.append({
            'type': 'wind',
            'districts': high_wind_districts.tolist(),
            'message': f"High winds in {', '.join(high_wind_districts[:3])}{'...' if len(high_wind_districts) > 3 else ''}"
        })
    
    # Check for snow
    snow_districts = today_weather[today_weather['snow_cm'] > 10]['district'].unique()
    if len(snow_districts) > 0:
        alerts.append({
            'type': 'snow',
            'districts': snow_districts.tolist(),
            'message': f"Heavy snow in {', '.join(snow_districts[:3])}{'...' if len(snow_districts) > 3 else ''}"
        })
    
    return alerts
