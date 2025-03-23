import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from models.load_balancer import GridModel
from utils.visualization import plot_grid_map, plot_load_balance_results
from utils.llm_integration import AIXplainLLMService

def show():
    st.title("Load Balancing & Rerouting Simulation")
    
    # Load data from session state
    grid_data = st.session_state.grid_data
    
    # Initialize grid model if not already done
    if 'grid_model' not in st.session_state:
        st.session_state.grid_model = GridModel(grid_data)
    
    # Initialize LLM service
    llm_service = AIXplainLLMService()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Load Balancing Simulation", "Grid Network Analysis"])
    
    with tab1:
        st.subheader("Simulate Load Balancing Scenarios")
        
        # Simulation parameters
        with st.form("load_balancing_form"):
            st.write("### Scenario Configuration")
            
            # Failed components selection
            st.write("#### Select Failed Components")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Substation failures
                st.write("Substations")
                substation_failures = []
                for _, substation in grid_data['substations'].iterrows():
                    if st.checkbox(f"{substation['name']} ({substation['id']})", value=False, key=f"sub_{substation['id']}"):
                        substation_failures.append(substation['id'])
            
            with col2:
                # Line failures
                st.write("Transmission Lines")
                line_failures = []
                for _, line in grid_data['transmission_lines'].iloc[:15].iterrows():  # Limit display to first 15 for UI clarity
                    from_sub = grid_data['substations'][grid_data['substations']['id'] == line['from_substation']]['name'].iloc[0]
                    to_sub = grid_data['substations'][grid_data['substations']['id'] == line['to_substation']]['name'].iloc[0]
                    if st.checkbox(f"{from_sub} to {to_sub} ({line['id']})", value=False, key=f"line_{line['id']}"):
                        line_failures.append(line['id'])
            
            # Demand changes
            st.write("#### Demand Changes")
            st.write("Adjust load at specific substations (in MW)")
            
            demand_changes = {}
            demand_change_count = st.number_input("Number of demand changes", min_value=0, max_value=5, value=1)
            
            for i in range(demand_change_count):
                col1, col2 = st.columns(2)
                with col1:
                    substation_options = grid_data['substations']['id'].tolist()
                    substation_names = grid_data['substations']['name'].tolist()
                    substation_display = [f"{id} ({name})" for id, name in zip(substation_options, substation_names)]
                    
                    sub_idx = st.selectbox(
                        f"Substation {i+1}",
                        options=range(len(substation_options)),
                        format_func=lambda x: substation_display[x],
                        key=f"demand_sub_{i}"
                    )
                    selected_sub = substation_options[sub_idx]
                
                with col2:
                    change_value = st.number_input(
                        f"Change in MW",
                        min_value=-100.0,
                        max_value=100.0,
                        value=0.0,
                        step=5.0,
                        key=f"demand_change_{i}"
                    )
                    
                    if change_value != 0:
                        demand_changes[selected_sub] = change_value
            
            submitted = st.form_submit_button("Run Simulation")
        
        # Run simulation when form is submitted
        if submitted:
            # Combine failed components
            failed_components = substation_failures + line_failures
            
            with st.spinner("Running load balancing simulation..."):
                # Run the simulation
                results = st.session_state.grid_model.load_balancing_simulation(
                    failed_components=failed_components,
                    demand_changes=demand_changes
                )
            
            # Display results
            st.subheader("Simulation Results")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Failed Components", len(failed_components))
            with col2:
                st.metric("Overloaded Lines", len(results['overloaded_components']))
            with col3:
                st.metric("Demand Changes", len(demand_changes))
            
            # Visualization of load balance
            st.write("### Load Distribution")
            load_balance_fig = plot_load_balance_results(results)
            if load_balance_fig:
                st.plotly_chart(load_balance_fig, use_container_width=True)
            
            # Display map with updated status
            st.write("### Grid Status After Simulation")
            
            # Create a risk score dictionary for visualization
            risk_scores = {}
            for line_id, line_data in results['line_status'].items():
                load_pct = line_data['load_percentage']
                
                # Convert load percentage to a risk score (0-1)
                if load_pct >= 100:
                    risk_scores[line_id] = 1.0  # Overloaded
                elif load_pct >= 80:
                    risk_scores[line_id] = 0.7  # Warning
                else:
                    risk_scores[line_id] = 0.3  # Normal
            
            # Add failed components with high risk
            for component_id in failed_components:
                risk_scores[component_id] = 1.0
            
            # Create outage data for visualization
            outage_data = pd.DataFrame([
                {'component_type': 'substation' if comp_id.startswith('SUB-') else 'line',
                 'component_id': comp_id}
                for comp_id in failed_components
            ])
            
            # Display map
            m = plot_grid_map(grid_data, outage_data, risk_scores)
            from streamlit_folium import folium_static
            folium_static(m, width=800, height=500)
            
            # Display recommendations
            st.subheader("System Recommendations")
            if results['recommendations']:
                for i, rec in enumerate(results['recommendations']):
                    if rec['type'] == 'critical':
                        st.error(rec['message'])
                    elif rec['type'] == 'rerouting':
                        st.warning(rec['message'])
                    elif rec['type'] == 'load_reduction':
                        st.info(rec['message'])
                    else:
                        st.write(rec['message'])
            else:
                st.write("No specific recommendations generated.")
            
            # Get LLM recommendation
            with st.spinner("Generating AI recommendation..."):
                recommendation = llm_service.generate_recommendation(
                    context=results,
                    query_type='load_balancing'
                )
            
            # Display recommendation
            st.subheader("AI Recommendation")
            st.info(recommendation)
    
    with tab2:
        st.subheader("Grid Network Analysis")
        
        # Get the grid graph
        G = st.session_state.grid_model.get_graph()
        
        # Display network statistics
        st.write("### Grid Network Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Substations", len([n for n in G.nodes() if G.nodes[n].get('type') == 'substation']))
        with col2:
            st.metric("Transmission Lines", G.number_of_edges())
        with col3:
            st.metric("Network Density", f"{nx.density(G):.4f}")
        with col4:
            try:
                st.metric("Avg. Path Length", f"{nx.average_shortest_path_length(G):.2f}")
            except nx.NetworkXError:
                st.metric("Avg. Path Length", "N/A (Disconnected)")
        
        # Calculate and display critical components
        st.write("### Critical Component Analysis")
        
        with st.spinner("Analyzing critical components..."):
            # Calculate node centrality
            centrality = nx.degree_centrality(G)
            betweenness = nx.betweenness_centrality(G)
            
            # Find top 5 critical substations
            substations = [n for n in G.nodes() if G.nodes[n].get('type') == 'substation']
            critical_substations = sorted(
                [(n, (centrality[n] + betweenness[n])/2) for n in substations],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Find critical edges (lines)
            edge_betweenness = nx.edge_betweenness_centrality(G)
            critical_lines = sorted(
                [(u, v, data.get('id'), edge_betweenness[(u, v)]) for u, v, data in G.edges(data=True)],
                key=lambda x: x[3],
                reverse=True
            )[:5]
        
        # Display critical components
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Critical Substations")
            critical_subs_df = pd.DataFrame({
                'Substation ID': [sub[0] for sub in critical_substations],
                'Criticality Score': [f"{sub[1]:.4f}" for sub in critical_substations],
                'District': [grid_data['substations'][grid_data['substations']['id'] == sub[0]]['district'].iloc[0] 
                             for sub in critical_substations]
            })
            st.dataframe(critical_subs_df, use_container_width=True)
        
        with col2:
            st.write("#### Critical Transmission Lines")
            critical_lines_df = pd.DataFrame({
                'Line ID': [line[2] for line in critical_lines],
                'From': [line[0] for line in critical_lines],
                'To': [line[1] for line in critical_lines],
                'Criticality Score': [f"{line[3]:.4f}" for line in critical_lines]
            })
            st.dataframe(critical_lines_df, use_container_width=True)
        
        # Analysis of grid resilience
        st.write("### Grid Resilience Analysis")
        
        # Calculate number of connected components
        num_components = nx.number_connected_components(G)
        
        # Simulation of random failures
        with st.spinner("Simulating random failures to assess grid resilience..."):
            failure_results = []
            num_trials = 10
            
            for i in range(1, 11):  # Test removing 1-10 random components
                disconnection_count = 0
                
                for trial in range(num_trials):
                    # Create a copy of the graph
                    G_copy = G.copy()
                    
                    # Select random nodes to remove
                    nodes_to_remove = np.random.choice(list(G_copy.nodes()), size=i, replace=False)
                    
                    # Remove nodes
                    for node in nodes_to_remove:
                        if node in G_copy:
                            G_copy.remove_node(node)
                    
                    # Check if graph is still connected
                    if nx.number_connected_components(G_copy) > num_components:
                        disconnection_count += 1
                
                failure_results.append({
                    'components_removed': i,
                    'disconnection_probability': disconnection_count / num_trials
                })
            
            failure_df = pd.DataFrame(failure_results)
        
        # Plot failure simulation results
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=failure_df['components_removed'],
            y=failure_df['disconnection_probability'],
            mode='lines+markers',
            name='Disconnection Probability'
        ))
        
        fig.update_layout(
            title='Grid Resilience to Random Failures',
            xaxis_title='Number of Components Removed',
            yaxis_title='Probability of Grid Disconnection',
            yaxis=dict(
                tickformat='.0%',
                range=[0, 1]
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("""
        **Interpretation:**
        - This chart shows how likely the grid is to become disconnected when random components fail
        - A steep curve indicates lower resilience to random failures
        - The point where the probability reaches 50% is an indicator of grid vulnerability
        """)
