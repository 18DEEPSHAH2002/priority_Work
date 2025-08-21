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
        
        # --- FIX 2: Strip leading/trailing whitespace from the 'Priority' and 'Status' column values ---
        if 'Priority' in df.columns:
            df['Priority'] = df['Priority'].str.strip()
        if 'Status' in df.columns:
            df['Status'] = df['Status'].str.strip()
        
        # --- Data Cleaning and Preprocessing ---
        # Rename columns to be more script-friendly
        df.rename(columns={
            'Entry Date': 'Start Date',
            'Marked to Officer': 'Assign To'
        }, inplace=True)

        # Convert date columns to datetime objects, handling potential errors
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        
        # NOTE: Removed the dropna() step to include all rows, even with missing data.
        # df.dropna(subset=['Priority', 'Dealing Branch', 'Assign To', 'Start Date'], inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}. Please ensure the sheet is public ('Anyone with the link can view') and the GID is correct.")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- Load Data ---
df = load_data()

# --- Main Application ---
st.title("📊 Task Management Analysis Dashboard")
st.markdown("---")

if not df.empty:
    # --- Key Metrics ---
    st.header("Key Performance Indicators")

    # Filter data based on priority
    most_urgent_tasks = df[df['Priority'] == 'Most Urgent']
    medium_priority_tasks = df[df['Priority'] == 'Medium']
    high_priority_tasks = df[df['Priority'] == 'High']
    
    # Calculate pending tasks
    today = datetime.now()
    pending_tasks = pd.DataFrame()
    if 'Status' in df.columns and 'Start Date' in df.columns:
        pending_tasks = df[(df['Status'] != 'Completed') & (df['Start Date'].notna()) & (pd.to_datetime(df['Start Date']) < today)]

    # Calculate metrics
    total_tasks = len(df)
    num_most_urgent = len(most_urgent_tasks)
    num_medium_priority = len(medium_priority_tasks)
    num_high_priority = len(high_priority_tasks)
    num_pending_tasks = len(pending_tasks)

    # Display metrics in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tasks", f"{total_tasks} 📝")
    col2.metric("Pending Tasks", f"{num_pending_tasks} ⏳")
    col3.metric("Most Urgent", f"{num_most_urgent} 🔥")
    col4.metric("High Priority", f"{num_high_priority} 🔩")
    col5.metric("Medium Priority", f"{num_medium_priority} ⚠️")
    

    st.markdown("---")

    # --- Visualizations ---
    st.header("Task Distribution Analysis by Priority")

    # Create two columns for the graphs
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
            # Using the 'pending_tasks' dataframe calculated earlier
            incomplete_tasks = pending_tasks.copy()

            st.subheader("Filter Incomplete Tasks")
            
            analysis_type = st.radio("Analyze by:", ("Dealing Branch Wise", "Officer Wise"))

            if analysis_type == "Dealing Branch Wise":
                # Handle potential NaN values in 'Dealing Branch' column for filtering
                branches = ['Select a Branch'] + sorted(incomplete_tasks['Dealing Branch'].dropna().unique().tolist())
                selected_branch = st.selectbox("Select Dealing Branch", branches)
                
                if selected_branch != 'Select a Branch':
                    filtered_df = incomplete_tasks[incomplete_tasks['Dealing Branch'] == selected_branch].copy()
                    
                    # Calculate pending days
                    filtered_df['Pending Days'] = (datetime.now() - filtered_df['Start Date']).dt.days
                    
                    st.markdown("---")
                    st.subheader(f"Found {len(filtered_df)} Incomplete Task(s) for {selected_branch}")
                    st.dataframe(
                        filtered_df[['Start Date', 'Dealing Branch', 'Assign To', 'Subject', 'File', 'Pending Days']],
                        column_config={
                            "File": st.column_config.LinkColumn("PDF File Link")
                        }
                    )

            elif analysis_type == "Officer Wise":
                # Handle potential NaN values in 'Assign To' column for filtering
                officers = ['Select an Officer'] + sorted(incomplete_tasks['Assign To'].dropna().unique().tolist())
                selected_officer = st.selectbox("Select Officer", officers)

                if selected_officer != 'Select an Officer':
                    filtered_df = incomplete_tasks[incomplete_tasks['Assign To'] == selected_officer].copy()

                    # Calculate pending days
                    filtered_df['Pending Days'] = (datetime.now() - filtered_df['Start Date']).dt.days

                    st.markdown("---")
                    st.subheader(f"Found {len(filtered_df)} Incomplete Task(s) for {selected_officer}")
                    st.dataframe(
                        filtered_df[['Start Date', 'Dealing Branch', 'Assign To', 'Subject', 'File', 'Pending Days']],
                        column_config={
                            "File": st.column_config.LinkColumn("PDF File Link")
                        }
                    )

        else:
            st.error("The 'Status' column is required for this analysis but was not found in the data.")

else:
    st.warning("Could not load data. Please check the Google Sheet link and ensure its sharing permissions are set to 'Anyone with the link'.")
