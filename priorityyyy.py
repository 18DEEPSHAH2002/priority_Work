import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- Page Configuration ---
# Set the layout and appearance of the Streamlit page.
st.set_page_config(
    page_title="Task Management Dashboard",
    page_icon="✅",
    layout="wide",
)

# --- Caching Function for Data Loading ---
# Using st.cache_data ensures that the data is loaded only once,
# speeding up the app's performance on subsequent runs.
@st.cache_data
def load_data(url):
    """
    Loads and preprocesses data from the specified Google Sheet URL.
    It cleans column names and handles potential missing values.
    """
    try:
        # Use regex to extract the sheet ID and GID for a robust URL construction
        sheet_id_match = re.search(r'spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        gid_match = re.search(r'gid=([0-9]+)', url)
        
        if sheet_id_match and gid_match:
            sheet_id = sheet_id_match.group(1)
            gid = gid_match.group(1)
            csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        else:
            # Fallback for simpler URLs
            csv_url = url.replace('/edit?', '/export?format=csv&')

        df = pd.read_csv(csv_url)

        # --- Data Cleaning and Preparation ---
        # Strip any leading/trailing whitespace from column names.
        df.columns = df.columns.str.strip()

        # Convert 'Pending Since' to datetime objects for proper calculations.
        # 'coerce' will turn any parsing errors into NaT (Not a Time).
        df['Pending Since'] = pd.to_datetime(df['Pending Since'], errors='coerce')

        # Clean up text columns by stripping whitespace and filling missing values.
        df['Task Status'] = df['Task Status'].str.strip().fillna('Unknown')
        df['Officer Name'] = df['Officer Name'].str.strip().fillna('Unassigned')
        df['Department'] = df['Department'].str.strip().fillna('Unknown')
        df['Priority'] = df['Priority'].str.strip().fillna('Not Specified')
        
        return df
    except Exception as e:
        # Provide a more specific error message if data loading fails.
        st.error(f"Error loading data: {e}")
        st.warning("Please ensure the Google Sheet is shared publicly ('Anyone with the link can view').")
        return pd.DataFrame()

# --- Data Loading ---
# The URL of your Google Sheet. Make sure it's shared correctly.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/edit?gid=213021534#gid=213021534"
df = load_data(GOOGLE_SHEET_URL)

# --- Sidebar Navigation ---
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio("Go to", ["Officer Pending Tasks", "Task Priority Dashboard"])
st.sidebar.markdown("---")
st.sidebar.info("This dashboard provides an overview of pending tasks from the Google Sheet.")

# --- Main Application Logic ---
# Only proceed if the DataFrame was loaded successfully.
if not df.empty:
    # Filter the DataFrame to only include tasks with a 'pending' status.
    pending_tasks_df = df[df['Task Status'].str.lower() == 'pending'].copy()

    # --- Page 1: Officer Pending Tasks ---
    if page == "Officer Pending Tasks":
        st.title("👨‍💼 Officer Pending Tasks Overview")
        st.markdown("This page shows the number of pending tasks assigned to each officer.")
        st.markdown("---")

        if not pending_tasks_df.empty:
            # Count pending tasks for each officer.
            officer_pending_counts = pending_tasks_df['Officer Name'].value_counts().reset_index()
            officer_pending_counts.columns = ['Officer Name', 'Number of Pending Tasks']

            # Create two columns for the layout.
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Pending Task List")
                # Display the data in a table.
                st.dataframe(officer_pending_counts, use_container_width=True, hide_index=True)

            with col2:
                st.subheader("Visual Distribution")
                # Create a bar chart to visualize the pending tasks per officer.
                fig = px.bar(
                    officer_pending_counts,
                    x='Officer Name',
                    y='Number of Pending Tasks',
                    title='Number of Pending Tasks per Officer',
                    text='Number of Pending Tasks', # This adds the count on top of the bars
                    color='Officer Name',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    xaxis_title="Officer Name",
                    yaxis_title="Count of Pending Tasks",
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No pending tasks found to display.")

    # --- Page 2: Task Priority Dashboard ---
    elif page == "Task Priority Dashboard":
        st.title("📊 Task Priority Dashboard")
        st.markdown("An in-depth look at task distribution by priority level, department, and officer.")
        st.markdown("---")

        if not pending_tasks_df.empty:
            # --- Key Metrics ---
            st.header("High-Level Summary")
            total_pending = pending_tasks_df.shape[0]
            most_urgent_count = pending_tasks_df[pending_tasks_df['Priority'] == 'Most Urgent'].shape[0]
            high_count = pending_tasks_df[pending_tasks_df['Priority'] == 'High'].shape[0]
            medium_count = pending_tasks_df[pending_tasks_df['Priority'] == 'Medium'].shape[0]

            # Display the key metrics in columns.
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Pending Tasks", total_pending)
            col2.metric("Most Urgent Tasks", most_urgent_count)
            col3.metric("High Priority Tasks", high_count)
            col4.metric("Medium Priority Tasks", medium_count)
            st.markdown("---")

            # --- Helper function for creating consistent bar charts ---
            def create_bar_chart(data, x_axis, title, color_by):
                """Creates a styled Plotly bar chart with counts displayed on the bars."""
                fig = px.bar(
                    data,
                    x=x_axis,
                    y='count',
                    title=title,
                    text='count',
                    color=color_by,
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    yaxis_title="Task Count",
                    xaxis_title=x_axis,
                    showlegend=True,
                )
                return fig

            # --- Most Urgent Tasks Section ---
            st.header("🚨 Most Urgent Tasks")
            most_urgent_df = pending_tasks_df[pending_tasks_df['Priority'] == 'Most Urgent']
            if not most_urgent_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_urgent = most_urgent_df['Officer Name'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(officer_urgent, 'Officer Name', 'Officer-wise Most Urgent Tasks', 'Officer Name'), use_container_width=True)
                with col2:
                    dept_urgent = most_urgent_df['Department'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(dept_urgent, 'Department', 'Department-wise Most Urgent Tasks', 'Department'), use_container_width=True)
            else:
                st.info("No 'Most Urgent' tasks are currently pending.")
            st.markdown("---")

            # --- High Priority Tasks Section ---
            st.header("⚠️ High Priority Tasks")
            high_df = pending_tasks_df[pending_tasks_df['Priority'] == 'High']
            if not high_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_high = high_df['Officer Name'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(officer_high, 'Officer Name', 'Officer-wise High Priority Tasks', 'Officer Name'), use_container_width=True)
                with col2:
                    dept_high = high_df['Department'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(dept_high, 'Department', 'Department-wise High Priority Tasks', 'Department'), use_container_width=True)
            else:
                st.info("No 'High' priority tasks are currently pending.")
            st.markdown("---")

            # --- Medium Priority Tasks Section ---
            st.header("🟡 Medium Priority Tasks")
            medium_df = pending_tasks_df[pending_tasks_df['Priority'] == 'Medium']
            if not medium_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_medium = medium_df['Officer Name'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(officer_medium, 'Officer Name', 'Officer-wise Medium Priority Tasks', 'Officer Name'), use_container_width=True)
                with col2:
                    dept_medium = medium_df['Department'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(dept_medium, 'Department', 'Department-wise Medium Priority Tasks', 'Department'), use_container_width=True)
            else:
                st.info("No 'Medium' priority tasks are currently pending.")

        else:
            st.warning("No pending tasks found to display.")
else:
    # This message shows if the initial data load fails.
    st.error("Failed to load data. Please check the Google Sheet URL and permissions.")
