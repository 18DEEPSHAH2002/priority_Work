import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Management Dashboard",
    page_icon="✅",
    layout="wide",
)

# --- Caching Function for Data Loading ---
@st.cache_data
def load_data(url):
    """
    Loads and preprocesses data from the specified Google Sheet URL.
    """
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        # Rename columns
        df.rename(columns={
            'Entry Date': 'Start Date',
            'Marked to Officer': 'Assign To',
            'Status': 'Task Status' 
        }, inplace=True)

        # Convert dates
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')

        # Clean text columns
        text_columns = ['Priority', 'Task Status', 'Dealing Branch', 'Assign To']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower().fillna('unknown')

        # Standardize priority
        def standardize_priority(priority_text):
            if 'most urgent' in priority_text:
                return 'most urgent'
            elif 'high' in priority_text:
                return 'high'
            elif 'medium' in priority_text:
                return 'medium'
            else:
                return 'unknown'

        if 'Priority' in df.columns:
            df['Priority'] = df['Priority'].apply(standardize_priority)

        # Days pending
        df['Days Pending'] = (datetime.now() - df['Start Date']).dt.days
        df['Days Pending'] = df['Days Pending'].fillna(0).astype(int)

        return df
    except KeyError as e:
        st.error(f"Column Mismatch Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- Data Loading ---
sheet_id = "14howESk1k414yH06e_hG8mCE0HYUcR5VFTnbro4IdiU"
sheet_gid = "345729707"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"
df = load_data(GOOGLE_SHEET_URL)

# --- Sidebar Navigation ---
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio("Go to", ["Officer Pending Tasks", "Task Priority Dashboard"])
st.sidebar.markdown("---")
st.sidebar.info("This dashboard provides an overview of pending tasks from the Google Sheet.")

# --- Main App ---
if not df.empty:
    pending_tasks_df = df[(df['Task Status'] != 'completed') & (df['Start Date'].notna())].copy()

    # --- Page 1: Officer Pending Tasks ---
    if page == "Officer Pending Tasks":
        st.title("👨‍💼 Officer Pending Tasks Overview")
        st.markdown("---")

        if not pending_tasks_df.empty:
            officer_pending_counts = pending_tasks_df['Assign To'].value_counts().reset_index()
            officer_pending_counts.columns = ['Officer', 'Number of Pending Tasks']

            avg_pending_days = pending_tasks_df.groupby('Assign To')['Days Pending'].mean().round(0).astype(int).reset_index()
            avg_pending_days.rename(columns={'Days Pending': 'Avg. Days Pending', 'Assign To': 'Officer'}, inplace=True)

            officer_summary = pd.merge(officer_pending_counts, avg_pending_days, on='Officer')
            officer_summary['Officer'] = officer_summary['Officer'].str.title()

            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("Pending Task Summary")
                st.dataframe(officer_summary, use_container_width=True, hide_index=True)
            with col2:
                st.subheader("Visual Distribution")
                fig = px.bar(
                    officer_summary,
                    x='Officer',
                    y='Number of Pending Tasks',
                    title='Number of Pending Tasks per Officer',
                    text='Number of Pending Tasks',
                    color='Officer',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(xaxis_title="Officer Name", yaxis_title="Count of Pending Tasks", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No pending tasks found to display.")

    # --- Page 2: Task Priority Dashboard ---
    elif page == "Task Priority Dashboard":
        st.title("📊 Task Priority Dashboard")
        st.markdown("---")

        if not pending_tasks_df.empty:
            # --- Key Metrics ---
            st.header("High-Level Summary")
            total_pending = pending_tasks_df.shape[0]
            most_urgent_count = pending_tasks_df[pending_tasks_df['Priority'] == 'most urgent'].shape[0]
            high_count = pending_tasks_df[pending_tasks_df['Priority'] == 'high'].shape[0]
            medium_count = pending_tasks_df[pending_tasks_df['Priority'] == 'medium'].shape[0]
            oldest_task_days = pending_tasks_df['Days Pending'].max() if not pending_tasks_df.empty else 0

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Pending", total_pending)
            col2.metric("Most Urgent", most_urgent_count)
            col3.metric("High Priority", high_count)
            col4.metric("Medium Priority", medium_count)
            col5.metric("Oldest Task (Days)", oldest_task_days)
            st.markdown("---")

            def create_bar_chart(data, x_axis, title, color_by):
                data[x_axis] = data[x_axis].str.title()
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
                fig.update_layout(yaxis_title="Task Count", showlegend=True)
                return fig

            # --- Priority Sections ---
            priority_levels = {
                "Most Urgent": "🚨",
                "High": "⚠️",
                "Medium": "🟡"
            }

            for priority, icon in priority_levels.items():
                st.header(f"{icon} {priority} Priority Tasks")
                priority_df = pending_tasks_df[pending_tasks_df['Priority'] == priority.lower()]
                
                if not priority_df.empty:
                    col1, col2 = st.columns(2)

                    with col1:
                        officer_data = priority_df['Assign To'].value_counts().reset_index()
                        officer_data.columns = ['Assign To', 'count']
                        st.plotly_chart(create_bar_chart(officer_data, 'Assign To', f'Officer-wise {priority} Tasks', 'Assign To'), use_container_width=True)

                    with col2:
                        dept_data = priority_df['Dealing Branch'].value_counts().reset_index()
                        dept_data.columns = ['Dealing Branch', 'count']
                        st.plotly_chart(create_bar_chart(dept_data, 'Dealing Branch', f'Department-wise {priority} Tasks', 'Dealing Branch'), use_container_width=True)

                else:
                    st.info(f"No '{priority}' priority tasks are currently pending.")
                st.markdown("---")

        else:
            st.warning("No pending tasks found to display.")
else:
    st.error("Failed to load data. Please check the Google Sheet URL and permissions.")
