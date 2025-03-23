import pandas as pd
import numpy as np
from collections import defaultdict, deque
import networkx as nx
import matplotlib.pyplot as plt

class GridModel:
    def __init__(self, grid_data):
        """Initialize the grid model with substations and transmission lines"""
        self.substations = grid_data['substations'].copy()
        self.transmission_lines = grid_data['transmission_lines'].copy()
        self.graph = self._build_grid_graph()
        
    def _build_grid_graph(self):
        """Build a network graph of the grid"""
        G = nx.Graph()
        
        # Add substations as nodes
        for _, substation in self.substations.iterrows():
            G.add_node(substation['id'], 
                       type='substation',
                       capacity=substation['capacity_mw'],
                       health=substation['health_index'],
                       district=substation['district'],
                       pos=(substation['longitude'], substation['latitude']))
        
        # Add transmission lines as edges
        for _, line in self.transmission_lines.iterrows():
            G.add_edge(line['from_substation'], 
                       line['to_substation'],
                       id=line['id'],
                       capacity=line['capacity_mw'],
                       load=line['current_load_pct'] / 100.0 * line['capacity_mw'],
                       health=line['health_index'],
                       length=line['length_km'])
        
        return G

    def get_graph(self):
        """Return the grid graph"""
        return self.graph

    def load_balancing_simulation(self, failed_components=None, demand_changes=None):
        """
        Simulate load balancing across the grid when components fail or demand changes
        
        Parameters:
        - failed_components: list of component IDs that are out of service
        - demand_changes: dictionary mapping substation IDs to demand change in MW
        
        Returns:
        - Status of each component after load balancing
        - Overloaded components
        - Recommended actions
        """
        # Create a copy of the graph to work with
        G = self.graph.copy()
        
        # Remove failed components
        if failed_components:
            for component_id in failed_components:
                # Check if it's a substation (node)
                if component_id in G.nodes():
                    G.remove_node(component_id)
                # Check if it's a transmission line
                else:
                    # Find the edge with this ID
                    for u, v, data in G.edges(data=True):
                        if data.get('id') == component_id:
                            G.remove_edge(u, v)
                            break
        
        # Apply demand changes
        if demand_changes:
            for substation_id, demand_change in demand_changes.items():
                if substation_id in G.nodes():
                    # For simplicity, we represent demand changes as load on incoming lines
                    for neighbor in G.neighbors(substation_id):
                        edge_data = G.get_edge_data(substation_id, neighbor)
                        # Distribute the demand change among connected lines
                        edge_data['load'] += demand_change / G.degree(substation_id)
        
        # Now calculate the new load distribution
        # This is a simplified DC power flow approximation
        overloaded_components = []
        line_status = {}
        
        # Check line loads
        for u, v, data in G.edges(data=True):
            current_load = data['load']
            capacity = data['capacity']
            load_pct = current_load / capacity * 100
            
            line_status[data['id']] = {
                'from_substation': u,
                'to_substation': v,
                'current_load_mw': current_load,
                'capacity_mw': capacity,
                'load_percentage': load_pct,
                'status': 'Normal' if load_pct < 80 else ('Warning' if load_pct < 100 else 'Overloaded')
            }
            
            if load_pct >= 100:
                overloaded_components.append({
                    'component_id': data['id'],
                    'type': 'transmission_line',
                    'load_percentage': load_pct,
                    'capacity_mw': capacity
                })
        
        # Generate recommendations based on the simulation results
        recommendations = self._generate_load_balancing_recommendations(G, overloaded_components, line_status)
        
        return {
            'line_status': line_status,
            'overloaded_components': overloaded_components,
            'recommendations': recommendations
        }
    
    def _generate_load_balancing_recommendations(self, G, overloaded_components, line_status):
        """Generate recommendations to address overloaded components"""
        recommendations = []
        
        if not overloaded_components:
            recommendations.append({
                'type': 'info',
                'message': 'All grid components are operating within capacity limits.'
            })
            return recommendations
        
        # For each overloaded component, find alternative routing
        for component in overloaded_components:
            if component['type'] == 'transmission_line':
                # Get the line data
                line_id = component['component_id']
                line_data = None
                for line_id_key, data in line_status.items():
                    if line_id_key == line_id:
                        line_data = data
                        break
                
                if line_data:
                    from_sub = line_data['from_substation']
                    to_sub = line_data['to_substation']
                    
                    # Find alternative paths
                    try:
                        # Remove the overloaded line temporarily
                        G.remove_edge(from_sub, to_sub)
                        
                        # Check if an alternative path exists
                        if nx.has_path(G, from_sub, to_sub):
                            alt_path = nx.shortest_path(G, from_sub, to_sub)
                            
                            # Create the recommendation
                            rec = {
                                'type': 'rerouting',
                                'component_id': line_id,
                                'message': f"Reroute power from {from_sub} to {to_sub} via: {' -> '.join(alt_path)}",
                                'alternative_path': alt_path
                            }
                            recommendations.append(rec)
                        else:
                            # No alternative path
                            rec = {
                                'type': 'critical',
                                'component_id': line_id,
                                'message': f"No alternative path exists between {from_sub} and {to_sub}. Urgent load reduction required."
                            }
                            recommendations.append(rec)
                        
                        # Restore the edge for further analysis
                        G.add_edge(from_sub, to_sub, **self.graph.get_edge_data(from_sub, to_sub))
                    
                    except nx.NetworkXNoPath:
                        # No path exists
                        rec = {
                            'type': 'critical',
                            'component_id': line_id,
                            'message': f"No alternative path exists between {from_sub} and {to_sub}. Urgent load reduction required."
                        }
                        recommendations.append(rec)
                    
                    # Add load reduction recommendation
                    overload_pct = component['load_percentage'] - 100
                    reduction_needed = (overload_pct / 100) * component['capacity_mw']
                    
                    rec = {
                        'type': 'load_reduction',
                        'component_id': line_id,
                        'message': f"Reduce load on line {line_id} by at least {reduction_needed:.2f} MW (current overload: {overload_pct:.1f}%)",
                        'reduction_mw': reduction_needed
                    }
                    recommendations.append(rec)
        
        return recommendations
    
    def disaster_scenario_simulation(self, scenario_type, affected_districts=None, severity='moderate'):
        """
        Simulate the impact of a disaster scenario on the grid
        
        Parameters:
        - scenario_type: Type of disaster ('flooding', 'earthquake', 'landslide', 'snowstorm', etc.)
        - affected_districts: List of affected districts
        - severity: Severity level ('mild', 'moderate', 'severe')
        
        Returns:
        - Impacted components
        - Grid resilience metrics
        - Recommended actions
        """
        # Set probability of component failure based on severity
        if severity == 'mild':
            substation_failure_prob = 0.1
            line_failure_prob = 0.2
        elif severity == 'moderate':
            substation_failure_prob = 0.3
            line_failure_prob = 0.4
        else:  # severe
            substation_failure_prob = 0.6
            line_failure_prob = 0.7
        
        # Additional modifiers based on scenario type
        if scenario_type == 'flooding':
            substation_failure_prob += 0.1
        elif scenario_type == 'earthquake':
            substation_failure_prob += 0.2
            line_failure_prob += 0.1
        elif scenario_type == 'landslide':
            line_failure_prob += 0.2
        elif scenario_type == 'snowstorm':
            line_failure_prob += 0.3
        
        # Identify potentially impacted components
        impacted_substations = []
        impacted_lines = []
        
        # Check substations in affected districts
        for _, substation in self.substations.iterrows():
            if affected_districts is None or substation['district'] in affected_districts:
                # Calculate failure probability, factoring in health index
                failure_prob = substation_failure_prob * (1.2 - substation['health_index'])
                
                if np.random.random() < failure_prob:
                    impacted_substations.append({
                        'id': substation['id'],
                        'name': substation['name'],
                        'district': substation['district'],
                        'capacity_mw': substation['capacity_mw'],
                        'failure_probability': failure_prob
                    })
        
        # Check lines connected to affected districts
        for _, line in self.transmission_lines.iterrows():
            # Get the substations at each end of the line
            from_sub_id = line['from_substation']
            to_sub_id = line['to_substation']
            
            from_sub = self.substations[self.substations['id'] == from_sub_id].iloc[0]
            to_sub = self.substations[self.substations['id'] == to_sub_id].iloc[0]
            
            # Check if either substation is in affected districts
            if (affected_districts is None or 
                from_sub['district'] in affected_districts or 
                to_sub['district'] in affected_districts):
                
                # Calculate failure probability, factoring in health index and length
                # Longer lines are more vulnerable
                length_factor = min(1.5, 1 + (line['length_km'] / 100))
                failure_prob = line_failure_prob * (1.2 - line['health_index']) * length_factor
                
                if np.random.random() < failure_prob:
                    impacted_lines.append({
                        'id': line['id'],
                        'from_substation': from_sub_id,
                        'to_substation': to_sub_id,
                        'capacity_mw': line['capacity_mw'],
                        'length_km': line['length_km'],
                        'failure_probability': failure_prob
                    })
        
        # Simulate load balancing with failed components
        failed_components = [sub['id'] for sub in impacted_substations] + [line['id'] for line in impacted_lines]
        load_balance_results = self.load_balancing_simulation(failed_components=failed_components)
        
        # Calculate grid resilience metrics
        connected_components = list(nx.connected_components(self.graph))
        
        # Create a graph with failed components removed
        G_after = self.graph.copy()
        for component_id in failed_components:
            if component_id in G_after.nodes():
                G_after.remove_node(component_id)
            else:
                # Find the edge with this ID
                for u, v, data in list(G_after.edges(data=True)):
                    if data.get('id') == component_id:
                        G_after.remove_edge(u, v)
                        break
        
        connected_components_after = list(nx.connected_components(G_after))
        
        # Fragmentation: increase in number of disconnected subgraphs
        fragmentation = len(connected_components_after) - len(connected_components)
        
        # Connectivity loss: percentage of nodes that can no longer communicate
        if len(self.graph.nodes()) > 0:
            connectivity_loss = (1 - (len(G_after.nodes()) / len(self.graph.nodes()))) * 100
        else:
            connectivity_loss = 0
        
        # Impact severity: percentage of total capacity affected
        total_capacity = sum(self.substations['capacity_mw'])
        impacted_capacity = sum(sub['capacity_mw'] for sub in impacted_substations)
        
        if total_capacity > 0:
            impact_severity = (impacted_capacity / total_capacity) * 100
        else:
            impact_severity = 0
        
        # Generate disaster response recommendations
        recommendations = self._generate_disaster_response_recommendations(
            scenario_type, 
            impacted_substations, 
            impacted_lines, 
            load_balance_results
        )
        
        return {
            'impacted_substations': impacted_substations,
            'impacted_lines': impacted_lines,
            'load_balance_results': load_balance_results,
            'resilience_metrics': {
                'fragmentation': fragmentation,
                'connectivity_loss': connectivity_loss,
                'impact_severity': impact_severity
            },
            'recommendations': recommendations
        }
    
    def _generate_disaster_response_recommendations(self, scenario_type, impacted_substations, impacted_lines, load_balance_results):
        """Generate recommendations for disaster response"""
        recommendations = []
        
        # Prioritize components for restoration
        critical_components = []
        
        # Add overloaded components as critical
        for comp in load_balance_results['overloaded_components']:
            critical_components.append({
                'id': comp['component_id'],
                'type': 'transmission_line',
                'priority': 'high',
                'reason': f"Overloaded at {comp['load_percentage']:.1f}% capacity"
            })
        
        # Assess criticality of impacted substations
        for sub in impacted_substations:
            # Check how many connections this substation has
            connections = sum(1 for _, line in self.transmission_lines.iterrows() 
                            if line['from_substation'] == sub['id'] or line['to_substation'] == sub['id'])
            
            priority = 'medium'
            if sub['capacity_mw'] > 200 or connections > 3:
                priority = 'high'
            elif sub['capacity_mw'] < 50 and connections <= 1:
                priority = 'low'
            
            critical_components.append({
                'id': sub['id'],
                'type': 'substation',
                'priority': priority,
                'capacity_mw': sub['capacity_mw'],
                'connections': connections,
                'reason': f"Critical infrastructure with {connections} connections and {sub['capacity_mw']} MW capacity"
            })
        
        # Prioritize high-capacity lines
        for line in impacted_lines:
            priority = 'medium'
            if line['capacity_mw'] > 300:
                priority = 'high'
            elif line['capacity_mw'] < 100:
                priority = 'low'
            
            critical_components.append({
                'id': line['id'],
                'type': 'transmission_line',
                'priority': priority,
                'capacity_mw': line['capacity_mw'],
                'reason': f"Transmission line with {line['capacity_mw']} MW capacity"
            })
        
        # Sort by priority
        critical_components.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']])
        
        # Generate restoration plan
        if critical_components:
            recommendations.append({
                'type': 'restoration_plan',
                'message': f"Critical Component Restoration Priority for {scenario_type} scenario:",
                'components': critical_components[:10]  # Top 10 most critical
            })
        
        # Emergency power recommendations
        affected_districts = set([sub['district'] for sub in impacted_substations])
        if affected_districts:
            recommendations.append({
                'type': 'emergency_power',
                'message': f"Deploy mobile generators to affected districts: {', '.join(affected_districts)}",
                'districts': list(affected_districts)
            })
        
        # Load shedding recommendations if necessary
        if load_balance_results['overloaded_components']:
            recommendations.append({
                'type': 'load_shedding',
                'message': "Implement controlled load shedding in non-critical areas to reduce grid stress",
                'overloaded_count': len(load_balance_results['overloaded_components'])
            })
        
        # Specific scenario recommendations
        if scenario_type == 'flooding':
            recommendations.append({
                'type': 'scenario_specific',
                'message': "Ensure all operational substations have flood protection barriers and pumps ready"
            })
        elif scenario_type == 'earthquake':
            recommendations.append({
                'type': 'scenario_specific',
                'message': "Conduct structural assessments of all towers and substations in the affected area before re-energizing"
            })
        elif scenario_type == 'landslide':
            recommendations.append({
                'type': 'scenario_specific',
                'message': "Monitor transmission towers on hillsides for stability issues and potential landslide warning signs"
            })
        elif scenario_type == 'snowstorm':
            recommendations.append({
                'type': 'scenario_specific',
                'message': "Deploy crews to clear snow from critical substations and check transmission lines for snow/ice loading"
            })
        
        # Safety measures
        recommendations.append({
            'type': 'safety',
            'message': "Ensure all field crews have proper PPE and emergency communication equipment before deployment"
        })
        
        return recommendations
