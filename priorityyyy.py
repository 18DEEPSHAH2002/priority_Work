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

# --- Data Loading ---
@st.cache_data
def load_data():
    """Loads data from the Google Sheet."""
    sheet_url = "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/export?format=csv"
    df = pd.read_csv(sheet_url)
    return df

try:
    # Load the data
    df = load_data()

    # --- Data Preprocessing ---
    df["Entry Date"] = pd.to_datetime(df["Entry Date"], errors="coerce")
    df["Response Recieved on"] = pd.to_datetime(df["Response Recieved on"], errors="coerce")
    df["Days Since Start"] = ((datetime.now() - df["Entry Date"]).dt.days).fillna(0).astype(int)

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Data")
    departments = st.sidebar.multiselect(
        "Select Department",
        options=df["Dealing Branch "].unique(),
        default=df["Dealing Branch "].unique(),
    )
    officers = st.sidebar.multiselect(
        "Select Officer",
        options=df["Marked to Officer"].unique(),
        default=df["Marked to Officer"].unique(),
    )
    priorities = st.sidebar.multiselect(
        "Select Priority",
        options=df["Priority"].unique(),
        default=df["Priority"].unique(),
    )

    # Filter the DataFrame
    filtered_df = df.query(
        "`Dealing Branch ` == @departments & `Marked to Officer` == @officers & Priority == @priorities"
    )

    # --- Main Dashboard Display ---
    incomplete_df = filtered_df[filtered_df["Status"] != "Completed"].copy()

    # Key Metrics
    total_tasks = filtered_df.shape[0]
    incomplete_tasks = incomplete_df.shape[0]
    urgent_tasks = incomplete_df[incomplete_df["Priority"] == "Most Urgent"].shape[0]
    medium_priority_tasks = incomplete_df[incomplete_df["Priority"] == "Medium"].shape[0]

    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks (in selection)", total_tasks)
    col2.metric("Incomplete Tasks", incomplete_tasks)
    col3.metric("Urgent Tasks", urgent_tasks, delta_color="inverse")
    col4.metric("Medium Priority Tasks", medium_priority_tasks, delta_color="off")

    st.markdown("---")

    # Display the filtered data in a table, including the 'File' column
    st.subheader("Filtered Task Data")
    st.dataframe(filtered_df[[
        'Subject', 'File', 'Marked to Officer', 'Dealing Branch ', 
        'Priority', 'Status', 'Days Since Start'
    ]])
    
    st.markdown("---")

    # --- Visualizations ---
    st.subheader("Visualizations of Incomplete Tasks")

    # Department-wise breakdown for 'Urgent' tasks
    urgent_by_dept = (
        incomplete_df[incomplete_df["Priority"] == "Most Urgent"]
        .groupby("Dealing Branch ")
        .size()
        .reset_index(name="count")
    )
    fig_urgent_dept = px.bar(
        urgent_by_dept,
        x="Dealing Branch ",
        y="count",
        title="Urgent Tasks by Department",
        labels={"Dealing Branch ": "Department", "count": "Number of 'Urgent' Tasks"},
        color_discrete_sequence=px.colors.sequential.Reds_r,
    )

    # Officer-wise breakdown for 'Urgent' tasks
    urgent_by_officer = (
        incomplete_df[incomplete_df["Priority"] == "Most Urgent"]
        .groupby("Marked to Officer")
        .size()
        .reset_index(name="count")
    )
    fig_urgent_officer = px.bar(
        urgent_by_officer,
        x="Marked to Officer",
        y="count",
        title="Urgent Tasks by Officer",
        labels={"Marked to Officer": "Officer", "count": "Number of 'Urgent' Tasks"},
        color_discrete_sequence=px.colors.sequential.Purples_r,
    )

    # Display charts in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_urgent_dept, use_container_width=True)
    with col2:
        st.plotly_chart(fig_urgent_officer, use_container_width=True)


except Exception as e:
    st.error(f"An error occurred while loading or processing the data: {e}")
    st.warning(
        "Please make sure the Google Sheet is accessible and has the correct columns."
    )
