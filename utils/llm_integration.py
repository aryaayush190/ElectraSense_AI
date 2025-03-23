import requests
import json
import os
from typing import Dict, List, Any, Optional

class AIXplainLLMService:
    """Client for interacting with AIXplain's Mistral Large LLM"""
    
    def __init__(self, api_key=None):
        """Initialize the AIXplain client with API key"""
        self.api_key = api_key or os.getenv("AIXPLAIN_API_KEY", "bc0da63b100ac992d34e86ba4502d2bbb3ed05dc0d18fef054b13a5d28692ea0")
        self.base_url = "https://api.aixplain.com/production/generate/41ebd663-9048-46f9-a2df-49e08b0572e5"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate_recommendation(self, 
                               context: Dict[str, Any], 
                               query_type: str, 
                               max_tokens: int = 512) -> str:
        """
        Generate a recommendation based on the provided context
        
        Parameters:
        - context: Dictionary containing the context data
        - query_type: Type of recommendation to generate (e.g., 'outage', 'load_balancing', 'disaster')
        - max_tokens: Maximum number of tokens to generate
        
        Returns:
        - Generated recommendation text
        """
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
            raise ValueError(f"Unknown query type: {query_type}")
        
        # Call the AIXplain API
        try:
            response = self._call_api(prompt, max_tokens)
            return response
        except Exception as e:
            print(f"Error calling AIXplain API: {e}")
            # Fallback response in case of API error
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
            return (
                "Based on the current conditions, there is a significant risk of power outages in the affected area. "
                "Recommend deploying emergency response teams on standby and notifying critical infrastructure facilities. "
                "Estimated outage duration of 3-6 hours if conditions worsen. Ensure backup generators are fueled and operational "
                "for critical services including hospitals and water treatment facilities."
            )
        elif query_type == 'load_balancing':
            return (
                "Current load distribution is suboptimal. Recommend redistributing load from overloaded lines to parallel circuits "
                "where available. Consider temporary reduction of service to non-critical industrial consumers during peak hours. "
                "Monitor transmission line temperatures carefully on all lines operating above 80% capacity."
            )
        elif query_type == 'disaster':
            scenario = context.get('scenario_type', 'disaster')
            return (
                f"Emergency response plan for {scenario} scenario: Prioritize restoration of power to critical infrastructure "
                "including hospitals, water treatment plants, and emergency services. Deploy mobile generators to affected areas. "
                "Establish emergency coordination center and maintain hourly communication with local authorities. "
                "Implement rolling blackouts if necessary to preserve grid stability."
            )
        elif query_type == 'dashboard':
            return (
                "Executive Summary: The grid is currently experiencing moderate stress due to weather conditions and existing outages. "
                "Careful management is required over the next 24 hours to maintain stability. \n\n"
                "Key Recommendations:\n"
                "1. Increase reserve capacity by 15% to handle potential fluctuations\n"
                "2. Deploy preventive maintenance teams to at-risk substations\n"
                "3. Coordinate with major industrial consumers regarding potential load shedding\n"
                "4. Monitor weather developments hourly for the next 24 hours"
            )
        else:
            return "No recommendation available due to system error. Please try again later."
