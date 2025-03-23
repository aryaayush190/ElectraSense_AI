import streamlit as st

def show():
    """Display About page with detailed information about the application"""
    st.title("About Electricity Resilience System")
    
    # Introduction
    st.markdown("""
    ## Introduction
    
    The Electricity Resilience System (ERS) is a comprehensive analytics platform designed to enhance 
    the reliability and resilience of power distribution networks in Himachal Pradesh, India. Using 
    advanced data analytics, machine learning, and LLM-powered recommendations, this system supports
    grid operators in predicting outages, optimizing load distribution, and responding effectively to 
    disasters affecting the electricity infrastructure.
    """)
    
    # Problem Statement
    st.markdown("""
    ## Problem Statement
    
    Mountainous regions like Himachal Pradesh face unique challenges in electricity distribution:
    
    * **Geographic Complexity**: Rugged terrain makes grid maintenance and emergency response difficult
    * **Extreme Weather Events**: Frequent storms, landslides, and snowfall cause disruptions
    * **Isolated Communities**: Critical infrastructure in remote areas depends on reliable power
    * **Limited Redundancy**: Fewer alternate routes for power transmission in mountainous regions
    * **Resource Constraints**: Challenges in mobilizing repair teams during emergencies
    
    Traditional reactive approaches to grid management are insufficient in these challenging contexts.
    Power outages in these regions can have severe consequences for both normal operations and
    disaster response efforts.
    """)
    
    # Key Features 
    st.markdown("""
    ## Key Features
    
    ### 1. Interactive Dashboard
    * **Real-time Grid Visualization**: Interactive map of substations, transmission lines, and risk areas
    * **District Risk Assessment**: Color-coded districts based on outage risk factors
    * **High-Priority Areas**: Mapping of critical infrastructure (hospitals, schools) requiring priority service
    * **Executive Summaries**: LLM-generated strategic recommendations for grid operators
    
    ### 2. Outage Prediction
    * **ML-Powered Forecasting**: XGBoost models predict outage probability and duration
    * **Weather Correlation Analysis**: Visualization of relationships between weather conditions and outages
    * **Component-Specific Risk Assessment**: Targeted analysis of vulnerable grid components
    * **Actionable Recommendations**: Specific steps to prepare for and mitigate potential outages
    
    ### 3. Load Balancing Simulation
    * **Network Flow Optimization**: Simulates optimal load distribution across the grid
    * **Failure Scenario Testing**: Analysis of grid performance when components fail
    * **Demand Adjustment Modeling**: Simulation of changes in consumption patterns
    * **Technical Remediation Steps**: Detailed actions for reducing strain on overloaded components
    
    ### 4. Disaster Response Planning
    * **Scenario-Based Planning**: Pre-configured disaster scenarios (floods, earthquakes, landslides)
    * **Impact Assessment**: Quantification of grid fragmentation and connectivity loss
    * **Critical Path Analysis**: Identification of essential transmission lines during emergencies
    * **Phased Response Plans**: Structured guidance for immediate, short-term, and medium-term actions
    """)
    
    # Technical Architecture
    st.markdown("""
    ## Technical Architecture
    
    ### Data Components
    * **Grid Infrastructure Data**: Detailed information on substations and transmission lines
    * **High-Priority Areas Database**: Critical facilities requiring prioritized service
    * **Weather Data**: Historical and current meteorological conditions
    * **Outage History**: Records of past disruptions with causes and durations
    * **District Risk Metrics**: Aggregated risk factors at district level
    
    ### Analytical Components
    * **XGBoost Models**: Machine learning models for outage prediction
    * **NetworkX-Based Grid Model**: Graph representation of the electricity network
    * **Load Balancing Algorithm**: Flow optimization for transmission line load management
    * **Risk Scoring System**: Multi-factor assessment of component vulnerability
    
    ### Visualization Components
    * **Interactive Folium Maps**: Geospatial representation of grid components
    * **Plotly Dashboards**: Interactive charts and visualizations for data analysis
    * **Streamlit UI**: User-friendly interface for system interaction
    
    ### Integration Components
    * **AIXplain API Integration**: Connection to Mistral Large LLM for recommendations
    * **OpenAI Integration**: Optional enhanced recommendations using GPT models
    * **Weather Data Processing**: Analysis and correlation of meteorological data
    """)
    
    # Use Cases
    st.markdown("""
    ## Primary Use Cases
    
    ### For Grid Operations Teams
    * **Daily Risk Assessment**: Morning review of potential outage areas requiring attention
    * **Preventive Maintenance Planning**: Prioritization of maintenance based on predicted risks
    * **Storm Preparation**: Pre-positioning of resources before extreme weather events
    * **Load Management**: Real-time adjustments to prevent overloads during peak demand
    
    ### For Emergency Response Planners
    * **Disaster Preparedness**: Development of response protocols for specific scenarios
    * **Resource Allocation**: Optimal positioning of emergency teams and equipment
    * **Critical Infrastructure Support**: Ensuring continuous power to essential facilities
    * **Recovery Planning**: Structured approach to grid restoration after major events
    
    ### For Energy Administration Officials
    * **Investment Prioritization**: Data-driven decisions for grid strengthening projects
    * **Policy Development**: Evidence-based regulatory recommendations
    * **Public Communication**: Accurate information for community advisories
    * **Performance Monitoring**: Tracking of resilience improvements over time
    """)
    
    # Future Scope
    st.markdown("""
    ## Future Development Roadmap
    
    ### Enhanced Prediction Capabilities
    * **Integration with Satellite Imagery**: Incorporating remote sensing data for vegetation encroachment detection
    * **Advanced Weather Models**: More precise meteorological predictions at micro-grid level
    * **Equipment Health Monitoring**: IoT sensor integration for real-time component status
    * **Demand Forecasting**: Predictive models for consumption patterns affecting grid stability
    
    ### Extended Analysis Tools
    * **Economic Impact Assessment**: Quantification of financial costs of outages
    * **Renewable Integration Modeling**: Analysis of solar and hydro additions to the grid
    * **Climate Change Adaptation**: Long-term planning for changing weather patterns
    * **Microgrid Isolation Strategy**: Optimized approaches for creating self-sufficient grid segments
    
    ### System Enhancements
    * **Mobile Application**: Field-accessible version for maintenance teams
    * **Real-time Data Streaming**: Live updates from grid sensors and weather stations
    * **Automated Alert System**: Proactive notifications for emerging risks
    * **Expanded Geographic Coverage**: Extension to additional regions beyond Himachal Pradesh
    
    ### Advanced AI Applications
    * **Multi-modal AI Analysis**: Combining text, image, and time-series data for comprehensive insights
    * **Reinforcement Learning for Grid Management**: Adaptive strategies for dynamic conditions
    * **Conversational Interface**: Natural language interaction for non-technical users
    * **Explainable AI for Recommendations**: Transparent reasoning behind system suggestions
    """)
    
    # Implementation Details
    st.markdown("""
    ## Technical Implementation
    
    ### Core Technologies
    * **Python**: Primary programming language for system development
    * **Streamlit**: Web application framework for interactive user interface
    * **Pandas/NumPy**: Data processing and numerical computation libraries
    * **Scikit-learn/XGBoost**: Machine learning frameworks for predictive models
    * **NetworkX**: Graph theory library for grid network analysis
    * **Folium/Plotly**: Visualization libraries for maps and charts
    
    ### Machine Learning Pipeline
    * **Feature Engineering**: Creation of relevant inputs from raw grid and weather data
    * **Model Training**: XGBoost regression and classification for outage prediction
    * **Hyperparameter Optimization**: Fine-tuning model parameters for optimal performance
    * **Validation Approach**: Time-series cross-validation for temporal prediction tasks
    
    ### AI Integration
    * **AIXplain API**: Primary LLM service using Mistral Large model
    * **OpenAI API**: Optional enhanced recommendation service using GPT models
    * **Prompt Engineering**: Specialized templates for different recommendation contexts
    * **Fallback Mechanisms**: Robust handling of service unavailability
    
    ### Security Considerations
    * **API Key Management**: Secure storage of external service credentials
    * **Data Privacy**: Processing of non-personal infrastructure information only
    * **Recommendation Verification**: Human-in-the-loop validation of critical suggestions
    * **Error Handling**: Graceful degradation when external services are unavailable
    """)
    
    # Benefits and Impact
    st.markdown("""
    ## Expected Benefits and Impact
    
    ### Operational Improvements
    * **Reduced Outage Duration**: 20-30% decrease in average restoration time
    * **Preventive Maintenance Efficiency**: 40% improvement in resource allocation
    * **Load Balancing Optimization**: 15-25% reduction in overload incidents
    * **Faster Disaster Response**: 50% improvement in critical infrastructure recovery time
    
    ### Economic Benefits
    * **Reduced Economic Losses**: Minimized business disruption from power outages
    * **Maintenance Cost Optimization**: More efficient use of limited resources
    * **Extended Infrastructure Lifespan**: Less strain on components through better load management
    * **Lower Emergency Response Costs**: More efficient deployment of repair teams
    
    ### Community Benefits
    * **Enhanced Essential Services**: More reliable power for hospitals and emergency facilities
    * **Improved Public Safety**: Better management of outages during extreme weather
    * **Community Resilience**: Faster recovery from natural disasters
    * **Rural Development Support**: More reliable electricity for remote communities
    """)
    
    # Contact Information
    st.markdown("""
    ## Development Information
    
    This system was developed as part of an initiative to enhance power grid resilience in mountainous 
    regions, with a specific focus on the unique challenges faced in Himachal Pradesh, India.
    
    The current version represents a proof-of-concept implementation using realistic but 
    simulated data. Real-world deployment would require integration with actual grid monitoring 
    systems, weather forecasting services, and emergency response protocols.
    """)
    
    # Technical Disclaimer
    st.info("""
    **Technical Note**: This application demonstrates capabilities using generated sample data. 
    For production deployment, integration with live data sources, proper security measures, 
    and thorough validation against historical events would be required.
    """)
