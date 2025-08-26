import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Management Dashboard",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Caching Function for Data Loading ---
@st.cache_data(ttl=600)
def load_data(sheet_id, gid):
    """Loads and cleans data from a public Google Sheet."""
    try:
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        df = pd.read_csv(url, skiprows=1)

        # Define and assign column names
        df.columns = [
            's_no', 'supervisor_office', 'branch_name', 'clerk', 'case_no',
            'case_title', 'case_status', 'status_comment', 'pending_stage',
            'court_name', 'dc_action_needed', 'what_action_needed_to_be_taken_by_dc',
            'reply_by', 'reply_filed', 'next_hearing_date', 'case_detail',
            'court_directions', 'direction_details', 'compliance_of_direction',
            'status_reply_required', 'status_reply_filed', 'case_documents',
            'remarks', 'days_left'
        ]

        # --- Data Cleaning and Preparation ---
        df = df.iloc[1:].reset_index(drop=True)
        df.dropna(subset=['s_no'], inplace=True)

        # Clean 'case_status'
        df['case_status'] = df['case_status'].str.strip().str.title().fillna('Not Specified')
        status_replacements = {'Pending': 'Pending', 'Decided': 'Decided', 'Dismissed': 'Decided', 'Disposed': 'Decided'}
        df['case_status'] = df['case_status'].replace(status_replacements).fillna('Not Specified')
        
        # Clean 'court_name'
        df['court_name'] = df['court_name'].str.strip().str.title().fillna('Not Specified')
        court_replacements = {'Punjab And Haryana High Court': 'High Court', 'District Court Ludhiana': 'District Court', 'Supreme Court Of India': 'Supreme Court'}
        df['court_name'] = df['court_name'].replace(court_replacements)

        # Clean dates and supervisor office
        df['next_hearing_date'] = pd.to_datetime(df['next_hearing_date'], errors='coerce')
        df['supervisor_office'] = df['supervisor_office'].str.strip().fillna('Not Assigned')
        
        # For this dashboard, we will add a 'Priority' column if it doesn't exist.
        # This is a placeholder. You should have this column in your actual sheet.
        if 'Priority' not in df.columns:
            # Simple logic to assign priority based on another column for demonstration
            priorities = ['Most Urgent', 'High', 'Medium']
            df['Priority'] = [priorities[i % 3] for i in range(len(df))]


        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}")
        st.error("Please make sure your Google Sheet is shared with 'Anyone with the link' as a 'Viewer'.")
        return pd.DataFrame()

# --- Data Loading ---
# Extract from your URL: https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/edit?gid=213021534
SHEET_ID = "14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI"
GID = "213021534"
df = load_data(SHEET_ID, GID)

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Officer Pending Tasks", "Task Priority Dashboard"])
st.sidebar.markdown("---")
st.sidebar.info("This dashboard provides an overview of pending tasks based on the provided Google Sheet.")

# --- Main Application Logic ---
if not df.empty:
    # Filter for pending tasks using the new column name
    pending_tasks_df = df[df['case_status'].str.lower() == 'pending'].copy()

    if page == "Officer Pending Tasks":
        # --- Officer Pending Tasks Page ---
        st.title("👨‍💼 Officer Pending Tasks Overview")
        st.markdown("This page shows the number of pending tasks for each officer.")

        if not pending_tasks_df.empty:
            officer_pending_counts = pending_tasks_df['supervisor_office'].value_counts().reset_index()
            officer_pending_counts.columns = ['Officer Name', 'Number of Pending Tasks']

            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Pending Task List")
                st.dataframe(officer_pending_counts, use_container_width=True, hide_index=True)

            with col2:
                st.subheader("Visual Distribution")
                fig = px.bar(
                    officer_pending_counts,
                    x='Officer Name',
                    y='Number of Pending Tasks',
                    title='Number of Pending Tasks per Officer',
                    text='Number of Pending Tasks',
                    color='Officer Name',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    xaxis_title="Officer Name",
                    yaxis_title="Count of Pending Tasks",
                    showlegend=False,
                    uniformtext_minsize=8,
                    uniformtext_mode='hide'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No pending tasks found to display.")

    elif page == "Task Priority Dashboard":
        # --- Task Priority Dashboard Page ---
        st.title("📊 Task Priority Dashboard")
        st.markdown("An in-depth look at task distribution by priority level.")

        if not pending_tasks_df.empty:
            # --- Key Metrics ---
            st.header("High-Level Summary")
            total_pending = pending_tasks_df.shape[0]
            # NOTE: The provided 'load_data' function does not include a 'Priority' column.
            # I have added a placeholder 'Priority' column in the load_data function for demonstration.
            # Please ensure your actual Google Sheet has a 'Priority' column.
            most_urgent_count = pending_tasks_df[pending_tasks_df['Priority'] == 'Most Urgent'].shape[0]
            high_count = pending_tasks_df[pending_tasks_df['Priority'] == 'High'].shape[0]
            medium_count = pending_tasks_df[pending_tasks_df['Priority'] == 'Medium'].shape[0]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Pending Tasks", total_pending)
            col2.metric("Most Urgent Tasks", most_urgent_count)
            col3.metric("High Priority Tasks", high_count)
            col4.metric("Medium Priority Tasks", medium_count)
            st.markdown("---")

            # --- Helper function for creating bar charts ---
            def create_bar_chart(data, x_axis, title, color_by):
                """Creates a styled Plotly bar chart."""
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
                    showlegend=True,
                    uniformtext_minsize=8,
                    uniformtext_mode='hide'
                )
                return fig

            # --- Most Urgent Tasks ---
            st.header("🚨 Most Urgent Tasks")
            most_urgent_df = pending_tasks_df[pending_tasks_df['Priority'] == 'Most Urgent']
            if not most_urgent_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_urgent = most_urgent_df['supervisor_office'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(officer_urgent, 'supervisor_office', 'Officer-wise Most Urgent Tasks', 'supervisor_office'), use_container_width=True)
                with col2:
                    dept_urgent = most_urgent_df['branch_name'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(dept_urgent, 'branch_name', 'Department-wise Most Urgent Tasks', 'branch_name'), use_container_width=True)
            else:
                st.info("No 'Most Urgent' tasks are currently pending.")
            st.markdown("---")

            # --- High Priority Tasks ---
            st.header("⚠️ High Priority Tasks")
            high_df = pending_tasks_df[pending_tasks_df['Priority'] == 'High']
            if not high_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_high = high_df['supervisor_office'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(officer_high, 'supervisor_office', 'Officer-wise High Priority Tasks', 'supervisor_office'), use_container_width=True)
                with col2:
                    dept_high = high_df['branch_name'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(dept_high, 'branch_name', 'Department-wise High Priority Tasks', 'branch_name'), use_container_width=True)
            else:
                st.info("No 'High' priority tasks are currently pending.")
            st.markdown("---")

            # --- Medium Priority Tasks ---
            st.header("🟡 Medium Priority Tasks")
            medium_df = pending_tasks_df[pending_tasks_df['Priority'] == 'Medium']
            if not medium_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_medium = medium_df['supervisor_office'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(officer_medium, 'supervisor_office', 'Officer-wise Medium Priority Tasks', 'supervisor_office'), use_container_width=True)
                with col2:
                    dept_medium = medium_df['branch_name'].value_counts().reset_index()
                    st.plotly_chart(create_bar_chart(dept_medium, 'branch_name', 'Department-wise Medium Priority Tasks', 'branch_name'), use_container_width=True)
            else:
                st.info("No 'Medium' priority tasks are currently pending.")

        else:
            st.warning("No pending tasks found to display.")
else:
    st.error("Failed to load data from the Google Sheet. Please check the URL and sheet permissions.")

