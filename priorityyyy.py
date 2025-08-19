import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Analysis Dashboard",
    page_icon="📊",
    layout="wide",
)

# --- Data Loading and Caching ---
@st.cache_data
def load_data(uploaded_file):
    """
    Loads data from an uploaded CSV file.
    The data is cached to improve performance.
    """
    try:
        # Read the data into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        
        # --- Data Cleaning and Preprocessing ---
        # Rename columns to be more script-friendly
        df.rename(columns={
            'Entry Date': 'Start Date',
            'Marked to Officer': 'Assign To'
        }, inplace=True)

        # Convert date columns to datetime objects, handling potential errors
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        
        # Drop rows where essential columns are missing
        df.dropna(subset=['Priority', 'Dealing Branch', 'Assign To', 'Start Date'], inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Error loading or processing the file: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- Sidebar for File Upload ---
st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])


# --- Main Application ---
st.title("📊 Task Management Analysis Dashboard")
st.markdown("---")

if uploaded_file is not None:
    df = load_data(uploaded_file)

    if not df.empty:
        # --- Key Metrics ---
        st.header("Key Performance Indicators")

        # Filter data based on priority
        most_urgent_tasks = df[df['Priority'] == 'Most Urgent']
        medium_priority_tasks = df[df['Priority'] == 'Medium']
        
        # Calculate metrics
        total_tasks = len(df)
        num_most_urgent = len(most_urgent_tasks)
        num_medium_priority = len(medium_priority_tasks)

        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", f"{total_tasks} 📝")
        col2.metric("Most Urgent Tasks", f"{num_most_urgent} 🔥")
        col3.metric("Medium Priority Tasks", f"{num_medium_priority} ⚠️")

        st.markdown("---")

        # --- Visualizations ---
        st.header("Task Distribution Analysis")

        # Create two columns for the graphs
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            # 1. Most Urgent Tasks by Dealing Branch
            st.subheader("Most Urgent Tasks by Dealing Branch")
            if not most_urgent_tasks.empty:
                urgent_by_branch = most_urgent_tasks['Dealing Branch'].value_counts().reset_index()
                urgent_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig1 = px.bar(urgent_by_branch, x='Dealing Branch', y='Number of Tasks', title='Most Urgent Tasks per Dealing Branch', color='Dealing Branch')
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("No 'Most Urgent' tasks to display.")

            # 2. Medium Priority Tasks by Dealing Branch
            st.subheader("Medium Priority Tasks by Dealing Branch")
            if not medium_priority_tasks.empty:
                medium_by_branch = medium_priority_tasks['Dealing Branch'].value_counts().reset_index()
                medium_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig2 = px.bar(medium_by_branch, x='Dealing Branch', y='Number of Tasks', title='Medium Priority Tasks per Dealing Branch', color='Dealing Branch')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No 'Medium' priority tasks to display.")

        with viz_col2:
            # 3. Most Urgent Tasks by Officer
            st.subheader("Most Urgent Tasks by Officer")
            if not most_urgent_tasks.empty:
                urgent_by_officer = most_urgent_tasks['Assign To'].value_counts().reset_index()
                urgent_by_officer.columns = ['Officer', 'Number of Tasks']
                fig3 = px.bar(urgent_by_officer, x='Officer', y='Number of Tasks', title='Most Urgent Tasks per Officer', color='Officer')
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("No 'Most Urgent' tasks to display.")

            # 4. Medium Priority Tasks by Officer
            st.subheader("Medium Priority Tasks by Officer")
            if not medium_priority_tasks.empty:
                medium_by_officer = medium_priority_tasks['Assign To'].value_counts().reset_index()
                medium_by_officer.columns = ['Officer', 'Number of Tasks']
                fig4 = px.bar(medium_by_officer, x='Officer', y='Number of Tasks', title='Medium Priority Tasks per Officer', color='Officer')
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.warning("No 'Medium' priority tasks to display.")

        st.markdown("---")

        # --- Pending Task Analysis ---
        st.header("Pending Task Analysis")
        
        # Define pending tasks: Status is not 'Completed' and today's date is after the start date
        today = datetime.now()
        # Ensure 'Status' column exists before trying to filter by it
        if 'Status' in df.columns:
            pending_tasks = df[(df['Status'] != 'Completed') & (df['Start Date'] < today)]
        else:
            # If no 'Status' column, assume all tasks are pending if their start date is in the past
            pending_tasks = df[df['Start Date'] < today]
            st.info("Note: 'Status' column not found. Pending tasks are calculated based on the 'Start Date'.")


        if not pending_tasks.empty:
            pending_col1, pending_col2 = st.columns(2)

            with pending_col1:
                # 5. Pending Tasks by Dealing Branch
                st.subheader("Pending Tasks by Dealing Branch")
                pending_by_branch = pending_tasks['Dealing Branch'].value_counts().reset_index()
                pending_by_branch.columns = ['Dealing Branch', 'Number of Pending Tasks']
                fig5 = px.bar(pending_by_branch, x='Dealing Branch', y='Number of Pending Tasks', title='Pending Tasks per Dealing Branch', color='Dealing Branch')
                st.plotly_chart(fig5, use_container_width=True)

            with pending_col2:
                # 6. Pending Tasks by Officer
                st.subheader("Pending Tasks by Officer")
                pending_by_officer = pending_tasks['Assign To'].value_counts().reset_index()
                pending_by_officer.columns = ['Officer', 'Number of Pending Tasks']
                fig6 = px.bar(pending_by_officer, x='Officer', y='Number of Pending Tasks', title='Pending Tasks per Officer', color='Officer')
                st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("Congratulations! There are no pending tasks.")

    else:
        st.warning("The uploaded file could not be processed. Please check the file format and content.")
else:
    st.info("Please upload a CSV file using the sidebar to begin the analysis.")
