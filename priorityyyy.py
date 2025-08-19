import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# --- Page Configuration ---
st.set_page_config(
    page_title="DC Ludhiana Task Dashboard",
    page_icon="📊",
    layout="wide",
)

# --- PDF Generation Function ---
def create_pdf(df):
    """Creates a PDF report from a DataFrame."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Title
    pdf.cell(0, 10, "Task Report", 0, 1, "C")
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    col_widths = [80, 40, 30, 30] # Column widths
    headers = ["Subject", "Marked to Officer", "Priority", "Days Since Start"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, "C")
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", "", 10)
    for index, row in df.iterrows():
        # Using multi_cell for the subject to handle long text
        subject = row.get("Subject", "N/A")
        officer = row.get("Marked to Officer", "N/A")
        priority = row.get("Priority", "N/A")
        days = str(row.get("Days Since Start", "N/A"))

        # Get current y position to align cells after multi_cell
        y_before = pdf.get_y()
        pdf.multi_cell(col_widths[0], 10, subject, 1)
        y_after = pdf.get_y()
        x_pos = pdf.get_x()
        
        # Reset position for the other cells to align with the start of the multi_cell row
        pdf.set_xy(x_pos + col_widths[0], y_before)

        pdf.cell(col_widths[1], y_after - y_before, officer, 1)
        pdf.cell(col_widths[2], y_after - y_before, priority, 1)
        pdf.cell(col_widths[3], y_after - y_before, days, 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')


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

    # Display the filtered data in a table
    st.subheader("Filtered Task Data")
    st.dataframe(filtered_df)
    
    # PDF Download Button
    pdf_data = create_pdf(filtered_df[['Subject', 'Marked to Officer', 'Priority', 'Days Since Start']])
    st.download_button(
        label="Download Report as PDF",
        data=pdf_data,
        file_name=f"task_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
    )


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
        color_discrete_sequence=px.colors.sequential.Redpurple_r,
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
