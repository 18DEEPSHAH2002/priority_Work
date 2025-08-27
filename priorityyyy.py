import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Task Management Dashboard", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=300)
def load_data(csv_url: str) -> pd.DataFrame:
    df = pd.read_csv(csv_url, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # Clean whitespace values
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # Rename common variants
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        if lc in ["assign to", "assign_to", "assignto", "assign to "]:
            rename_map[c] = "Assign To"
        if lc in ["dealing branch", "dealing_branch", "dealingbranch"]:
            rename_map[c] = "Dealing Branch"
        if lc in ["priority", "priority level"]:
            rename_map[c] = "Priority"
        if lc in ["task status", "status"]:
            rename_map[c] = "Task Status"
        if lc in ["file", "open file", "open_file", "openfile"]:
            rename_map[c] = "File"
        if lc in ["start date", "start_date"]:
            rename_map[c] = "Start Date"
        if lc in ["days pending", "days_pending"]:
            rename_map[c] = "Days Pending"

    df = df.rename(columns=rename_map)

    # Ensure key columns
    if "Assign To" not in df.columns:
        df["Assign To"] = "Unknown"
    if "Dealing Branch" not in df.columns:
        df["Dealing Branch"] = "Unknown"
    if "Priority" not in df.columns:
        df["Priority"] = "Unspecified"
    if "Task Status" not in df.columns:
        df["Task Status"] = "open"

    # Normalize priority values
    def normalize_priority(x):
        if pd.isna(x):
            return "Unspecified"
        s = str(x).strip().lower()
        if s in ["high", "high priority", "most urgent", "urgent", "1"]:
            return "High"
        if s in ["medium", "med", "2"]:
            return "Medium"
        if s in ["low", "low priority", "3"]:
            return "Low"
        return x.title()

    df["Priority"] = df["Priority"].apply(normalize_priority)

    # Filter out completed
    df["Task Status"] = df["Task Status"].str.strip().str.lower()
    df = df[~df["Task Status"].isin(["completed", "complete", "done", "closed"])].copy()

    # Days Pending
    if "Days Pending" in df.columns:
        df["Days Pending"] = pd.to_numeric(df["Days Pending"], errors="coerce")
    else:
        df["Days Pending"] = np.nan

    df["Officer"] = df["Assign To"].astype(str).str.strip()

    # File links
    if "File" in df.columns:
        def make_link(x):
            if pd.isna(x) or str(x).strip() == "":
                return ""
            href = str(x).strip()
            if not href.lower().startswith(("http://", "https://")):
                return href
            return f"<a href=\"{href}\" target=\"_blank\">{href}</a>"
        df["File_Link"] = df["File"].apply(make_link)
    else:
        df["File_Link"] = ""

    return df

# -----------------------------
# App
# -----------------------------
st.title("Officer Pending Tasks Overview 🧾")
st.caption("Loads data directly from your Google Sheet and visualizes pending tasks.")

# Default CSV export URL derived from the sheet link you provided
default_csv = "https://docs.google.com/spreadsheets/d/14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/export?format=csv&gid=213021534"

st.sidebar.header("Data source")
csv_url = st.sidebar.text_input(
    "Google Sheet CSV export URL",
    value=default_csv,
    help="Public Google Sheet CSV export URL. Ensure the sheet is shared as 'Anyone with the link can view' or published to web."
)

with st.spinner("Loading data..."):
    try:
        df = load_data(csv_url)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

# Pages
page = st.sidebar.radio("Select page", ["Officer Pending Tasks", "Task Priority Dashboard"]) 

# Aggregations
agg_officer = df.groupby("Officer").agg(
    Number_of_Pending_Tasks=("Officer", "count"),
    Avg_Days_Pending=("Days Pending", "mean")
).reset_index()
agg_officer["Avg_Days_Pending"] = agg_officer["Avg_Days_Pending"].round(0).fillna(0).astype(int)

if page == "Officer Pending Tasks":
    st.header("Visual Distribution")
    fig = px.bar(
        agg_officer.sort_values("Number_of_Pending_Tasks", ascending=False),
        x="Officer", y="Number_of_Pending_Tasks", text="Number_of_Pending_Tasks", height=420
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pending Task Summary")
    st.dataframe(agg_officer.rename(columns={
        "Officer": "Officer",
        "Number_of_Pending_Tasks": "Number of Pending Tasks",
        "Avg_Days_Pending": "Avg. Days Pending"
    }).sort_values("Number of Pending Tasks", ascending=False))

    st.markdown("---")
    st.subheader("🔎 Filter and View Pending Task Details")

    departments = ["All"] + sorted(df["Dealing Branch"].fillna("Unknown").unique().tolist())
    selected_dept = st.selectbox("Select a Department", departments)

    if selected_dept == "All":
        officers = ["All"] + sorted(df["Officer"].fillna("Unknown").unique().tolist())
    else:
        officers = ["All"] + sorted(df.loc[df["Dealing Branch"] == selected_dept, "Officer"].fillna("Unknown").unique().tolist())

    selected_officer = st.selectbox("Select an Officer", officers)

    rows = df.copy()
    if selected_dept != "All":
        rows = rows[rows["Dealing Branch"] == selected_dept]
    if selected_officer != "All":
        rows = rows[rows["Officer"] == selected_officer]

    display_cols = [c for c in [
        "Sr", "Assign To", "Officer", "Dealing Branch", "Priority", "Subject", "Received From",
        "Open File", "Start Date", "Task Status", "Response Received", "Response Received on", "Remarks", "Days Pending", "File", "File_Link"
    ] if c in rows.columns]

    if "File_Link" in rows.columns:
        st.markdown("**Click on file links to open**")
        def df_to_html_table(df_view, columns):
            html = "<table style='width:100%; border-collapse: collapse;'>"
            html += "<thead><tr>"
            for col in columns:
                html += f"<th style='text-align:left; padding:8px; border-bottom:1px solid #ddd'>{col}</th>"
            html += "</tr></thead><tbody>"
            for _, r in df_view.iterrows():
                html += "<tr>"
                for col in columns:
                    v = r.get(col, "")
                    if pd.isna(v):
                        v = ""
                    html += f"<td style='padding:6px; border-bottom:1px solid #f1f1f1'>{v}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            return html
        html_table = df_to_html_table(rows[display_cols], display_cols)
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.dataframe(rows[display_cols])

    st.caption("Tasks with status 'completed' or 'done' are excluded automatically.")

elif page == "Task Priority Dashboard":
    st.header("Task Priority Dashboard")
    total_pending = len(df)
    counts_by_priority = df["Priority"].value_counts().to_dict()
    oldest_task_days = int(df["Days Pending"].max() if df["Days Pending"].notna().any() else 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pending Tasks", total_pending)
    col2.metric("Oldest Task (days)", oldest_task_days)
    col3.metric("Distinct Officers", df["Officer"].nunique())

    st.subheader("Counts by Priority")
    st.write(pd.DataFrame.from_dict(counts_by_priority, orient="index", columns=["count"]).reset_index().rename(columns={"index": "Priority"}))

    st.subheader("Workload by Priority and Officer")
    pivot = df.pivot_table(index="Officer", columns="Priority", values="Subject", aggfunc="count", fill_value=0).reset_index()
    if pivot.shape[0] > 0:
        fig2 = px.bar(pivot, x="Officer", y=[c for c in pivot.columns if c != "Officer"], title="Tasks per Officer by Priority", height=450)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Workload by Priority and Department")
    pivot_dept = df.pivot_table(index="Dealing Branch", columns="Priority", values="Subject", aggfunc="count", fill_value=0).reset_index()
    if pivot_dept.shape[0] > 0:
        fig3 = px.bar(pivot_dept, x="Dealing Branch", y=[c for c in pivot_dept.columns if c != "Dealing Branch"], title="Tasks per Department by Priority", height=450)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("Table: Pending Tasks (priority view)")
    st.dataframe(df.sort_values(["Priority", "Days Pending"], ascending=[True, False]))

st.write("\n---\nBuilt with ❤️ using Streamlit")
