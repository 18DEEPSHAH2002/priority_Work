import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="DC Ludhiana Task Dashboard",
    page_icon="📊",
    layout="wide",
)

# --- Title and Description ---
st.title("📊 DC Ludhiana Task Dashboard")
st.markdown("""
This dashboard provides an overview of ongoing tasks, allowing you to filter and analyze them by department, officer, and priority.
""")

# --- Data Loading ---
@st.cache_data
def load_data():
    """Loads data from the Google Sheet."""
    # Construct the correct URL to download the Google Sheet as a CSV
    sheet_url = "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/export?format=csv"
    df = pd.read_csv(sheet_url)
    return df

try:
    # Load the data
    df = load_data()

    # --- Data Preprocessing ---
    # Convert date columns to datetime objects, handling potential errors
    df["Entry Date"] = pd.to_datetime(df["Entry Date"], errors="coerce")
    df["Response Recieved on"] = pd.to_datetime(
        df["Response Recieved on"], errors="coerce"
    )

    # Calculate the number of days since the task started
    df["Days Since Start"] = (
        (datetime.now() - df["Entry Date"]).dt.days
    ).fillna(0).astype(int)


    # --- Sidebar Filters ---
    st.sidebar.header("Filter Data")

    # Filter by Department (Dealing Branch)
    departments = st.sidebar.multiselect(
        "Select Department",
        options=df["Dealing Branch "].unique(),
        default=df["Dealing Branch "].unique(),
    )

    # Filter by Officer (Marked to Officer)
    officers = st.sidebar.multiselect(
        "Select Officer",
        options=df["Marked to Officer"].unique(),
        default=df["Marked to Officer"].unique(),
    )

    # Filter by Priority
    priorities = st.sidebar.multiselect(
        "Select Priority",
        options=df["Priority"].unique(),
        default=df["Priority"].unique(),
    )

    # Filter the DataFrame based on user selections
    filtered_df = df.query(
        "`Dealing Branch ` == @departments & `Marked to Officer` == @officers & Priority == @priorities"
    )

    # --- Main Dashboard Display ---

    # Create a dataframe that excludes completed tasks for visualizations
    incomplete_df = filtered_df[filtered_df["Status"] != "Completed"].copy()


    # Key Metrics
    total_tasks = filtered_df.shape[0]
    incomplete_tasks = incomplete_df.shape[0]
    most_urgent_tasks = incomplete_df[incomplete_df["Priority"] == "Most Urgent"].shape[0]
    medium_priority_tasks = incomplete_df[incomplete_df["Priority"] == "Medium"].shape[0]


    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks (in selection)", total_tasks)
    with col2:
        st.metric("Incomplete Tasks", incomplete_tasks)
    with col3:
        st.metric("Most Urgent Tasks", most_urgent_tasks, delta_color="inverse")
    with col4:
        st.metric("Medium Priority Tasks", medium_priority_tasks, delta_color="off")


    st.markdown("---")

    # Display the filtered data in a table
    st.subheader("Filtered Task Data")
    st.dataframe(filtered_df)

    st.markdown("---")

    # --- Visualizations ---
    st.subheader("Visualizations of Incomplete Tasks")

    # Department-wise breakdown for 'Most Urgent' tasks
    most_urgent_by_dept = (
        incomplete_df[incomplete_df["Priority"] == "Most Urgent"]
        .groupby("Dealing Branch ")
        .size()
        .reset_index(name="count")
    )
    fig_most_urgent = px.bar(
        most_urgent_by_dept,
        x="Dealing Branch ",
        y="count",
        title="Most Urgent Tasks by Department",
        labels={"Dealing Branch ": "Department", "count": "Number of 'Most Urgent' Tasks"},
        color_discrete_sequence=px.colors.sequential.Reds_r,
    )
    fig_most_urgent.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Tasks",
    )

    # Department-wise breakdown for 'Medium' priority tasks
    medium_priority_by_dept = (
        incomplete_df[incomplete_df["Priority"] == "Medium"]
        .groupby("Dealing Branch ")
        .size()
        .reset_index(name="count")
    )
    fig_medium_priority = px.bar(
        medium_priority_by_dept,
        x="Dealing Branch ",
        y="count",
        title="Medium Priority Tasks by Department",
        labels={"Dealing Branch ": "Department", "count": "Number of 'Medium' Priority Tasks"},
        color_discrete_sequence=px.colors.sequential.Oranges_r,
    )
    fig_medium_priority.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Tasks",
    )


    # Display charts
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_most_urgent, use_container_width=True)
    with col2:
        st.plotly_chart(fig_medium_priority, use_container_width=True)


except Exception as e:
    st.error(f"An error occurred while loading or processing the data: {e}")
    st.warning(
        "Please make sure the Google Sheet is accessible and has the correct columns."
    )
