import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Oura Ring Dashboard", page_icon="💍", layout="wide")

st.title("Oura Ring Health Dashboard")

# Initialize session state
if 'oura_data' not in st.session_state:
    st.session_state['oura_data'] = None
if 'data_source' not in st.session_state:
    st.session_state['data_source'] = None

# Sidebar for configuration
st.sidebar.header("Configuration")

# Option 1: Upload CSV file
st.sidebar.subheader("Upload Oura Data")
uploaded_file = st.sidebar.file_uploader("Upload your Oura Ring CSV file", type=['csv'])

# Option 2: API Integration
st.sidebar.subheader("Or Connect via API")
api_token = st.sidebar.text_input("Oura API Token (optional)", type="password")

# Add clear data button if we have session data
if st.session_state['oura_data'] is not None:
    if st.sidebar.button("Clear Data / Fetch New"):
        st.session_state['oura_data'] = None
        st.session_state['data_source'] = None
        st.rerun()

# Function to display tabs with data
def display_data_tabs(df):
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Sleep", "Activity", "Readiness", "Trends"])
    
    with tab1:
        st.header("Daily Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Days", len(df))
        
        with col2:
            if 'sleep_score' in df.columns:
                avg_sleep = df['sleep_score'].mean()
                st.metric("Avg Sleep Score", f"{avg_sleep:.1f}")
        
        with col3:
            if 'readiness_score' in df.columns:
                avg_readiness = df['readiness_score'].mean()
                st.metric("Avg Readiness", f"{avg_readiness:.1f}")
        
        with col4:
            if 'activity_score' in df.columns:
                avg_activity = df['activity_score'].mean()
                st.metric("Avg Activity", f"{avg_activity:.1f}")
        
        st.subheader("Raw Data")
        st.dataframe(df)
    
    with tab2:
        st.header("Sleep Analysis")
        
        if 'sleep_score' in df.columns:
            date_col = 'date' if 'date' in df.columns else df.columns[0]
            
            fig = px.line(df, x=date_col, y='sleep_score',
                         title='Sleep Score Over Time')
            st.plotly_chart(fig, use_container_width=True)
            
            if 'total_sleep_duration' in df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    df_copy = df.copy()
                    df_copy['sleep_hours'] = df_copy['total_sleep_duration'] / 3600
                    fig = px.histogram(df_copy, x='sleep_hours', nbins=30,
                                     title='Sleep Duration Distribution (hours)')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    avg_sleep_hours = (df['total_sleep_duration'] / 3600).mean()
                    st.metric("Average Sleep Duration", f"{avg_sleep_hours:.1f} hours")
                    
                    df_copy = df.copy()
                    df_copy['sleep_hours'] = df_copy['total_sleep_duration'] / 3600
                    fig = px.line(df_copy, x=date_col, y='sleep_hours',
                                title='Sleep Duration Over Time')
                    st.plotly_chart(fig, use_container_width=True)
            
            if all(col in df.columns for col in ['deep_sleep', 'rem_sleep', 'light_sleep']):
                st.subheader("Sleep Stages")
                sleep_stages = df[[date_col, 'deep_sleep', 'rem_sleep', 'light_sleep']].melt(
                    id_vars=date_col, var_name='Stage', value_name='Score'
                )
                fig = px.bar(sleep_stages, x=date_col, y='Score', color='Stage',
                           title='Sleep Stages Over Time')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sleep data available.")
    
    with tab3:
        st.header("Activity Analysis")
        
        if 'activity_score' in df.columns:
            date_col = 'date' if 'date' in df.columns else df.columns[0]
            
            fig = px.line(df, x=date_col, y='activity_score',
                         title='Activity Score Over Time')
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'steps' in df.columns:
                    fig = px.bar(df, x=date_col, y='steps',
                               title='Daily Steps')
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric("Average Steps", f"{df['steps'].mean():.0f}")
            
            with col2:
                if 'calories' in df.columns:
                    fig = px.line(df, x=date_col, y='calories',
                                title='Active Calories Burned')
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric("Avg Active Calories", f"{df['calories'].mean():.0f}")
        else:
            st.info("No activity data available.")
    
    with tab4:
        st.header("Readiness Analysis")
        
        if 'readiness_score' in df.columns:
            date_col = 'date' if 'date' in df.columns else df.columns[0]
            
            fig = px.line(df, x=date_col, y='readiness_score',
                         title='Readiness Score Over Time')
            st.plotly_chart(fig, use_container_width=True)
            
            fig = px.histogram(df, x='readiness_score', nbins=20,
                             title='Readiness Score Distribution')
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'temperature_deviation' in df.columns:
                    fig = px.line(df, x=date_col, y='temperature_deviation',
                                title='Temperature Deviation')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'resting_heart_rate' in df.columns:
                    fig = px.line(df, x=date_col, y='resting_heart_rate',
                                title='Resting Heart Rate')
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No readiness data available.")
    
    with tab5:
        st.header("Trends & Correlations")
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                x_axis = st.selectbox("X-axis", numeric_cols, key="x_axis_select")
            with col2:
                y_axis = st.selectbox("Y-axis", [col for col in numeric_cols if col != x_axis], key="y_axis_select")
            
            fig = px.scatter(df, x=x_axis, y=y_axis, trendline="ols",
                           title=f"{x_axis} vs {y_axis}")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Correlation Matrix")
            corr = df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, aspect="auto",
                          title="Correlation Heatmap")
            st.plotly_chart(fig, use_container_width=True)

# Handle CSV upload
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("Data loaded successfully!")
    display_data_tabs(df)

# Handle API data
elif api_token and st.session_state['oura_data'] is not None:
    df = st.session_state['oura_data']
    st.success(f"Data loaded successfully! ({len(df)} days)")
    display_data_tabs(df)

elif api_token:
    st.info("Ready to fetch data from Oura API")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    if st.button("Fetch Data"):
        try:
            with st.spinner("Fetching your Oura Ring data..."):
                headers = {'Authorization': f'Bearer {api_token}'}
                
                # Fetch sleep data
                sleep_response = requests.get(
                    "https://api.ouraring.com/v2/usercollection/daily_sleep",
                    headers=headers,
                    params={'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}
                )
                
                # Fetch activity data
                activity_response = requests.get(
                    "https://api.ouraring.com/v2/usercollection/daily_activity",
                    headers=headers,
                    params={'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}
                )
                
                # Fetch readiness data
                readiness_response = requests.get(
                    "https://api.ouraring.com/v2/usercollection/daily_readiness",
                    headers=headers,
                    params={'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}
                )
                
                if sleep_response.status_code == 200 or activity_response.status_code == 200:
                    # Process sleep data
                    sleep_data = []
                    if sleep_response.status_code == 200:
                        for item in sleep_response.json().get('data', []):
                            sleep_data.append({
                                'date': item.get('day'),
                                'sleep_score': item.get('score'),
                                'total_sleep_duration': item.get('contributors', {}).get('total_sleep', 0),
                                'deep_sleep': item.get('contributors', {}).get('deep_sleep', 0),
                                'rem_sleep': item.get('contributors', {}).get('rem_sleep', 0),
                                'light_sleep': item.get('contributors', {}).get('light_sleep', 0),
                            })
                    
                    # Process activity data
                    activity_data = []
                    if activity_response.status_code == 200:
                        for item in activity_response.json().get('data', []):
                            activity_data.append({
                                'date': item.get('day'),
                                'activity_score': item.get('score'),
                                'steps': item.get('steps'),
                                'calories': item.get('active_calories'),
                            })
                    
                    # Process readiness data
                    readiness_data = []
                    if readiness_response.status_code == 200:
                        for item in readiness_response.json().get('data', []):
                            readiness_data.append({
                                'date': item.get('day'),
                                'readiness_score': item.get('score'),
                                'temperature_deviation': item.get('temperature_deviation'),
                                'resting_heart_rate': item.get('contributors', {}).get('resting_heart_rate', 0)
                            })
                    
                    # Merge all dataframes
                    df = None
                    if sleep_data:
                        df = pd.DataFrame(sleep_data)
                    if activity_data:
                        activity_df = pd.DataFrame(activity_data)
                        if df is not None:
                            df = df.merge(activity_df, on='date', how='outer')
                        else:
                            df = activity_df
                    if readiness_data:
                        readiness_df = pd.DataFrame(readiness_data)
                        if df is not None:
                            df = df.merge(readiness_df, on='date', how='outer')
                        else:
                            df = readiness_df
                    
                    if df is not None and not df.empty:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date')
                        
                        # Store in session state
                        st.session_state['oura_data'] = df
                        st.session_state['data_source'] = 'api'
                        st.rerun()
                    else:
                        st.warning("No data returned for the selected date range.")
                else:
                    st.error(f"Failed to fetch data. Status code: {sleep_response.status_code}")
                    st.info("Make sure your API token is valid and has the necessary permissions.")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Please check your API token and try again.")
    
    st.markdown("""
    ### How to get your Oura API Token:
    1. Go to [Oura Cloud](https://cloud.ouraring.com/)
    2. Log in to your account
    3. Navigate to Settings > Personal Access Tokens
    4. Create a new token with the required scopes (daily, sleep, readiness)
    5. Copy and paste the token above
    """)

else:
    st.info("Please upload your Oura Ring data CSV file or enter your API token in the sidebar")
    
    st.markdown("""
    ### Welcome to your Oura Ring Dashboard!
    
    This app helps you visualize and analyze your Oura Ring health data.
    
    **Features:**
    - Daily overview of your health metrics
    - Sleep analysis and trends
    - Activity tracking
    - Readiness monitoring
    - Correlation analysis
    
    **How to get started:**
    1. Export your data from [Oura Cloud](https://cloud.ouraring.com/)
    2. Upload the CSV file using the sidebar
    3. Explore your health insights!
    
    **Optional:** You can also connect via the Oura API (requires personal access token)
    """)
