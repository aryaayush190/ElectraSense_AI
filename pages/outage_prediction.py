import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from models.outage_predictor import OutagePredictor
from utils.visualization import plot_outage_prediction, plot_weather_correlation
from utils.llm_integration import AIXplainLLMService

def show():
    st.title("Outage Prediction Tool")
    
    # Load data from session state
    grid_data = st.session_state.grid_data
    weather_data = st.session_state.weather_data
    outage_history = st.session_state.outage_history
    
    # Initialize predictor
    if 'outage_predictor' not in st.session_state:
        st.session_state.outage_predictor = OutagePredictor()
        
        # Train the model (only once)
        with st.spinner("Training outage prediction model..."):
            st.session_state.outage_predictor.train(grid_data, weather_data, outage_history)
    
    # Initialize LLM service
    llm_service = AIXplainLLMService()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Outage Prediction", "Weather Correlation Analysis"])
    
    with tab1:
        st.subheader("Predict Outage Duration")
        
        # Form for input parameters
        with st.form("prediction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Component selection
                component_type = st.selectbox(
                    "Component Type",
                    ["substation", "line"]
                )
                
                if component_type == "substation":
                    component_options = grid_data['substations']['id'].tolist()
                    component_names = grid_data['substations']['name'].tolist()
                    component_display = [f"{id} ({name})" for id, name in zip(component_options, component_names)]
                else:
                    component_options = grid_data['transmission_lines']['id'].tolist()
                    component_display = component_options
                
                component_id = st.selectbox(
                    "Component ID",
                    options=range(len(component_options)),
                    format_func=lambda x: component_display[x]
                )
                selected_component_id = component_options[component_id]
                
                # Get district for selected component
                if component_type == "substation":
                    district = grid_data['substations'][grid_data['substations']['id'] == selected_component_id]['district'].iloc[0]
                else:
                    # For lines, use the district of the 'from' substation
                    from_sub = grid_data['transmission_lines'][grid_data['transmission_lines']['id'] == selected_component_id]['from_substation'].iloc[0]
                    district = grid_data['substations'][grid_data['substations']['id'] == from_sub]['district'].iloc[0]
                
                # Outage cause
                cause = st.selectbox(
                    "Outage Cause",
                    ["Equipment Failure", "Weather Related", "Scheduled Maintenance", 
                     "Animal/Bird Contact", "Tree Contact", "Tower/Pole Damage", "Unknown"]
                )
            
            with col2:
                # Weather conditions
                temperature = st.slider("Temperature (°C)", -20, 45, 20)
                precipitation = st.slider("Precipitation (mm)", 0, 100, 0)
                wind_speed = st.slider("Wind Speed (km/h)", 0, 120, 10)
                storm_event = st.checkbox("Storm Event")
                humidity = st.slider("Humidity (%)", 0, 100, 50)
                snow = st.slider("Snow (cm)", 0, 50, 0)
            
            submitted = st.form_submit_button("Predict Outage Duration")
        
        # Make prediction when form is submitted
        if submitted:
            # Prepare features
            if component_type == "substation":
                component = grid_data['substations'][grid_data['substations']['id'] == selected_component_id].iloc[0]
                features = {
                    'component_type': component_type,
                    'district': district,
                    'voltage_level': component['voltage_level'],
                    'capacity_mw': component['capacity_mw'],
                    'age_years': 2023 - component['year_commissioned'],
                    'health_index': component['health_index'],
                    'transformer_count': component['transformer_count'],
                    'line_length_km': 0,  # N/A for substations
                    'current_load_pct': 0,  # N/A for substations
                    'temperature_c': temperature,
                    'precipitation_mm': precipitation,
                    'wind_speed_kmh': wind_speed,
                    'storm_event': storm_event,
                    'humidity_pct': humidity,
                    'snow_cm': snow,
                    'cause': cause
                }
            else:  # line
                component = grid_data['transmission_lines'][grid_data['transmission_lines']['id'] == selected_component_id].iloc[0]
                features = {
                    'component_type': component_type,
                    'district': district,
                    'voltage_level': component['voltage'],
                    'capacity_mw': component['capacity_mw'],
                    'age_years': 2023 - component['year_commissioned'],
                    'health_index': component['health_index'],
                    'transformer_count': 0,  # N/A for lines
                    'line_length_km': component['length_km'],
                    'current_load_pct': component['current_load_pct'],
                    'temperature_c': temperature,
                    'precipitation_mm': precipitation,
                    'wind_speed_kmh': wind_speed,
                    'storm_event': storm_event,
                    'humidity_pct': humidity,
                    'snow_cm': snow,
                    'cause': cause
                }
            
            # Make prediction
            duration_prediction = st.session_state.outage_predictor.predict_outage_duration(features)
            outage_probability = st.session_state.outage_predictor.predict_outage_probability(features)
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Predicted Outage Duration", f"{duration_prediction:.2f} hours")
                st.metric("Outage Probability", f"{outage_probability:.1%}")
                
                # Format duration in a more readable way
                hours = int(duration_prediction)
                minutes = int((duration_prediction - hours) * 60)
                if hours > 0:
                    duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
                    if minutes > 0:
                        duration_str += f" {minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                
                st.write(f"Expected outage duration: **{duration_str}**")
            
            with col2:
                # Visualization
                fig = plot_outage_prediction(features, duration_prediction)
                st.plotly_chart(fig, use_container_width=True)
            
            # Get LLM recommendation
            with st.spinner("Generating AI recommendation..."):
                # Prepare context for LLM
                context = {
                    'component_type': component_type,
                    'component_id': selected_component_id,
                    'district': district,
                    'outage_probability': outage_probability,
                    'predicted_duration': duration_prediction,
                    'weather': {
                        'temperature_c': temperature,
                        'precipitation_mm': precipitation,
                        'wind_speed_kmh': wind_speed,
                        'storm_event': storm_event,
                        'humidity_pct': humidity,
                        'snow_cm': snow
                    },
                    'cause': cause
                }
                
                recommendation = llm_service.generate_recommendation(
                    context=context,
                    query_type='outage'
                )
            
            # Display recommendation
            st.subheader("AI Recommendation")
            st.info(recommendation)
    
    with tab2:
        st.subheader("Weather Impact Analysis")
        
        # Weather correlation plot
        weather_corr_fig = plot_weather_correlation(outage_history, weather_data)
        if weather_corr_fig:
            st.plotly_chart(weather_corr_fig, use_container_width=True)
        else:
            st.write("Insufficient data for correlation analysis.")
        
        # Additional analysis - outage duration by district in different weather conditions
        st.subheader("Outage Duration by District")
        
        # Merge outage and weather data
        merged_data = pd.merge(
            outage_history,
            weather_data,
            on=['date', 'district'],
            how='inner'
        )
        
        if not merged_data.empty:
            # Group by district and calculate average duration
            district_duration = merged_data.groupby(['district', 'storm_event'])['duration_hours'].mean().reset_index()
            
            # Create bar chart
            fig = px.bar(
                district_duration,
                x='district',
                y='duration_hours',
                color='storm_event',
                labels={
                    'district': 'District',
                    'duration_hours': 'Average Outage Duration (hours)',
                    'storm_event': 'During Storm'
                },
                title='Average Outage Duration by District'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate correlation statistics
            st.subheader("Weather Factor Correlation with Outage Duration")
            
            # Calculate correlations
            correlation_temp = merged_data['temperature_c'].corr(merged_data['duration_hours'])
            correlation_precip = merged_data['precipitation_mm'].corr(merged_data['duration_hours'])
            correlation_wind = merged_data['wind_speed_kmh'].corr(merged_data['duration_hours'])
            correlation_humidity = merged_data['humidity_pct'].corr(merged_data['duration_hours'])
            correlation_snow = merged_data['snow_cm'].corr(merged_data['duration_hours'])
            
            # Display correlations
            corr_data = {
                'Weather Factor': ['Temperature', 'Precipitation', 'Wind Speed', 'Humidity', 'Snow'],
                'Correlation with Outage Duration': [
                    correlation_temp,
                    correlation_precip,
                    correlation_wind,
                    correlation_humidity,
                    correlation_snow
                ]
            }
            
            corr_df = pd.DataFrame(corr_data)
            
            # Create bar chart
            fig = px.bar(
                corr_df,
                x='Weather Factor',
                y='Correlation with Outage Duration',
                color='Correlation with Outage Duration',
                labels={
                    'Correlation with Outage Duration': 'Correlation Coefficient'
                },
                title='Weather Factors Correlation with Outage Duration'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("""
            **Interpretation Guide:**
            - Values close to 1 indicate a strong positive correlation (as the weather factor increases, outage duration tends to increase)
            - Values close to -1 indicate a strong negative correlation (as the weather factor increases, outage duration tends to decrease)
            - Values close to 0 indicate little to no correlation
            """)
        else:
            st.write("Insufficient data for district analysis.")
