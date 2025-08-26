import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # Ensures the sidebar is open by default
)

# --- Force Light Theme ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] > .main {
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    """
    Loads data from the specified Google Sheet URL.
    The data is cached to improve performance.
    """
    # Construct the correct URL to download the Google Sheet as a CSV
    sheet_id = "14howESk1k414yH06e_hG8mCE0HYUcR5VFTnbro4IdiU"
    sheet_gid = "345729707"  # Specific GID for your sheet tab
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"
    
    try:
        # Read the data into a pandas DataFrame
        df = pd.read_csv(csv_url)
        
        # --- FIX 1: Strip leading/trailing whitespace from all column names ---
        df.columns = df.columns.str.strip()
        
        # --- FIX 2: Clean all relevant text columns for consistent grouping ---
        text_columns = ['Priority', 'Status', 'Dealing Branch', 'Assign To']
        for col in text_columns:
            if col in df.columns:
                # Use .astype(str) to handle potential non-string data before applying .str methods
                df[col] = df[col].astype(str).str.strip().str.lower()
        
        # --- Data Cleaning and Preprocessing ---
        # Rename columns to be more script-friendly
        df.rename(columns={
            'Entry Date': 'Start Date',
            'Marked to Officer': 'Assign To'
        }, inplace=True)

        # Convert date columns to datetime objects, handling potential errors
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}. Please ensure the sheet is public ('Anyone with the link can view') and the GID is correct.")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- Load Data ---
df = load_data()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
# Set "Officer Summary" as the default page by listing it first
page = st.sidebar.radio("Go to", ["Officer Summary", "Dashboard"])


# --- Main Application Logic ---
if not df.empty:
    # --- Pre-calculate pending tasks for use in all pages ---
    today = datetime.now()
    pending_tasks = pd.DataFrame()
    if 'Status' in df.columns and 'Start Date' in df.columns:
        pending_tasks = df[(df['Status'] != 'completed') & (df['Start Date'].notna()) & (pd.to_datetime(df['Start Date']) < today)]

    # --- Page 1: Dashboard ---
    if page == "Dashboard":
        st.title("📊 Task Management Analysis Dashboard")
        st.markdown("---")
        
        # --- Key Metrics ---
        st.header("Key Performance Indicators")

        # Filter data based on priority (using lowercase)
        most_urgent_tasks = df[df['Priority'] == 'most urgent']
        medium_priority_tasks = df[df['Priority'] == 'medium']
        high_priority_tasks = df[df['Priority'] == 'high']

        # Calculate metrics
        num_most_urgent = len(most_urgent_tasks)
        num_medium_priority = len(medium_priority_tasks)
        num_high_priority = len(high_priority_tasks)
        num_pending_tasks = len(pending_tasks)

        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pending Tasks", f"{num_pending_tasks} ⏳")
        col2.metric("Most Urgent", f"{num_most_urgent} 🔥")
        col3.metric("High Priority", f"{num_high_priority} 🔩")
        col4.metric("Medium Priority", f"{num_medium_priority} ⚠️")
        
        st.markdown("---")

        # --- Visualizations ---
        st.header("Task Distribution Analysis by Priority")
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            st.subheader("Most Urgent Tasks by Dealing Branch")
            if not most_urgent_tasks.empty:
                urgent_by_branch = most_urgent_tasks['Dealing Branch'].value_counts().reset_index()
                urgent_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig1 = px.bar(urgent_by_branch, x='Dealing Branch', y='Number of Tasks', title='Most Urgent Tasks per Dealing Branch', color='Dealing Branch', text='Number of Tasks')
                fig1.update_traces(textposition='outside')
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("No 'Most Urgent' tasks to display.")

            st.subheader("Medium Priority Tasks by Dealing Branch")
            if not medium_priority_tasks.empty:
                medium_by_branch = medium_priority_tasks['Dealing Branch'].value_counts().reset_index()
                medium_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig2 = px.bar(medium_by_branch, x='Dealing Branch', y='Number of Tasks', title='Medium Priority Tasks per Dealing Branch', color='Dealing Branch', text='Number of Tasks')
                fig2.update_traces(textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No 'Medium' priority tasks to display.")
                
            st.subheader("High Priority Tasks by Dealing Branch")
            if not high_priority_tasks.empty:
                high_by_branch = high_priority_tasks['Dealing Branch'].value_counts().reset_index()
                high_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig_high_branch = px.bar(high_by_branch, x='Dealing Branch', y='Number of Tasks', title='High Priority Tasks per Dealing Branch', color='Dealing Branch', text='Number of Tasks')
                fig_high_branch.update_traces(textposition='outside')
                st.plotly_chart(fig_high_branch, use_container_width=True)
            else:
                st.warning("No 'High' priority tasks to display.")

        with viz_col2:
            st.subheader("Most Urgent Tasks by Officer")
            if not most_urgent_tasks.empty:
                urgent_by_officer = most_urgent_tasks['Assign To'].value_counts().reset_index()
                urgent_by_officer.columns = ['Officer', 'Number of Tasks']
                fig3 = px.bar(urgent_by_officer, x='Officer', y='Number of Tasks', title='Most Urgent Tasks per Officer', color='Officer', text='Number of Tasks')
                fig3.update_traces(textposition='outside')
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("No 'Most Urgent' tasks to display.")

            st.subheader("Medium Priority Tasks by Officer")
            if not medium_priority_tasks.empty:
                medium_by_officer = medium_priority_tasks['Assign To'].value_counts().reset_index()
                medium_by_officer.columns = ['Officer', 'Number of Tasks']
                fig4 = px.bar(medium_by_officer, x='Officer', y='Number of Tasks', title='Medium Priority Tasks per Officer', color='Officer', text='Number of Tasks')
                fig4.update_traces(textposition='outside')
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.warning("No 'Medium' priority tasks to display.")
                
            st.subheader("High Priority Tasks by Officer")
            if not high_priority_tasks.empty:
                high_by_officer = high_priority_tasks['Assign To'].value_counts().reset_index()
                high_by_officer.columns = ['Officer', 'Number of Tasks']
                fig_high_officer = px.bar(high_by_officer, x='Officer', y='Number of Tasks', title='High Priority Tasks per Officer', color='Officer', text='Number of Tasks')
                fig_high_officer.update_traces(textposition='outside')
                st.plotly_chart(fig_high_officer, use_container_width=True)
            else:
                st.warning("No 'High' priority tasks to display.")

        st.markdown("---")
        
        # --- Incomplete Work Analysis Section ---
        st.header("📋 Detailed Incomplete Work Analysis")
        with st.expander("Click to view and filter all incomplete tasks"):
            if 'Status' in df.columns:
                incomplete_tasks = pending_tasks.copy()
                st.subheader("Filter Incomplete Tasks")
                analysis_type = st.radio("Analyze by:", ("Dealing Branch Wise", "Officer Wise"))

                if analysis_type == "Dealing Branch Wise":
                    branches = ['Select a Branch'] + sorted(incomplete_tasks['Dealing Branch'].dropna().unique().tolist())
                    selected_branch = st.selectbox("Select Dealing Branch", branches)
                    if selected_branch != 'Select a Branch':
                        filtered_df = incomplete_tasks[incomplete_tasks['Dealing Branch'] == selected_branch].copy()
                        st.markdown("---")
                        st.subheader(f"Found {len(filtered_df)} Incomplete Task(s) for {selected_branch}")
                        st.dataframe(
                            filtered_df[['Start Date', 'Dealing Branch', 'Assign To', 'Subject', 'File']],
                            column_config={"File": st.column_config.LinkColumn("PDF File Link")}
                        )

                elif analysis_type == "Officer Wise":
                    officers = ['Select an Officer'] + sorted(incomplete_tasks['Assign To'].dropna().unique().tolist())
                    selected_officer = st.selectbox("Select Officer", officers)
                    if selected_officer != 'Select an Officer':
                        filtered_df = incomplete_tasks[incomplete_tasks['Assign To'] == selected_officer].copy()
                        st.markdown("---")
                        st.subheader(f"Found {len(filtered_df)} Incomplete Task(s) for {selected_officer}")
                        st.dataframe(
                            filtered_df[['Start Date', 'Dealing Branch', 'Assign To', 'Subject', 'File']],
                            column_config={"File": st.column_config.LinkColumn("PDF File Link")}
                        )
            else:
                st.error("The 'Status' column is required for this analysis but was not found in the data.")

    # --- Page 2: Officer Summary ---
    elif page == "Officer Summary":
        st.title("👨‍💼 Officer-wise Pending Task Summary")
        st.markdown("---")
        
        if not pending_tasks.empty:
            st.header("Pending Task Count per Officer")
            officer_pending_counts = pending_tasks['Assign To'].value_counts().reset_index()
            officer_pending_counts.columns = ['Officer', 'Number of Pending Tasks']
            
            # Capitalize the officer names for better display
            officer_pending_counts['Officer'] = officer_pending_counts['Officer'].str.title()
            
            st.dataframe(officer_pending_counts, use_container_width=True)
        else:
            st.info("Congratulations! There are no pending tasks.")

else:
    st.warning("Could not load data. Please check the Google Sheet link and ensure its sharing permissions are set to 'Anyone with the link'.")
