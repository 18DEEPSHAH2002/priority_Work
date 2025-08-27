# main_dashboard.py
# To run this app, save the code as a Python file (e.g., main_dashboard.py)
# and run the following command in your terminal:
# streamlit run main_dashboard.py
#
# Required libraries:
# pip install streamlit pandas plotly

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
# Set the layout to wide mode for a better dashboard experience
st.set_page_config(
    page_title="Task Management Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Data Loading and Cleaning ---
# Use Streamlit's caching to prevent re-loading data on every interaction.
@st.cache_data
def load_data():
    """
    Loads data from the specified Google Sheet, cleans it, and prepares it for visualization.
    - Filters out completed tasks.
    - Standardizes text data (strips whitespace, converts to consistent case).
    - Normalizes priority levels.
    - Converts date column to datetime objects.
    """
    # Construct the Google Sheet URL for CSV export
    sheet_id = "14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI"
    gid = "213021534"
    google_sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        # Read the data from Google Sheets into a pandas DataFrame
        df = pd.read_csv(google_sheet_url)

        # --- Data Cleaning Pipeline ---
        # 1. Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # 2. Strip whitespace from all object (text) columns
        for col in df.select_dtypes(['object']):
            df[col] = df[col].str.strip()

        # 3. Filter out tasks that are marked as 'Completed' (case-insensitive)
        df = df[df['Status'].str.lower() != 'completed']

        # 4. Standardize the 'Priority' column
        # Create a mapping for common variations
        priority_map = {
            'high priority': 'High',
            'medium priority': 'Medium',
            'low priority': 'Low'
        }
        # Apply mapping and capitalize the result for consistency
        df['Priority'] = df['Priority'].str.lower().replace(priority_map).str.title()
        
        # 5. Convert 'Date of Assign' to datetime objects for proper sorting and analysis
        # 'coerce' will turn any parsing errors into NaT (Not a Time)
        df['Date of Assign'] = pd.to_datetime(df['Date of Assign'], errors='coerce')

        return df

    except Exception as e:
        # If data loading fails, show an error message
        st.error(f"Error loading data from Google Sheet: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error

# Load the data using the function defined above
df_pending = load_data()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a page:", ["Officer Pending Tasks", "Task Priority Dashboard"])

# --- Main App Logic ---
# Display a message if the data could not be loaded
if df_pending.empty:
    st.warning("No pending tasks to display or data could not be loaded.")
else:
    # --- Page 1: Officer Pending Tasks ---
    if page == "Officer Pending Tasks":
        st.title("📊 Officer Pending Tasks Overview")
        st.markdown("This page provides a summary and detailed view of pending tasks assigned to officers.")

        # Calculate the number of pending tasks for each officer
        pending_by_officer = df_pending['Assign To'].value_counts().reset_index()
        pending_by_officer.columns = ['Officer', 'Pending Tasks']

        # --- Layout for Charts and Summary Table ---
        col1, col2 = st.columns((2, 1))

        with col1:
            # Bar chart showing pending tasks per officer
            st.subheader("Pending Tasks per Officer")
            fig = px.bar(
                pending_by_officer,
                x='Officer',
                y='Pending Tasks',
                title='Total Pending Tasks by Officer',
                labels={'Pending Tasks': 'Number of Pending Tasks'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(xaxis_title="Officer", yaxis_title="Number of Tasks")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Summary table of pending tasks per officer
            st.subheader("Summary Table")
            st.dataframe(pending_by_officer, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Detailed Pending Task List")
        
        # --- Interactive Filters for the Detailed List ---
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            # Department filter
            departments = ['All'] + sorted(df_pending['Dealing Branch'].unique().tolist())
            selected_dept = st.selectbox("Filter by Department (Dealing Branch):", departments)

        # Dynamically update officer list based on selected department
        if selected_dept == 'All':
            filtered_df_for_officer_list = df_pending
        else:
            filtered_df_for_officer_list = df_pending[df_pending['Dealing Branch'] == selected_dept]
        
        with filter_col2:
            # Officer filter
            officers = ['All'] + sorted(filtered_df_for_officer_list['Assign To'].unique().tolist())
            selected_officer = st.selectbox("Filter by Officer (Assign To):", officers)

        # Apply filters to the main dataframe
        final_filtered_df = df_pending.copy()
        if selected_dept != 'All':
            final_filtered_df = final_filtered_df[final_filtered_df['Dealing Branch'] == selected_dept]
        if selected_officer != 'All':
            final_filtered_df = final_filtered_df[final_filtered_df['Assign To'] == selected_officer]

        # Display the filtered dataframe with clickable links
        st.dataframe(
            final_filtered_df,
            column_config={
                "File": st.column_config.LinkColumn(
                    "File Link",
                    help="Click link to open the file.",
                    display_text="Open File"
                )
            },
            use_container_width=True
        )

    # --- Page 2: Task Priority Dashboard ---
    elif page == "Task Priority Dashboard":
        st.title("🚀 Task Priority Dashboard")
        st.markdown("This page provides an analysis of pending tasks based on their priority level.")
        
        # --- Key Performance Indicators (KPIs) ---
        total_pending = len(df_pending)
        high_priority = len(df_pending[df_pending['Priority'] == 'High'])
        medium_priority = len(df_pending[df_pending['Priority'] == 'Medium'])
        oldest_task_date = df_pending['Date of Assign'].min().strftime('%d %b %Y') if not df_pending['Date of Assign'].isnull().all() else "N/A"

        st.subheader("Key Metrics")
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("Total Pending Tasks", total_pending)
        kpi_col2.metric("High Priority Tasks", high_priority)
        kpi_col3.metric("Medium Priority Tasks", medium_priority)
        kpi_col4.metric("Oldest Task Date", oldest_task_date)
        
        st.markdown("---")

        # --- Charts for Priority Breakdown ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Grouped bar chart for officer workload by priority
            st.subheader("Workload by Priority (per Officer)")
            officer_priority_df = df_pending.groupby(['Assign To', 'Priority']).size().reset_index(name='count')
            fig_officer = px.bar(
                officer_priority_df,
                x='Assign To',
                y='count',
                color='Priority',
                title='Pending Tasks by Priority per Officer',
                labels={'count': 'Number of Tasks', 'Assign To': 'Officer'},
                barmode='group',
                color_discrete_map={'High': '#FF6B6B', 'Medium': '#FFD166', 'Low': '#06D6A0'}
            )
            st.plotly_chart(fig_officer, use_container_width=True)

        with chart_col2:
            # Grouped bar chart for department workload by priority
            st.subheader("Workload by Priority (per Department)")
            dept_priority_df = df_pending.groupby(['Dealing Branch', 'Priority']).size().reset_index(name='count')
            fig_dept = px.bar(
                dept_priority_df,
                x='Dealing Branch',
                y='count',
                color='Priority',
                title='Pending Tasks by Priority per Department',
                labels={'count': 'Number of Tasks', 'Dealing Branch': 'Department'},
                barmode='group',
                color_discrete_map={'High': '#FF6B6B', 'Medium': '#FFD166', 'Low': '#06D6A0'}
            )
            st.plotly_chart(fig_dept, use_container_width=True)
