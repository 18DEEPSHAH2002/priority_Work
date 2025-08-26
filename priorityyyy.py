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
def load_data(url: str) -> pd.DataFrame:
    """
    Load & preprocess data from a Google Sheet CSV export URL.
    - Robust text cleanup (keeps true NaNs as empty string during cleaning).
    - Standardizes Priority (treats 'urgent' as 'most urgent').
    - Standardizes officer names so variants group together.
    - Calculates Days Pending only where date is valid.
    """
    df = pd.read_csv(url)

    # Clean header names
    df.columns = df.columns.str.strip()

    # Rename common headers to stable names (edit if your sheet uses different labels)
    df.rename(
        columns={
            "Entry Date": "Start Date",
            "Marked to Officer": "Assign To",
            "Status": "Task Status",
        },
        inplace=True,
    )

    # Convert date
    df["Start Date"] = pd.to_datetime(df.get("Start Date"), errors="coerce")

    # Clean text columns safely (preserve NaN by filling '' just for string ops)
    for col in ["Priority", "Task Status", "Dealing Branch", "Assign To"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
                .str.lower()
            )

    # --- Priority standardization (wider net) ---
    def standardize_priority(p: str) -> str:
        if not p:
            return "unknown"
        # treat any form of "urgent" as "most urgent"
        if "urgent" in p:
            return "most urgent"
        if "high" in p:
            return "high"
        if "medium" in p or "med" in p:
            return "medium"
        if "low" in p:
            return "low"
        return "unknown"

    if "Priority" in df.columns:
        df["Priority"] = df["Priority"].apply(standardize_priority)

    # --- Officer / assignee normalization so variants group together ---
    def normalize_officer(s: str) -> str:
        s = s.replace(".", " ")
        s = " ".join(s.split())  # collapse spaces
        # common buckets (customize freely)
        if "cmfo" in s:
            return "cmfo"
        if "dyesa" in s or "dy esa" in s:
            return "dyesa"
        if s.startswith("dro") or " dro" in s or s == "dro":
            return "dro"
        if "adc" in s and "ud" in s:
            return "adc ud"
        if "adc" in s and " g" in s:
            return "adc g"
        if s.startswith("ac ") and " g" in s:
            return "ac g"
        return s  # fallback

    if "Assign To" in df.columns:
        df["Assign To"] = df["Assign To"].apply(normalize_officer)

    # --- Task status: identify "done/closed" generically ---
    def is_done(status: str) -> bool:
        if not status:
            return False
        status = status.lower()
        done_keys = ["complete", "completed", "closed", "disposed", "resolved", "done"]
        return any(k in status for k in done_keys)

    if "Task Status" in df.columns:
        df["__is_done"] = df["Task Status"].apply(is_done)
    else:
        df["__is_done"] = False  # if no status col, treat as pending

    # --- Days Pending (only where Start Date is valid) ---
    df["Days Pending"] = (datetime.now() - df["Start Date"]).dt.days
    df.loc[df["Start Date"].isna(), "Days Pending"] = pd.NA
    df["Days Pending"] = df["Days Pending"].astype("Int64")

    return df


# --- Data Loading ---
sheet_id = "14howESk1k414yH06e_hG8mCE0HYUcR5VFTnbro4IdiU"
sheet_gid = "345729707"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"
df = load_data(GOOGLE_SHEET_URL)

# --- Sidebar Navigation ---
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio("Go to", ["Officer Pending Tasks", "Task Priority Dashboard"])
st.sidebar.markdown("---")
st.sidebar.info("Counts now include ALL non-completed tasks (even if Start Date is missing).")

# --- Helpers ---
def create_bar_chart(data: pd.DataFrame, x_axis: str, title: str, color_by: str):
    data = data.copy()
    data[x_axis] = data[x_axis].str.title()
    fig = px.bar(
        data,
        x=x_axis,
        y="count",
        title=title,
        text="count",
        color=color_by,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="Task Count", xaxis_title=x_axis.title(), showlegend=True)
    return fig


# --- Main App ---
if df.empty:
    st.error("Failed to load data. Please check the Google Sheet URL and permissions.")
    st.stop()

# IMPORTANT: Do NOT filter out rows with missing Start Date for counts
pending_df = df[~df["__is_done"]].copy()

# --- Page 1: Officer Pending Tasks ---
if page == "Officer Pending Tasks":
    st.title("👨‍💼 Officer Pending Tasks Overview")
    st.markdown("Counts include all non-completed tasks. Avg days uses only rows with a valid Start Date.")
    st.markdown("---")

    if pending_df.empty:
        st.warning("No pending tasks found to display.")
    else:
        # Counts per officer
        officer_counts = pending_df["Assign To"].value_counts(dropna=False).reset_index()
        officer_counts.columns = ["Officer", "Number of Pending Tasks"]

        # Avg pending days (only where we have a Start Date)
        avg_days = (
            pending_df[pending_df["Days Pending"].notna()]
            .groupby("Assign To")["Days Pending"]
            .mean()
            .round(0)
            .astype(int)
            .reset_index()
            .rename(columns={"Assign To": "Officer", "Days Pending": "Avg. Days Pending*"})
        )

        officer_summary = pd.merge(officer_counts, avg_days, on="Officer", how="left")
        officer_summary["Officer"] = officer_summary["Officer"].astype(str).str.title()

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Pending Task Summary")
            st.dataframe(officer_summary, use_container_width=True, hide_index=True)
            st.caption("(*) Average days computed for tasks that have a valid Start Date.")
        with col2:
            fig = px.bar(
                officer_summary,
                x="Officer",
                y="Number of Pending Tasks",
                title="Number of Pending Tasks per Officer",
                text="Number of Pending Tasks",
                color="Officer",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_title="Officer Name", yaxis_title="Count of Pending Tasks", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- Page 2: Task Priority Dashboard ---
elif page == "Task Priority Dashboard":
    st.title("📊 Task Priority Dashboard")
    st.markdown("Priority includes 'urgent' under **Most Urgent**. Counts use all non-completed tasks.")
    st.markdown("---")

    if pending_df.empty:
        st.warning("No pending tasks found to display.")
    else:
        # Key metrics
        total_pending = len(pending_df)
        most_urgent_count = (pending_df["Priority"] == "most urgent").sum()
        high_count = (pending_df["Priority"] == "high").sum()
        medium_count = (pending_df["Priority"] == "medium").sum()
        low_count = (pending_df["Priority"] == "low").sum()
        oldest_task_days = (
            pending_df["Days Pending"].dropna().max() if pending_df["Days Pending"].notna().any() else 0
        )

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Pending", total_pending)
        c2.metric("Most Urgent", int(most_urgent_count))
        c3.metric("High Priority", int(high_count))
        c4.metric("Medium Priority", int(medium_count))
        c5.metric("Oldest Task (Days)", int(oldest_task_days or 0))
        st.markdown("---")

        # Priority sections
        priority_levels = [
            ("Most Urgent", "most urgent", "🚨"),
            ("High", "high", "⚠️"),
            ("Medium", "medium", "🟡"),
            ("Low", "low", "🟢"),
        ]

        for label, key, icon in priority_levels:
            st.header(f"{icon} {label} Priority Tasks")
            p_df = pending_df[pending_df["Priority"] == key]

            if p_df.empty:
                st.info(f"No '{label}' priority tasks are currently pending.")
                st.markdown("---")
                continue

            col1, col2 = st.columns(2)

            with col1:
                officer_data = p_df["Assign To"].value_counts(dropna=False).reset_index()
                officer_data.columns = ["Assign To", "count"]
                st.plotly_chart(
                    create_bar_chart(officer_data, "Assign To", f"Officer-wise {label} Tasks", "Assign To"),
                    use_container_width=True,
                )

            with col2:
                dept_data = p_df["Dealing Branch"].value_counts(dropna=False).reset_index()
                dept_data.columns = ["Dealing Branch", "count"]
                st.plotly_chart(
                    create_bar_chart(dept_data, "Dealing Branch", f"Department-wise {label} Tasks", "Dealing Branch"),
                    use_container_width=True,
                )

            st.markdown("---")
