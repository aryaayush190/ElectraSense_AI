import streamlit as st
from data_generator import initialize_data

# Set page configuration
st.set_page_config(
    page_title="ElectraSense: Electricity Resilience System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data if not already done
if 'data_initialized' not in st.session_state:
    st.session_state.data_initialized = False

if not st.session_state.data_initialized:
    # Generate or load data once
    st.session_state.grid_data, st.session_state.weather_data, st.session_state.outage_history, st.session_state.infrastructure_data = initialize_data()
    st.session_state.data_initialized = True

# Sidebar navigation
st.sidebar.title("Electricity Resilience System")
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Electricity_logo.svg/1200px-Electricity_logo.svg.png", width=100)

# Navigation options
page = st.sidebar.radio(
    "Navigate to",
    ["Dashboard", "Outage Prediction", "Load Balancing", "Disaster Response", "About"]
)

# Display information in sidebar
st.sidebar.markdown("---")
st.sidebar.info(
    "This system provides real-time monitoring and prediction capabilities "
    "for electricity grid resilience in Himachal Pradesh."
)
st.sidebar.markdown("---")
st.sidebar.write("Developed by Team AstralVolt")
st.sidebar.write("@Powered by aiXplain")

# Import and display the selected page
if page == "Dashboard":
    import pages.dashboard as dashboard_module
    dashboard_module.show()
elif page == "Outage Prediction":
    import pages.outage_prediction as outage_prediction_module
    outage_prediction_module.show()
elif page == "Load Balancing":
    import pages.load_balancing as load_balancing_module
    load_balancing_module.show()
elif page == "Disaster Response":
    import pages.disaster_response as disaster_response_module
    disaster_response_module.show()
elif page == "About":
    import pages.about as about_module
    about_module.show()