import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from models.load_balancer import GridModel
from utils.visualization import plot_grid_map, plot_disaster_scenario_results
from utils.llm_integration import AIXplainLLMService

def show():
    st.title("Disaster Response Planning")
    
    # Load data from session state
    grid_data = st.session_state.grid_data
    weather_data = st.session_state.weather_data
    
    # Initialize grid model if not already done
    if 'grid_model' not in st.session_state:
        st.session_state.grid_model = GridModel(grid_data)
    
    # Initialize LLM service
    llm_service = AIXplainLLMService()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Disaster Scenario Simulation", "Resilience Assessment"])
    
    with tab1:
        st.subheader("Simulate Disaster Scenarios")
        
        # Scenario configuration form
        with st.form("disaster_scenario_form"):
            st.write("### Scenario Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Scenario type
                scenario_type = st.selectbox(
                    "Disaster Type",
                    ["flooding", "earthquake", "landslide", "snowstorm", "wildfire", "extreme heat"]
                )
                
                # Severity
                severity = st.select_slider(
                    "Severity Level",
                    options=["mild", "moderate", "severe"],
                    value="moderate"
                )
            
            with col2:
                # Affected districts
                districts = sorted(grid_data['substations']['district'].unique().tolist())
                
                # Select all districts checkbox
                all_districts = st.checkbox("All Districts", value=False)
                
                if all_districts:
                    affected_districts = districts
                    st.write("All districts selected")
                else:
                    affected_districts = st.multiselect(
                        "Affected Districts",
                        options=districts,
                        default=[districts[0]]
                    )
            
            # Additional scenario parameters based on type
            if scenario_type == "flooding":
                st.write("#### Flooding Parameters")
                flood_level = st.slider("Flood Level (meters)", 0.5, 10.0, 2.0, 0.5)
                flood_duration = st.slider("Flood Duration (days)", 1, 14, 3)
            
            elif scenario_type == "earthquake":
                st.write("#### Earthquake Parameters")
                magnitude = st.slider("Magnitude (Richter scale)", 4.0, 9.0, 6.0, 0.1)
                epicenter_district = st.selectbox("Epicenter District", districts)
            
            elif scenario_type == "snowstorm":
                st.write("#### Snowstorm Parameters")
                snow_accumulation = st.slider("Snow Accumulation (cm)", 10, 200, 50, 10)
                temperature = st.slider("Temperature (°C)", -30, 0, -10, 1)
            
            submitted = st.form_submit_button("Run Simulation")
        
        # Run simulation when form is submitted
        if submitted:
            with st.spinner(f"Simulating {severity} {scenario_type} scenario..."):
                # Run the simulation
                results = st.session_state.grid_model.disaster_scenario_simulation(
                    scenario_type=scenario_type,
                    affected_districts=affected_districts,
                    severity=severity
                )
            
            # Display results
            st.subheader("Simulation Results")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Impacted Substations", len(results['impacted_substations']))
            with col2:
                st.metric("Impacted Lines", len(results['impacted_lines']))
            with col3:
                if 'resilience_metrics' in results:
                    st.metric("Impact Severity", f"{results['resilience_metrics']['impact_severity']:.1f}%")
            
            # Display map with impacted components
            st.write("### Projected Impact Map")
            
            # Create a list of impacted component IDs
            impacted_components = [sub['id'] for sub in results['impacted_substations']] + \
                                 [line['id'] for line in results['impacted_lines']]
            
            # Create outage data for visualization
            outage_data = pd.DataFrame([
                {'component_type': 'substation' if comp_id.startswith('SUB-') else 'line',
                 'component_id': comp_id}
                for comp_id in impacted_components
            ])
            
            # Display map
            m = plot_grid_map(grid_data, outage_data)
            from streamlit_folium import folium_static
            folium_static(m, width=800, height=500)
            
            # Display resilience metrics and impact distribution
            st.write("### Impact Assessment")
            
            # Visualize impact metrics
            fig_metrics, fig_impact = plot_disaster_scenario_results(results)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if fig_metrics:
                    st.plotly_chart(fig_metrics, use_container_width=True)
                
                # Display impacted substations
                if results['impacted_substations']:
                    st.write("#### Critical Impacted Substations")
                    
                    # Sort by capacity
                    critical_subs = sorted(
                        results['impacted_substations'],
                        key=lambda x: x.get('capacity_mw', 0),
                        reverse=True
                    )[:5]  # Top 5
                    
                    critical_subs_df = pd.DataFrame({
                        'Substation ID': [sub['id'] for sub in critical_subs],
                        'District': [sub['district'] for sub in critical_subs],
                        'Capacity (MW)': [sub['capacity_mw'] for sub in critical_subs]
                    })
                    st.dataframe(critical_subs_df, use_container_width=True)
            
            with col2:
                if fig_impact:
                    st.plotly_chart(fig_impact, use_container_width=True)
                
                # Display load balance issues
                if 'load_balance_results' in results and results['load_balance_results']['overloaded_components']:
                    st.write("#### Overloaded Components After Disaster")
                    
                    overload_df = pd.DataFrame([
                        {
                            'Component ID': comp['component_id'],
                            'Load (%)': f"{comp['load_percentage']:.1f}%",
                            'Capacity (MW)': comp['capacity_mw']
                        }
                        for comp in results['load_balance_results']['overloaded_components']
                    ])
                    st.dataframe(overload_df, use_container_width=True)
            
            # Display recommendations
            st.subheader("System Recommendations")
            if 'recommendations' in results and results['recommendations']:
                # Group recommendations by type
                rec_types = {}
                for rec in results['recommendations']:
                    rec_type = rec.get('type', 'other')
                    if rec_type not in rec_types:
                        rec_types[rec_type] = []
                    rec_types[rec_type].append(rec)
                
                # Display by type with appropriate styling
                if 'restoration_plan' in rec_types:
                    st.write("#### Restoration Priority Plan")
                    for rec in rec_types['restoration_plan']:
                        st.write(rec['message'])
                        if 'components' in rec:
                            for i, component in enumerate(rec['components']):
                                priority_color = {
                                    'high': 'red',
                                    'medium': 'orange',
                                    'low': 'blue'
                                }.get(component['priority'], 'black')
                                
                                st.markdown(
                                    f"<span style='color:{priority_color}'>{i+1}. "
                                    f"{component['id']} ({component['type']}) - {component['reason']}</span>",
                                    unsafe_allow_html=True
                                )
                
                if 'emergency_power' in rec_types:
                    st.write("#### Emergency Power Deployment")
                    for rec in rec_types['emergency_power']:
                        st.warning(rec['message'])
                
                if 'load_shedding' in rec_types:
                    st.write("#### Load Shedding Plan")
                    for rec in rec_types['load_shedding']:
                        st.error(rec['message'])
                
                if 'scenario_specific' in rec_types:
                    st.write("#### Scenario-Specific Actions")
                    for rec in rec_types['scenario_specific']:
                        st.info(rec['message'])
                
                if 'safety' in rec_types:
                    st.write("#### Safety Measures")
                    for rec in rec_types['safety']:
                        st.success(rec['message'])
            else:
                st.write("No specific recommendations generated.")
            
            # Get LLM recommendation
            with st.spinner("Generating AI recommendation..."):
                # Prepare context for LLM
                context = {
                    'scenario_type': scenario_type,
                    'severity': severity,
                    'affected_districts': affected_districts,
                    'resilience_metrics': results.get('resilience_metrics', {}),
                    'impacted_substations': results.get('impacted_substations', []),
                    'impacted_lines': results.get('impacted_lines', []),
                    'recommendations': results.get('recommendations', [])
                }
                
                recommendation = llm_service.generate_recommendation(
                    context=context,
                    query_type='disaster'
                )
            
            # Display recommendation
            st.subheader("AI Recommendation")
            st.info(recommendation)
    
    with tab2:
        st.subheader("Grid Resilience Assessment")
        
        # General resilience metrics
        st.write("### Overall Grid Resilience Metrics")
        
        # Get the grid graph
        G = st.session_state.grid_model.get_graph()
        
        # Calculate resilience metrics
        with st.spinner("Calculating grid resilience metrics..."):
            # Network connectivity metrics
            avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
            if nx.is_connected(G):
                avg_path_length = nx.average_shortest_path_length(G)
                diameter = nx.diameter(G)
                connected = "Yes"
            else:
                avg_path_length = float('inf')
                diameter = float('inf')
                connected = "No"
            
            # Redundancy metrics
            edge_connectivity = nx.edge_connectivity(G) if connected == "Yes" else 0
            node_connectivity = nx.node_connectivity(G) if connected == "Yes" else 0
            
            # Component age and health
            substations = grid_data['substations']
            lines = grid_data['transmission_lines']
            
            avg_substation_age = 2023 - substations['year_commissioned'].mean()
            avg_line_age = 2023 - lines['year_commissioned'].mean()
            
            avg_substation_health = substations['health_index'].mean()
            avg_line_health = lines['health_index'].mean()
            
            # Create metrics dataframe
            metrics_data = {
                'Metric': [
                    'Connected Graph', 'Average Node Degree', 'Average Path Length', 
                    'Network Diameter', 'Edge Connectivity', 'Node Connectivity',
                    'Average Substation Age (years)', 'Average Line Age (years)',
                    'Average Substation Health Index', 'Average Line Health Index'
                ],
                'Value': [
                    connected, f"{avg_degree:.2f}", f"{avg_path_length:.2f}" if avg_path_length != float('inf') else "N/A",
                    f"{diameter}" if diameter != float('inf') else "N/A", f"{edge_connectivity}", f"{node_connectivity}",
                    f"{avg_substation_age:.1f}", f"{avg_line_age:.1f}",
                    f"{avg_substation_health:.2f}", f"{avg_line_health:.2f}"
                ]
            }
            
            metrics_df = pd.DataFrame(metrics_data)
        
        # Display metrics
        st.dataframe(metrics_df, use_container_width=True)
        
        st.write("""
        **Interpretation:**
        - **Connected Graph**: Whether all nodes in the grid can reach each other
        - **Average Node Degree**: Average number of connections per substation
        - **Average Path Length**: Average number of steps to get from one node to another
        - **Network Diameter**: Maximum distance between any pair of nodes
        - **Edge/Node Connectivity**: Minimum number of edges/nodes that need to be removed to disconnect the graph
        - **Health Indices**: Measure of component condition (0-1, higher is better)
        """)
        
        # Vulnerability assessment
        st.write("### Vulnerability Assessment")
        
        # Critical component analysis
        critical_districts = []
        district_vulnerability = {}
        
        for district in grid_data['substations']['district'].unique():
            # Count components in district
            subs_in_district = grid_data['substations'][grid_data['substations']['district'] == district]
            
            # Get average health
            avg_health = subs_in_district['health_index'].mean()
            
            # Get average age
            avg_age = 2023 - subs_in_district['year_commissioned'].mean()
            
            # Calculate total capacity
            total_capacity = subs_in_district['capacity_mw'].sum()
            
            # Calculate vulnerability score (higher = more vulnerable)
            vulnerability = (
                (1 - avg_health) * 0.4 +  # Lower health = higher vulnerability
                min(1, avg_age / 40) * 0.3 +  # Older age = higher vulnerability
                min(1, 200 / max(1, total_capacity)) * 0.3  # Lower capacity = higher vulnerability
            )
            
            district_vulnerability[district] = {
                'vulnerability_score': vulnerability,
                'substation_count': len(subs_in_district),
                'avg_health': avg_health,
                'avg_age': avg_age,
                'total_capacity_mw': total_capacity
            }
            
            if vulnerability > 0.6:
                critical_districts.append(district)
        
        # Create vulnerability dataframe
        vulnerability_data = []
        for district, data in district_vulnerability.items():
            vulnerability_data.append({
                'District': district,
                'Vulnerability Score': data['vulnerability_score'],
                'Substation Count': data['substation_count'],
                'Avg Health Index': data['avg_health'],
                'Avg Age (years)': data['avg_age'],
                'Total Capacity (MW)': data['total_capacity_mw'],
            })
        
        vulnerability_df = pd.DataFrame(vulnerability_data)
        vulnerability_df = vulnerability_df.sort_values('Vulnerability Score', ascending=False)
        
        # Plot vulnerability by district
        fig = px.bar(
            vulnerability_df,
            x='District',
            y='Vulnerability Score',
            color='Vulnerability Score',
            hover_data=['Substation Count', 'Avg Health Index', 'Total Capacity (MW)'],
            title='District Vulnerability Assessment',
            color_continuous_scale='RdYlGn_r'  # Red for high vulnerability, green for low
        )
        
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Highlight critical districts
        if critical_districts:
            st.warning(f"Critical districts with high vulnerability: {', '.join(critical_districts)}")
        
        # Recommended preparedness actions
        st.subheader("Recommended Preparedness Actions")
        
        # General preparedness recommendations
        general_rec = [
            "**1. Infrastructure Upgrades**: Prioritize maintenance for components with health index below 0.8",
            "**2. Backup Systems**: Install backup generators at critical substations",
            "**3. Communication Systems**: Ensure robust emergency communication channels",
            "**4. Vegetation Management**: Regular clearing around transmission lines",
            "**5. Training**: Regular disaster response drills for personnel"
        ]
        
        for rec in general_rec:
            st.write(rec)
        
        # District-specific recommendations
        if critical_districts:
            st.write("### District-Specific Recommendations")
            
            for district in critical_districts[:3]:  # Show top 3 most critical
                district_data = district_vulnerability[district]
                
                st.markdown(f"#### {district}")
                
                if district_data['avg_health'] < 0.8:
                    st.write("- **Priority Maintenance**: Improve component health index through targeted maintenance")
                
                if district_data['avg_age'] > 30:
                    st.write("- **Equipment Upgrades**: Replace aging infrastructure with modern components")
                
                if district_data['total_capacity_mw'] < 150:
                    st.write("- **Capacity Enhancement**: Increase capacity or add redundant power sources")
                
                # Weather-related recommendations
                district_weather = weather_data[weather_data['district'] == district].sort_values('date').tail(30)
                
                if district_weather['precipitation_mm'].mean() > 20:
                    st.write("- **Flood Protection**: Enhance flood protection measures at substations")
                
                if district_weather['wind_speed_kmh'].max() > 40:
                    st.write("- **Wind Resistance**: Reinforce transmission towers for high winds")
                
                if district_weather['snow_cm'].max() > 10:
                    st.write("- **Snow Clearance**: Ensure snow clearing equipment is available")
        
        # Document recommendations with LLM
        st.subheader("Generate Comprehensive Preparedness Plan")
        
        selected_district = st.selectbox(
            "Select District for Detailed Plan",
            options=sorted(grid_data['substations']['district'].unique())
        )
        
        if st.button("Generate Plan"):
            with st.spinner("Generating comprehensive preparedness plan..."):
                # Get district-specific data
                district_info = district_vulnerability.get(selected_district, {})
                
                district_substations = grid_data['substations'][grid_data['substations']['district'] == selected_district]
                
                district_lines = []
                for _, line in grid_data['transmission_lines'].iterrows():
                    from_sub = grid_data['substations'][grid_data['substations']['id'] == line['from_substation']]
                    to_sub = grid_data['substations'][grid_data['substations']['id'] == line['to_substation']]
                    
                    if not from_sub.empty and not to_sub.empty:
                        if from_sub.iloc[0]['district'] == selected_district or to_sub.iloc[0]['district'] == selected_district:
                            district_lines.append(line)
                
                # Get weather patterns
                district_weather = weather_data[weather_data['district'] == selected_district].sort_values('date')
                
                has_storms = district_weather['storm_event'].mean() > 0.1
                has_snow = district_weather['snow_cm'].max() > 5
                has_heavy_rain = district_weather['precipitation_mm'].max() > 30
                has_high_winds = district_weather['wind_speed_kmh'].max() > 40
                
                # Prepare context for LLM
                context = {
                    'scenario_type': 'preparedness',
                    'district': selected_district,
                    'vulnerability_score': district_info.get('vulnerability_score', 0.5),
                    'substation_count': district_info.get('substation_count', 0),
                    'avg_health': district_info.get('avg_health', 0),
                    'avg_age': district_info.get('avg_age', 0),
                    'total_capacity_mw': district_info.get('total_capacity_mw', 0),
                    'weather_risks': {
                        'storms': has_storms,
                        'snow': has_snow,
                        'heavy_rain': has_heavy_rain,
                        'high_winds': has_high_winds
                    }
                }
                
                # Get LLM recommendation
                recommendation = llm_service.generate_recommendation(
                    context=context,
                    query_type='disaster'
                )
            
            # Display recommendation
            st.info(recommendation)
            
            # Option to download as PDF (placeholder - would need additional libraries)
            st.download_button(
                label="Download Plan as PDF",
                data="This would be a PDF in a real implementation",
                file_name=f"{selected_district}_disaster_preparedness_plan.pdf",
                mime="application/pdf",
                disabled=True
            )
            st.caption("Note: PDF download functionality would be implemented in a production system")
