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
        datetime.now() - df["Entry Date"]
    ).dt.days

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

    # Key Metrics
    total_tasks = filtered_df.shape[0]
    incomplete_tasks = filtered_df[
        filtered_df["Status"] != "Completed"
    ].shape[0]
    completed_tasks = filtered_df[
        filtered_df["Status"] == "Completed"
    ].shape[0]

    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tasks", total_tasks)
    with col2:
        st.metric("Incomplete Tasks", incomplete_tasks)
    with col3:
        st.metric("Completed Tasks", completed_tasks)

    st.markdown("---")

    # Display the filtered data in a table
    st.subheader("Filtered Task Data")
    st.dataframe(filtered_df)

    st.markdown("---")

    # --- Visualizations ---
    st.subheader("Visualizations")

    # Incomplete Tasks by Department
    incomplete_by_dept = (
        filtered_df[filtered_df["Status"] != "Completed"]
        .groupby("Dealing Branch ")
        .size()
        .reset_index(name="count")
    )
    fig_dept = px.bar(
        incomplete_by_dept,
        x="Dealing Branch ",
        y="count",
        title="Incomplete Tasks by Department",
        labels={"Dealing Branch ": "Department", "count": "Number of Incomplete Tasks"},
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_dept.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Incomplete Tasks",
    )


    # Incomplete Tasks by Priority
    incomplete_by_priority = (
        filtered_df[filtered_df["Status"] != "Completed"]
        .groupby("Priority")
        .size()
        .reset_index(name="count")
    )
    fig_priority = px.pie(
        incomplete_by_priority,
        names="Priority",
        values="count",
        title="Incomplete Tasks by Priority",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    # Display charts
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_dept, use_container_width=True)
    with col2:
        st.plotly_chart(fig_priority, use_container_width=True)


except Exception as e:
    st.error(f"An error occurred while loading or processing the data: {e}")
    st.warning(
        "Please make sure the Google Sheet is accessible and has the correct columns."
    )
