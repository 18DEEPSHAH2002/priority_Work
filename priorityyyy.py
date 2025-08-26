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
@st.cache_data
def load_data(url):
    """Loads and preprocesses data from the Google Sheet."""
    try:
        df = pd.read_csv(url)

        # Data Cleaning and Preparation
        df.columns = df.columns.str.strip()
        df['Pending Since'] = pd.to_datetime(df['Pending Since'], errors='coerce')
        df['Task Status'] = df['Task Status'].str.strip().fillna('Unknown')
        df['Officer Name'] = df['Officer Name'].str.strip().fillna('Unassigned')
        df['Department'] = df['Department'].str.strip().fillna('Unknown')
        df['Priority'] = df['Priority'].str.strip().fillna('Not Specified')
        return df
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return pd.DataFrame()

# --- Data Loading ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/export?format=csv&gid=213021534"
df = load_data(GOOGLE_SHEET_URL)

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Officer Pending Tasks", "Task Priority Dashboard"])
st.sidebar.markdown("---")
st.sidebar.info("This dashboard provides an overview of pending tasks based on the provided Google Sheet.")

# --- Main Application Logic ---
if not df.empty:
    # Filter for pending tasks
    pending_tasks_df = df[df['Task Status'].str.lower() == 'pending'].copy()

    if page == "Officer Pending Tasks":
        # --- Officer Pending Tasks Page ---
        st.title("👨‍💼 Officer Pending Tasks Overview")
        st.markdown("This page shows the number of pending tasks for each officer.")

        if not pending_tasks_df.empty:
            officer_pending_counts = pending_tasks_df['Officer Name'].value_counts().reset_index()
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

            # --- Function to prepare counts ---
            def prepare_counts(df, column_name):
                counts = df[column_name].value_counts().reset_index()
                counts.columns = [column_name, 'count']
                return counts

            # --- Most Urgent Tasks ---
            st.header("🚨 Most Urgent Tasks")
            most_urgent_df = pending_tasks_df[pending_tasks_df['Priority'] == 'Most Urgent']
            if not most_urgent_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_urgent = prepare_counts(most_urgent_df, 'Officer Name')
                    st.plotly_chart(create_bar_chart(officer_urgent, 'Officer Name', 'Officer-wise Most Urgent Tasks', 'Officer Name'), use_container_width=True)
                with col2:
                    dept_urgent = prepare_counts(most_urgent_df, 'Department')
                    st.plotly_chart(create_bar_chart(dept_urgent, 'Department', 'Department-wise Most Urgent Tasks', 'Department'), use_container_width=True)
            else:
                st.info("No 'Most Urgent' tasks are currently pending.")
            st.markdown("---")

            # --- High Priority Tasks ---
            st.header("⚠️ High Priority Tasks")
            high_df = pending_tasks_df[pending_tasks_df['Priority'] == 'High']
            if not high_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_high = prepare_counts(high_df, 'Officer Name')
                    st.plotly_chart(create_bar_chart(officer_high, 'Officer Name', 'Officer-wise High Priority Tasks', 'Officer Name'), use_container_width=True)
                with col2:
                    dept_high = prepare_counts(high_df, 'Department')
                    st.plotly_chart(create_bar_chart(dept_high, 'Department', 'Department-wise High Priority Tasks', 'Department'), use_container_width=True)
            else:
                st.info("No 'High' priority tasks are currently pending.")
            st.markdown("---")

            # --- Medium Priority Tasks ---
            st.header("🟡 Medium Priority Tasks")
            medium_df = pending_tasks_df[pending_tasks_df['Priority'] == 'Medium']
            if not medium_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    officer_medium = prepare_counts(medium_df, 'Officer Name')
                    st.plotly_chart(create_bar_chart(officer_medium, 'Officer Name', 'Officer-wise Medium Priority Tasks', 'Officer Name'), use_container_width=True)
                with col2:
                    dept_medium = prepare_counts(medium_df, 'Department')
                    st.plotly_chart(create_bar_chart(dept_medium, 'Department', 'Department-wise Medium Priority Tasks', 'Department'), use_container_width=True)
            else:
                st.info("No 'Medium' priority tasks are currently pending.")

        else:
            st.warning("No pending tasks found to display.")
else:
    st.error("Failed to load data from the Google Sheet. Please check the URL and sheet permissions.")
