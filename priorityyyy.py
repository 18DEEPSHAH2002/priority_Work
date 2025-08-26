import streamlit as st
import pandas as pd
import plotly.express as px

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
    It cleans column names, handles potential missing values, and calculates pending days.
    """
    try:
        # The URL is the direct CSV export link.
        df = pd.read_csv(url)

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
        
        # --- New Feature: Calculate Days Pending ---
        # Calculate the number of days a task has been pending from the 'Pending Since' date.
        # NaT (Not a Time) values in 'Pending Since' will result in NaN, which we fill with 0.
        df['Days Pending'] = (pd.to_datetime('today') - df['Pending Since']).dt.days
        df['Days Pending'] = df['Days Pending'].fillna(0).astype(int)

        return df
    except KeyError as e:
        st.error(f"Column Mismatch Error: Could not find the column {e} in your Google Sheet.")
        st.info("Please check your Google Sheet for the exact spelling and capitalization of the column headers.")
        # Try to load the data anyway and show the columns found for debugging
        try:
            temp_df = pd.read_csv(url)
            st.write("Here are the column names I found in your sheet:", temp_df.columns.tolist())
        except Exception as read_e:
            st.error(f"Could not even read the columns from the sheet. Error: {read_e}")
        return pd.DataFrame()
    except Exception as e:
        # Provide a more specific error message if data loading fails.
        st.error(f"An error occurred while loading the data: {e}")
        st.warning("Please ensure the Google Sheet is shared publicly ('Anyone with the link can view').")
        return pd.DataFrame()

# --- Data Loading ---
# Construct the direct CSV export URL from the sheet ID and GID.
sheet_id = "14howESk1k414yH06e_hG8mCE0HYUcR5VFTnbro4IdiU"
sheet_gid = "345729707"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"
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
        st.markdown("This page shows the number and average age of pending tasks for each officer.")
        st.markdown("---")

        if not pending_tasks_df.empty:
            # Count pending tasks for each officer.
            officer_pending_counts = pending_tasks_df['Officer Name'].value_counts().reset_index()
            officer_pending_counts.columns = ['Officer Name', 'Number of Pending Tasks']

            # --- New Feature: Calculate Average Pending Days ---
            avg_pending_days = pending_tasks_df.groupby('Officer Name')['Days Pending'].mean().round(0).astype(int).reset_index()
            avg_pending_days.rename(columns={'Days Pending': 'Avg. Days Pending'}, inplace=True)

            # Merge the counts and the average days into one summary table.
            officer_summary = pd.merge(officer_pending_counts, avg_pending_days, on='Officer Name')

            # Create two columns for the layout.
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Pending Task Summary")
                # Display the enhanced summary table.
                st.dataframe(officer_summary, use_container_width=True, hide_index=True)

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
            # --- New Feature: Oldest Task Metric ---
            oldest_task_days = pending_tasks_df['Days Pending'].max() if not pending_tasks_df.empty else 0


            # Display the key metrics in columns.
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Pending Tasks", total_pending)
            col2.metric("Most Urgent Tasks", most_urgent_count)
            col3.metric("High Priority Tasks", high_count)
            col4.metric("Medium Priority Tasks", medium_count)
            col5.metric("Oldest Task (Days)", oldest_task_days)
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
