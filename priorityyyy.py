import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Management Dashboard",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Caching Function for Data Loading ---
@st.cache_data
def load_data(url):
    """Loads and preprocesses data from the Google Sheet."""
    try:
        df = pd.read_csv(url)
    except:
        df = pd.read_excel(url)

    # Only keep rows where "Sr" is present
    if "Sr" in df.columns:
        df = df[df["Sr"].notna()]  # remove rows without Sr value
    else:
        st.warning("⚠️ 'Sr' column not found. Dashboard will be empty.")
        df = pd.DataFrame()

    return df

# --- Load Data ---
st.sidebar.header("Data Source")
url = st.sidebar.text_input("Enter Google Sheet/CSV/Excel URL:", "")

if url:
    df = load_data(url)

    if not df.empty:
        st.title("📊 Task Management Dashboard")

        # --- Show Data Preview ---
        with st.expander("🔍 View Data"):
            st.dataframe(df)

        # --- Task Status Distribution ---
        if "Status" in df.columns:
            status_counts = df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            fig_status = px.pie(
                status_counts,
                names="Status",
                values="Count",
                title="Task Status Distribution",
                hole=0.4
            )
            st.plotly_chart(fig_status, use_container_width=True)

        # --- Tasks by Department ---
        if "Department" in df.columns:
            dept_counts = df["Department"].value_counts().reset_index()
            dept_counts.columns = ["Department", "Count"]

            fig_dept = px.bar(
                dept_counts,
                x="Department",
                y="Count",
                title="Tasks by Department",
                text="Count"
            )
            st.plotly_chart(fig_dept, use_container_width=True)

        # --- Tasks by Priority ---
        if "Priority" in df.columns:
            priority_counts = df["Priority"].value_counts().reset_index()
            priority_counts.columns = ["Priority", "Count"]

            fig_priority = px.bar(
                priority_counts,
                x="Priority",
                y="Count",
                title="Tasks by Priority",
                text="Count"
            )
            st.plotly_chart(fig_priority, use_container_width=True)

        # --- Task Timeline ---
        if "Deadline" in df.columns:
            try:
                df["Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")
                df_timeline = df.groupby("Deadline").size().reset_index(name="Tasks")

                fig_timeline = px.line(
                    df_timeline,
                    x="Deadline",
                    y="Tasks",
                    title="Task Timeline (Deadlines)",
                    markers=True
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            except Exception as e:
                st.warning(f"⚠️ Could not plot timeline: {e}")

    else:
        st.error("No valid data found (maybe missing 'Sr' column).")

else:
    st.info("👈 Enter a Google Sheet/CSV/Excel file URL in the sidebar to start.")
