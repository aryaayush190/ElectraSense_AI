import requests
import json
import os
import time
from typing import Dict, List, Any, Optional

class AIXplainLLMService:
    """Client for interacting with AIXplain's Mistral Large LLM"""
    
    def __init__(self, api_key=None):
        """Initialize the AIXplain client with API key"""
        self.api_key = api_key or os.getenv("AIXPLAIN_API_KEY", "")
        # Verify if we have a valid API key
        if not self.api_key or len(self.api_key.strip()) < 5:
            print("Warning: Invalid or missing AIXplain API key. Using fallback responses.")
            self.use_aixplain = False
        else:
            self.use_aixplain = True
            
        self.base_url = "https://api.aixplain.com/production/generate/41ebd663-9048-46f9-a2df-49e08b0572e5"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate_recommendation(self, context: Dict[str, Any], query_type: str, max_tokens: int = 512) -> str:
        """
        Generate a recommendation based on the provided context
        
        Parameters:
        - context: Dictionary containing the context data
        - query_type: Type of recommendation to generate (e.g., 'outage', 'load_balancing', 'disaster')
        - max_tokens: Maximum number of tokens to generate
        
        Returns:
        - Generated recommendation text
        """
        # If AIXplain is not configured, use fallback responses
        if not self.use_aixplain:
            return self._fallback_response(query_type, context)
            
        # Build prompt based on query type
        if query_type == 'outage':
            prompt = self._build_outage_prompt(context)
        elif query_type == 'load_balancing':
            prompt = self._build_load_balancing_prompt(context)
        elif query_type == 'disaster':
            prompt = self._build_disaster_prompt(context)
        elif query_type == 'dashboard':
            prompt = self._build_dashboard_prompt(context)
        else:
            return self._fallback_response(query_type, context)
        
        # Call the AIXplain API with retry logic
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                response = self._call_api(prompt, max_tokens)
                return response
            except Exception as e:
                print(f"Error calling AIXplain API (attempt {retry_count+1}/{max_retries+1}): {e}")
                retry_count += 1
                if retry_count <= max_retries:
                    # Wait before retrying (exponential backoff)
                    time.sleep(1 * retry_count)
                    continue
                else:
                    # All retries failed, use fallback
                    print("All API call attempts failed. Using fallback response.")
                    return self._fallback_response(query_type, context)
    
    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Call the AIXplain API with the given prompt"""
        payload = {
            "text": prompt,
            "param": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 50
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", "No recommendation available.")
            else:
                print(f"API Error: {response.status_code}, {response.text}")
                raise Exception(f"API Error: {response.status_code}")
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def _build_outage_prompt(self, context: Dict[str, Any]) -> str:
        """Build a prompt for outage prediction recommendation"""
        prompt = (
            "You are an expert power grid consultant specializing in outage management. "
            "Based on the following information about a potential power outage, "
            "provide a detailed technical recommendation for how to prepare and respond. "
            "Include specific actions that should be taken, resources that should be mobilized, "
            "and an estimated timeline.\n\n"
        )
        
        prompt += "Power grid information:\n"
        
        if 'component_type' in context:
            prompt += f"- Component type: {context.get('component_type', 'Unknown')}\n"
        if 'district' in context:
            prompt += f"- District: {context.get('district', 'Unknown')}\n"
        if 'outage_probability' in context:
            prompt += f"- Predicted outage probability: {context.get('outage_probability', 0):.2%}\n"
        if 'predicted_duration' in context:
            prompt += f"- Predicted outage duration: {context.get('predicted_duration', 0):.2f} hours\n"
        
        # Weather information
        if 'weather' in context:
            prompt += "\nWeather conditions:\n"
            weather = context['weather']
            if 'temperature_c' in weather:
                prompt += f"- Temperature: {weather.get('temperature_c', 0)}°C\n"
            if 'precipitation_mm' in weather:
                prompt += f"- Precipitation: {weather.get('precipitation_mm', 0)} mm\n"
            if 'wind_speed_kmh' in weather:
                prompt += f"- Wind speed: {weather.get('wind_speed_kmh', 0)} km/h\n"
            if 'storm_event' in weather:
                prompt += f"- Storm event: {'Yes' if weather.get('storm_event', False) else 'No'}\n"
        
        prompt += "\nProvide a detailed recommendation on how to prepare for and respond to this potential outage. Include specific actions for grid operators and emergency response teams."
        
        return prompt
    
    def _build_load_balancing_prompt(self, context: Dict[str, Any]) -> str:
        """Build a prompt for load balancing recommendation"""
        prompt = (
            "You are an expert power grid engineer specializing in load management and power flow optimization. "
            "Based on the following information about the current grid status, "
            "provide a detailed technical recommendation for optimal load balancing. "
            "Include specific technical actions, switching operations, and generation adjustments.\n\n"
        )
        
        # Add overloaded components
        if 'overloaded_components' in context and context['overloaded_components']:
            prompt += "Overloaded components:\n"
            for comp in context['overloaded_components']:
                prompt += f"- Component {comp.get('component_id', 'Unknown')}: {comp.get('load_percentage', 0):.1f}% of capacity\n"
        else:
            prompt += "No overloaded components reported.\n"
        
        # Add recommended actions from simulation
        if 'recommendations' in context and context['recommendations']:
            prompt += "\nSystem-generated recommendations:\n"
            for rec in context['recommendations']:
                prompt += f"- {rec.get('message', '')}\n"
        
        prompt += "\nBased on the above information, provide a detailed technical recommendation for optimal load balancing. Include consideration of time of day, weather conditions if relevant, and potential risks of each approach. Format your response as an actionable plan for grid operators."
        
        return prompt
    
    def _build_disaster_prompt(self, context: Dict[str, Any]) -> str:
        """Build a prompt for disaster response recommendation"""
        prompt = (
            "You are an expert in power grid disaster response planning. "
            "Based on the following information about a potential disaster scenario, "
            "provide a comprehensive emergency response plan. "
            "Include specific priorities, resource allocation recommendations, and contingency measures.\n\n"
        )
        
        # Add scenario information
        if 'scenario_type' in context:
            prompt += f"Disaster scenario: {context.get('scenario_type', 'Unknown')}\n"
        if 'severity' in context:
            prompt += f"Severity level: {context.get('severity', 'Unknown')}\n"
        if 'affected_districts' in context:
            districts = context.get('affected_districts', [])
            prompt += f"Affected districts: {', '.join(districts)}\n"
        
        # Add impact information
        if 'resilience_metrics' in context:
            metrics = context['resilience_metrics']
            prompt += "\nImpact assessment:\n"
            prompt += f"- Grid fragmentation: {metrics.get('fragmentation', 0)} new isolated segments\n"
            prompt += f"- Connectivity loss: {metrics.get('connectivity_loss', 0):.1f}%\n"
            prompt += f"- Impact severity: {metrics.get('impact_severity', 0):.1f}% of total capacity affected\n"
        
        # Add impacted components
        if 'impacted_substations' in context:
            prompt += f"\nImpacted substations: {len(context.get('impacted_substations', []))}\n"
        if 'impacted_lines' in context:
            prompt += f"Impacted transmission lines: {len(context.get('impacted_lines', []))}\n"
        
        # Add system-generated recommendations
        if 'recommendations' in context and context['recommendations']:
            prompt += "\nSystem-generated recommendations:\n"
            for rec in context['recommendations']:
                if 'message' in rec:
                    prompt += f"- {rec['message']}\n"
        
        prompt += "\nBased on the above scenario and impact assessment, provide a comprehensive emergency response plan. Include immediate actions, resource requirements, restoration priorities, and coordination recommendations with local authorities. Your plan should address both short-term emergency response and medium-term service restoration."
        
        return prompt
    
    def _build_dashboard_prompt(self, context: Dict[str, Any]) -> str:
        """Build a prompt for dashboard summary and recommendations"""
        prompt = (
            "You are an executive advisor for electricity grid operations. "
            "Based on the following current grid status information, "
            "provide a concise executive summary and key recommendations. "
            "Focus on high-priority issues and strategic insights.\n\n"
        )
        
        # Add current grid status
        if 'substations_at_risk' in context:
            prompt += f"Substations at risk: {len(context.get('substations_at_risk', []))}\n"
        if 'lines_at_risk' in context:
            prompt += f"Transmission lines at risk: {len(context.get('lines_at_risk', []))}\n"
        
        # Add weather information
        if 'weather_alerts' in context:
            prompt += f"\nWeather alerts: {len(context.get('weather_alerts', []))}\n"
            for alert in context.get('weather_alerts', []):
                if isinstance(alert, dict) and 'message' in alert:
                    prompt += f"- {alert['message']}\n"
        
        # Add current outages
        if 'active_outages' in context:
            prompt += f"\nActive outages: {len(context.get('active_outages', []))}\n"
            for outage in context.get('active_outages', [])[:3]:  # List first 3
                if isinstance(outage, dict):
                    prompt += f"- {outage.get('component_id', 'Unknown')} in {outage.get('district', 'Unknown')}\n"
        
        prompt += "\nBased on the above information, provide a concise executive summary (2-3 sentences) followed by 3-5 key strategic recommendations. Focus on major concerns and high-impact decisions that grid managers should consider."
        
        return prompt
    
    def _fallback_response(self, query_type: str, context: Dict[str, Any]) -> str:
        """Provide a fallback response when the API call fails"""
        if query_type == 'outage':
            # Extract relevant context details
            district = context.get('district', 'the affected region')
            component_type = context.get('component_type', 'power infrastructure')
            predicted_duration = context.get('predicted_duration', 4.5)
            
            # Weather context if available
            weather_context = ""
            if 'weather' in context:
                weather = context['weather']
                if weather.get('storm_event', False):
                    weather_context = "Given the ongoing storm conditions, "
                elif weather.get('precipitation_mm', 0) > 30:
                    weather_context = "With significant rainfall in the area, "
                elif weather.get('wind_speed_kmh', 0) > 35:
                    weather_context = "With high winds affecting the region, "
            
            return (
                f"🔴 OUTAGE ALERT: {district.upper()}\n\n"
                f"{weather_context}there is a significant risk of {component_type} failure in {district}. "
                f"Analysis indicates a potential outage duration of {predicted_duration:.1f}-{predicted_duration*1.5:.1f} hours if conditions worsen.\n\n"
                "⚡ RECOMMENDED ACTIONS:\n"
                "1. Deploy emergency response teams to the affected area immediately\n"
                "2. Notify all high-priority infrastructure facilities (hospitals, emergency services)\n"
                "3. Activate backup power systems for critical facilities\n"
                "4. Prepare mobile generators for rapid deployment\n"
                "5. Issue public service announcements to affected communities\n\n"
                "Monitor weather patterns closely as conditions may change rapidly. Establish hourly status updates with field teams."
            )
        elif query_type == 'load_balancing':
            # Get overloaded components if available
            overloaded_count = 0
            overloaded_examples = []
            if 'overloaded_components' in context and context['overloaded_components']:
                overloaded_count = len(context['overloaded_components'])
                for comp in context['overloaded_components'][:2]:  # Show first two examples
                    if 'component_id' in comp and 'load_percentage' in comp:
                        overloaded_examples.append(f"{comp['component_id']} ({comp['load_percentage']:.1f}%)")
            
            overloaded_text = f"Detected {overloaded_count} overloaded components" 
            if overloaded_examples:
                overloaded_text += f" including {', '.join(overloaded_examples)}"
            
            return (
                f"⚠️ LOAD BALANCING ALERT\n\n"
                f"{overloaded_text}. Current grid load distribution requires optimization to prevent potential failures.\n\n"
                "📊 LOAD MANAGEMENT STRATEGY:\n"
                "1. Redistribute excess load from critical paths to parallel circuits where available\n"
                "2. Implement 15% temporary reduction of service to pre-identified non-essential industrial consumers during peak hours (14:00-18:00)\n"
                "3. Increase generation capacity at Substation-12 and Substation-07 by 10%\n"
                "4. Reroute transmission from eastern circuit to western backup lines\n"
                "5. Deploy field engineers to monitor transmission line temperatures on all lines operating above 85% capacity\n\n"
                "Continue monitoring load distribution at 30-minute intervals. Prepare for phase 2 load shedding if conditions deteriorate."
            )
        elif query_type == 'disaster':
            scenario = context.get('scenario_type', 'disaster')
            severity = context.get('severity', 'moderate')
            affected_districts = context.get('affected_districts', [])
            
            # Customize response based on scenario type
            priority_actions = []
            if scenario.lower() == 'flooding':
                priority_actions = [
                    "Shut down vulnerable substations in flood zones prior to water reaching critical levels",
                    "Deploy water pumping equipment to protect critical infrastructure",
                    "Establish emergency power corridors from eastern generating stations"
                ]
            elif scenario.lower() == 'earthquake':
                priority_actions = [
                    "Deploy structural assessment teams to all major substations and transmission towers",
                    "Activate backup power routes avoiding areas with potential structural damage",
                    "Prepare for extended outages in mountainous regions with difficult access"
                ]
            elif scenario.lower() == 'snowstorm' or scenario.lower() == 'blizzard':
                priority_actions = [
                    "Preposition snow removal equipment at critical substations",
                    "Activate ice-load monitoring on main transmission lines",
                    "Ready emergency helicopters for line inspections once weather permits"
                ]
            else:
                # Generic disaster actions
                priority_actions = [
                    "Establish emergency coordination center at central headquarters",
                    "Deploy rapid assessment teams to affected areas",
                    "Prepare emergency power generation for critical infrastructure"
                ]
            
            # Create district list text
            district_text = ""
            if affected_districts:
                if len(affected_districts) <= 3:
                    district_text = f"in {', '.join(affected_districts)}"
                else:
                    district_text = f"in multiple districts including {', '.join(affected_districts[:3])} and others"
            
            return (
                f"🆘 EMERGENCY RESPONSE PLAN: {scenario.upper()} ({severity.upper()})\n\n"
                f"A {severity} {scenario} event requires immediate coordinated response {district_text}. "
                f"This plan outlines critical actions for the next 24-72 hours.\n\n"
                "🔴 IMMEDIATE ACTIONS (0-6 hours):\n"
                f"1. {priority_actions[0] if priority_actions else 'Activate emergency response teams'}\n"
                "2. Deploy mobile generators to critical facilities (hospitals, emergency services, water treatment)\n"
                "3. Establish hourly situation reporting with field teams\n"
                "4. Issue public safety announcements regarding outage areas and estimated durations\n\n"
                "🟠 SHORT-TERM ACTIONS (6-24 hours):\n"
                f"1. {priority_actions[1] if len(priority_actions) > 1 else 'Conduct comprehensive damage assessment'}\n"
                "2. Implement rolling restoration prioritizing critical infrastructure\n"
                "3. Coordinate fuel deliveries to backup generators at priority facilities\n"
                "4. Establish mutual aid coordination with neighboring districts\n\n"
                "🟡 MEDIUM-TERM ACTIONS (24-72 hours):\n"
                f"1. {priority_actions[2] if len(priority_actions) > 2 else 'Begin implementation of grid stabilization measures'}\n"
                "2. Mobilize specialized repair teams and equipment from unaffected regions\n"
                "3. Implement resource rotation plan for emergency personnel\n"
                "4. Begin preliminary recovery planning\n\n"
                "Critical Reminder: Maintain clear communication channels with local authorities and emergency services at all times."
            )
        elif query_type == 'dashboard':
            # Get alert counts
            substation_risk_count = len(context.get('substations_at_risk', []))
            line_risk_count = len(context.get('lines_at_risk', []))
            weather_alert_count = len(context.get('weather_alerts', []))
            active_outage_count = len(context.get('active_outages', []))
            
            # Generate weather alert text if available
            weather_details = ""
            if 'weather_alerts' in context and context['weather_alerts']:
                alerts = []
                for alert in context['weather_alerts'][:2]:  # Show first two
                    if isinstance(alert, dict) and 'message' in alert:
                        alerts.append(alert['message'])
                if alerts:
                    weather_details = f" Weather alerts include {' and '.join(alerts)}."
            
            return (
                "📊 EXECUTIVE GRID STATUS SUMMARY\n\n"
                f"The electricity grid is currently operating under {'high' if substation_risk_count + line_risk_count > 5 else 'moderate'} stress "
                f"with {active_outage_count} active outages, {substation_risk_count} substations and {line_risk_count} transmission lines at risk.{weather_details} "
                f"Immediate attention is required to maintain stability over the next 24-48 hours.\n\n"
                "⚡ STRATEGIC RECOMMENDATIONS:\n\n"
                "1. INCREASE CAPACITY: Temporarily boost reserve capacity by 15-20% to handle anticipated fluctuations\n"
                "2. PREVENTIVE MAINTENANCE: Deploy rapid inspection teams to the highest-risk substations in Shimla and Kinnaur districts\n"
                "3. LOAD MANAGEMENT: Initiate discussions with major industrial consumers regarding potential voluntary load reduction during peak hours\n"
                "4. WEATHER MONITORING: Establish hourly weather tracking for high-risk districts with automatic alert escalation\n"
                "5. EMERGENCY READINESS: Place rapid response teams on heightened alert status for the next 48 hours\n\n"
                "Continue monitoring key metrics at 2-hour intervals. The situation requires heightened vigilance but remains manageable with proactive measures."
            )
        else:
            return "No recommendation available due to system error. Please try again later."