
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Task Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    .filter-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .priority-high { color: #dc3545; font-weight: bold; }
    .priority-medium { color: #fd7e14; font-weight: bold; }
    .priority-low { color: #198754; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_gsheet(sheet_url):
    """
    Load data from Google Sheet using Streamlit's connection feature
    """
    try:
        # Using st.connection for Google Sheets
        conn = st.connection("gsheets", type="GSheetsConnection")
        data = conn.read(spreadsheet=sheet_url, usecols=list(range(20)))  # Read first 20 columns
        return data
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {str(e)}")
        # Return sample data for demonstration if connection fails
        return create_sample_data()

def create_sample_data():
    """
    Create sample task data for demonstration purposes
    """
    sample_data = {
        'Task ID': ['TASK001', 'TASK002', 'TASK003', 'TASK004', 'TASK005', 'TASK006', 'TASK007', 'TASK008'],
        'Task Name': [
            'Review Budget Report',
            'Update Website Content', 
            'Prepare Monthly Presentation',
            'Conduct Team Meeting',
            'System Maintenance',
            'Client Follow-up',
            'Document Review',
            'Training Session'
        ],
        'Dealing Branch': ['Finance', 'IT', 'Finance', 'HR', 'IT', 'Sales', 'Legal', 'HR'],
        'Assign To': ['John Smith', 'Alice Johnson', 'John Smith', 'Bob Wilson', 'Alice Johnson', 'Carol Davis', 'Eve Brown', 'Bob Wilson'],
        'Priority': ['High', 'Medium', 'High', 'Low', 'Medium', 'High', 'Low', 'Medium'],
        'Status': ['Pending', 'Pending', 'Pending', 'Completed', 'Pending', 'Pending', 'Pending', 'Completed'],
        'Assigned Date': [
            '2024-08-20', '2024-08-22', '2024-08-15', '2024-08-25',
            '2024-08-23', '2024-08-18', '2024-08-21', '2024-08-24'
        ],
        'Due Date': [
            '2024-08-30', '2024-09-05', '2024-08-28', '2024-08-26',
            '2024-09-01', '2024-08-29', '2024-09-03', '2024-08-27'
        ],
        'File': [
            'https://example.com/budget-report', 'https://example.com/website-update',
            'https://example.com/presentation', 'https://example.com/meeting-notes',
            'https://example.com/maintenance', 'https://example.com/client-info',
            'https://example.com/document', 'https://example.com/training'
        ]
    }
    return pd.DataFrame(sample_data)

def clean_data(df):
    """
    Clean and standardize the data for consistent processing
    """
    if df.empty:
        return df

    # Clean column names - remove extra spaces and standardize
    df.columns = df.columns.str.strip()

    # Standardize text data
    text_columns = ['Dealing Branch', 'Assign To', 'Priority', 'Status']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Standardize Priority values
    if 'Priority' in df.columns:
        priority_mapping = {
            'High Priority': 'High', 'High': 'High', 'HIGH': 'High',
            'Medium Priority': 'Medium', 'Medium': 'Medium', 'MEDIUM': 'Medium',
            'Low Priority': 'Low', 'Low': 'Low', 'LOW': 'Low'
        }
        df['Priority'] = df['Priority'].map(priority_mapping).fillna(df['Priority'])

    # Standardize Status values
    if 'Status' in df.columns:
        status_mapping = {
            'Complete': 'Completed', 'Finished': 'Completed', 'Done': 'Completed',
            'In Progress': 'Pending', 'Ongoing': 'Pending', 'Open': 'Pending'
        }
        df['Status'] = df['Status'].map(status_mapping).fillna(df['Status'])

    return df

def filter_pending_tasks(df):
    """
    Filter out completed tasks to show only pending ones
    """
    if 'Status' in df.columns:
        return df[df['Status'].str.lower() != 'completed'].copy()
    return df

def create_officer_summary_chart(df):
    """
    Create bar chart showing pending tasks by officer
    """
    if df.empty or 'Assign To' not in df.columns:
        return None

    officer_counts = df['Assign To'].value_counts()

    fig = px.bar(
        x=officer_counts.index,
        y=officer_counts.values,
        labels={'x': 'Officer', 'y': 'Number of Pending Tasks'},
        title='Pending Tasks by Officer',
        color=officer_counts.values,
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_tickangle=-45
    )

    return fig

def create_department_summary_chart(df):
    """
    Create bar chart showing pending tasks by department
    """
    if df.empty or 'Dealing Branch' not in df.columns:
        return None

    dept_counts = df['Dealing Branch'].value_counts()

    fig = px.bar(
        x=dept_counts.index,
        y=dept_counts.values,
        labels={'x': 'Department', 'y': 'Number of Pending Tasks'},
        title='Pending Tasks by Department',
        color=dept_counts.values,
        color_continuous_scale='Greens'
    )

    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_tickangle=-45
    )

    return fig

def create_priority_breakdown_chart(df):
    """
    Create stacked bar chart showing priority breakdown by officer and department
    """
    if df.empty or not all(col in df.columns for col in ['Assign To', 'Priority']):
        return None, None

    # Priority breakdown by Officer
    priority_officer = df.groupby(['Assign To', 'Priority']).size().unstack(fill_value=0)

    fig_officer = go.Figure()
    colors = {'High': '#dc3545', 'Medium': '#fd7e14', 'Low': '#198754'}

    for priority in ['High', 'Medium', 'Low']:
        if priority in priority_officer.columns:
            fig_officer.add_trace(go.Bar(
                name=priority,
                x=priority_officer.index,
                y=priority_officer[priority],
                marker_color=colors.get(priority, '#6c757d')
            ))

    fig_officer.update_layout(
        barmode='stack',
        title='Task Priority Breakdown by Officer',
        xaxis_title='Officer',
        yaxis_title='Number of Tasks',
        height=400,
        xaxis_tickangle=-45
    )

    # Priority breakdown by Department
    if 'Dealing Branch' in df.columns:
        priority_dept = df.groupby(['Dealing Branch', 'Priority']).size().unstack(fill_value=0)

        fig_dept = go.Figure()

        for priority in ['High', 'Medium', 'Low']:
            if priority in priority_dept.columns:
                fig_dept.add_trace(go.Bar(
                    name=priority,
                    x=priority_dept.index,
                    y=priority_dept[priority],
                    marker_color=colors.get(priority, '#6c757d')
                ))

        fig_dept.update_layout(
            barmode='stack',
            title='Task Priority Breakdown by Department',
            xaxis_title='Department',
            yaxis_title='Number of Tasks',
            height=400,
            xaxis_tickangle=-45
        )
    else:
        fig_dept = None

    return fig_officer, fig_dept

def display_filtered_task_list(df, show_links=True):
    """
    Display the filtered task list with optional clickable links
    """
    if df.empty:
        st.info("No tasks match the current filters.")
        return

    # Prepare display dataframe
    display_df = df.copy()

    # Configure column display
    column_config = {}

    # Handle clickable links if File column exists
    if 'File' in df.columns and show_links:
        column_config['File'] = st.column_config.LinkColumn(
            'File Link',
            help='Click to open the file',
            max_chars=50
        )

    # Configure priority column with colors
    if 'Priority' in df.columns:
        column_config['Priority'] = st.column_config.TextColumn(
            'Priority',
            help='Task priority level'
        )

    # Display the dataframe with configuration
    st.dataframe(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )

    # Add priority styling with HTML if needed
    if 'Priority' in df.columns:
        st.markdown("""
        **Priority Legend:**
        - <span class="priority-high">High Priority</span>
        - <span class="priority-medium">Medium Priority</span>  
        - <span class="priority-low">Low Priority</span>
        """, unsafe_allow_html=True)

def officer_pending_tasks_page():
    """
    Main page showing officer pending tasks overview
    """
    st.markdown('<h1 class="main-header">📋 Officer Pending Tasks Overview</h1>', unsafe_allow_html=True)

    # Load and process data
    sheet_url = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/edit?gid=213021534#gid=213021534")

    with st.spinner("Loading data from Google Sheet..."):
        raw_data = load_data_from_gsheet(sheet_url)
        clean_df = clean_data(raw_data)
        pending_df = filter_pending_tasks(clean_df)

    if pending_df.empty:
        st.warning("No pending tasks found in the data.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Pending Tasks", len(pending_df))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        unique_officers = pending_df['Assign To'].nunique() if 'Assign To' in pending_df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Officers with Tasks", unique_officers)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        unique_depts = pending_df['Dealing Branch'].nunique() if 'Dealing Branch' in pending_df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Departments Involved", unique_depts)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        high_priority = len(pending_df[pending_df['Priority'] == 'High']) if 'Priority' in pending_df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("High Priority Tasks", high_priority)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Charts section
    col1, col2 = st.columns(2)

    with col1:
        officer_chart = create_officer_summary_chart(pending_df)
        if officer_chart:
            st.plotly_chart(officer_chart, use_container_width=True)

    with col2:
        dept_chart = create_department_summary_chart(pending_df)
        if dept_chart:
            st.plotly_chart(dept_chart, use_container_width=True)

    # Summary table
    st.subheader("📊 Summary by Officer")
    if 'Assign To' in pending_df.columns:
        summary_table = pending_df.groupby('Assign To').agg({
            'Task ID': 'count',
            'Priority': lambda x: f"H:{sum(x=='High')} M:{sum(x=='Medium')} L:{sum(x=='Low')}" if 'Priority' in pending_df.columns else 'N/A'
        }).rename(columns={'Task ID': 'Total Tasks', 'Priority': 'Priority Breakdown'})

        st.dataframe(summary_table, use_container_width=True)

    st.markdown("---")

    # Filters section
    st.subheader("🔍 Filter Tasks")

    # Create filters in sidebar
    with st.sidebar:
        st.markdown('<div class="filter-header">📋 Task Filters</div>', unsafe_allow_html=True)

        with st.form(key="task_filters"):
            # Department filter
            departments = ['All'] + sorted(pending_df['Dealing Branch'].unique()) if 'Dealing Branch' in pending_df.columns else ['All']
            selected_dept = st.selectbox("Select Department:", departments)

            # Officer filter (dynamic based on department)
            if selected_dept != 'All' and 'Dealing Branch' in pending_df.columns and 'Assign To' in pending_df.columns:
                dept_officers = pending_df[pending_df['Dealing Branch'] == selected_dept]['Assign To'].unique()
                officers = ['All'] + sorted(dept_officers)
            else:
                officers = ['All'] + sorted(pending_df['Assign To'].unique()) if 'Assign To' in pending_df.columns else ['All']

            selected_officer = st.selectbox("Select Officer:", officers)

            # Priority filter
            if 'Priority' in pending_df.columns:
                priorities = ['All'] + sorted(pending_df['Priority'].unique())
                selected_priority = st.selectbox("Select Priority:", priorities)
            else:
                selected_priority = 'All'

            apply_filters = st.form_submit_button("Apply Filters", type="primary")

    # Apply filters
    filtered_df = pending_df.copy()

    if apply_filters or 'filters_applied' not in st.session_state:
        if selected_dept != 'All' and 'Dealing Branch' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Dealing Branch'] == selected_dept]

        if selected_officer != 'All' and 'Assign To' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Assign To'] == selected_officer]

        if selected_priority != 'All' and 'Priority' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]

        st.session_state.filters_applied = True

    # Display filtered results
    st.subheader("📝 Detailed Task List")
    st.caption(f"Showing {len(filtered_df)} tasks")

    display_filtered_task_list(filtered_df)

def task_priority_dashboard_page():
    """
    Second page showing task priority analysis
    """
    st.markdown('<h1 class="main-header">🎯 Task Priority Dashboard</h1>', unsafe_allow_html=True)

    # Load and process data
    sheet_url = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/edit?gid=213021534#gid=213021534")

    with st.spinner("Loading data for priority analysis..."):
        raw_data = load_data_from_gsheet(sheet_url)
        clean_df = clean_data(raw_data)
        pending_df = filter_pending_tasks(clean_df)

    if pending_df.empty:
        st.warning("No pending tasks found for priority analysis.")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Pending", len(pending_df))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        high_count = len(pending_df[pending_df['Priority'] == 'High']) if 'Priority' in pending_df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("High Priority", high_count)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        medium_count = len(pending_df[pending_df['Priority'] == 'Medium']) if 'Priority' in pending_df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Medium Priority", medium_count)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        low_count = len(pending_df[pending_df['Priority'] == 'Low']) if 'Priority' in pending_df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Low Priority", low_count)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Find oldest task
    if 'Assigned Date' in pending_df.columns:
        try:
            pending_df['Assigned Date'] = pd.to_datetime(pending_df['Assigned Date'])
            oldest_task = pending_df.loc[pending_df['Assigned Date'].idxmin()]

            st.subheader("⏰ Oldest Pending Task")
            col1, col2 = st.columns([1, 3])
            with col1:
                days_old = (datetime.now() - oldest_task['Assigned Date']).days
                st.metric("Days Old", days_old)
            with col2:
                st.write(f"**Task:** {oldest_task.get('Task Name', 'N/A')}")
                st.write(f"**Assigned to:** {oldest_task.get('Assign To', 'N/A')}")
                st.write(f"**Department:** {oldest_task.get('Dealing Branch', 'N/A')}")
        except Exception as e:
            st.warning("Could not determine oldest task due to date format issues.")

    st.markdown("---")

    # Priority breakdown charts
    st.subheader("📊 Priority Analysis")

    fig_officer, fig_dept = create_priority_breakdown_chart(pending_df)

    if fig_officer:
        st.plotly_chart(fig_officer, use_container_width=True)

    if fig_dept:
        st.plotly_chart(fig_dept, use_container_width=True)

    # Priority distribution pie chart
    if 'Priority' in pending_df.columns:
        priority_counts = pending_df['Priority'].value_counts()

        fig_pie = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Overall Priority Distribution",
            color_discrete_map={'High': '#dc3545', 'Medium': '#fd7e14', 'Low': '#198754'}
        )

        st.plotly_chart(fig_pie, use_container_width=True)

def main():
    """
    Main application with navigation
    """
    # Initialize session state
    if 'filters_applied' not in st.session_state:
        st.session_state.filters_applied = False

    # Define pages
    pages = [
        st.Page(officer_pending_tasks_page, title="Officer Pending Tasks", icon="📋", default=True),
        st.Page(task_priority_dashboard_page, title="Task Priority Dashboard", icon="🎯")
    ]

    # Navigation
    pg = st.navigation(pages, position="sidebar", expanded=True)

    # Run the selected page
    pg.run()

if __name__ == "__main__":
    main()
