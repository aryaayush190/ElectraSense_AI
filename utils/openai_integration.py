import json
import os
from typing import Dict, Any, Optional

class OpenAIService:
    """Client for interacting with OpenAI API"""
    
    # Default API key - replace with your own for direct usage
    DEFAULT_API_KEY = ""
    
    def __init__(self):
        """Initialize OpenAI service with API key"""
        # Try API key from environment or default
        self.api_key = os.environ.get("OPENAI_API_KEY", self.DEFAULT_API_KEY)
        self.client = None
        self.available = False
        
        try:
            # Only attempt to import if we have an API key
            if self.api_key and len(self.api_key.strip()) > 10:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.api_key)
                    self.available = True
                    print("OpenAI client initialized successfully")
                except ImportError:
                    print("OpenAI package not installed. Run 'pip install openai' to enable this feature.")
                except Exception as e:
                    print(f"Error initializing OpenAI client: {e}")
            else:
                print("OpenAI API key not found or invalid")
        except Exception as e:
            print(f"Error setting up OpenAI service: {e}")
            
    def is_available(self) -> bool:
        """
        Check if OpenAI service is available
        
        Returns:
            True if OpenAI can be used, False otherwise
        """
        return self.available
            
    def generate_enhanced_recommendation(self, context: Dict[str, Any], query_type: str, max_tokens: int = 500) -> Optional[str]:
        """
        Generate enhanced recommendation using OpenAI if available
        
        Args:
            context: Dictionary containing the context data
            query_type: Type of recommendation to generate
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Enhanced recommendation text or None if unavailable
        """
        if not self.available or not self.client:
            return None
            
        try:
            # Build system prompt based on query type
            if query_type == 'outage':
                system_prompt = "You are an expert power grid consultant specializing in outage management."
            elif query_type == 'load_balancing':
                system_prompt = "You are an expert power grid engineer specializing in load management and power flow optimization."
            elif query_type == 'disaster':
                system_prompt = "You are an expert in power grid disaster response planning."
            elif query_type == 'dashboard':
                system_prompt = "You are an executive advisor for electricity grid operations."
            else:
                system_prompt = "You are an expert power grid consultant."
                
            # Add instructions
            system_prompt += " Provide detailed technical recommendations based on the information provided."
            system_prompt += " Focus on practical, actionable steps and specific insights."
            system_prompt += " Use formatting with bullet points and sections for clarity."
            
            # Convert context to string representation
            context_str = json.dumps(context, indent=2)
            
            user_prompt = f"Based on the following power grid data, provide a detailed recommendation and analysis:\n\n{context_str}"
            
            # The newest OpenAI model is gpt-4o which was released May 13, 2024
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Error in OpenAI API call: {e}")
                return None
        except Exception as e:
            print(f"Error generating enhanced recommendation with OpenAI: {e}")
            return None