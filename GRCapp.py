import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_FILE = "tasks.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        date_cols = ["Project Start Date", "Project End Date", "Start Date", "Due Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    else:
        df = pd.DataFrame(columns=[
            "Project", "Purpose", "Project Start Date", "Project End Date",
            "Main Task", "Subtask", "Task ID", "Task Description",
            "R", "A", "C", "I", "Start Date", "Due Date", "Status", "Comments"
        ])
    return df

def save_data(df):
    df_copy = df.copy()
    for col in ["Project Start Date", "Project End Date", "Start Date", "Due Date"]:
        if col in df_copy.columns and pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime("%d/%m/%Y")
    df_copy.to_csv(DATA_FILE, index=False)

def generate_main_task_id(df, project):
    main_ids = df[df["Project"] == project]["Main Task"].dropna().astype(str)
    numeric_ids = [int(mid) for mid in main_ids if mid.isdigit()]
    return str(max(numeric_ids, default=0) + 1)

def generate_subtask_id(df, project, main_task_id):
    task_ids = df[
        (df["Project"] == project) &
        (df["Main Task"].astype(str) == str(main_task_id)) &
        (df["Subtask"].notna())
    ]["Task ID"].astype(str)

    subtasks_for_main = []
    for tid in task_ids:
        parts = tid.split(".")
        if len(parts) == 2 and parts[0] == str(main_task_id):
            try:
                subtasks_for_main.append(int(parts[1]))
            except ValueError:
                continue

    next_subtask_num = max(subtasks_for_main, default=0) + 1
    return str(next_subtask_num)

# --- App Title ---
st.title("📋 GRC Project Management")
df = load_data()

# --- Add New Project ---
st.subheader("📌 Define New Project")
with st.form("project_form"):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        new_project = st.text_input("New Project Name")
        new_purpose = st.text_input("Project Purpose")
    with col_p2:
        new_start = st.date_input("Project Start Date")
        new_end = st.date_input("Project End Date")
    add_project = st.form_submit_button("Save Project")
    if add_project:
        st.session_state["new_project"] = new_project
        st.session_state["new_purpose"] = new_purpose
        st.session_state["new_start"] = new_start
        st.session_state["new_end"] = new_end
        st.success(f"Project '{new_project}' defined.")

# --- Select Project ---
st.subheader("🧩 Select Project to Add Tasks")
existing_projects = df["Project"].dropna().unique().tolist()
if "new_project" in st.session_state and st.session_state["new_project"] not in existing_projects:
    existing_projects.insert(0, st.session_state["new_project"])
project = st.selectbox("Select Project", existing_projects)

if project:
    project_info = df[df["Project"] == project].iloc[0] if project in df["Project"].values else {
        "Purpose": st.session_state.get("new_purpose", ""),
        "Project Start Date": st.session_state.get("new_start", None),
        "Project End Date": st.session_state.get("new_end", None)
    }

    # --- Add Main Task ---
    st.subheader("🧱 Add Main Task")
    with st.form("main_task_form"):
        main_task_id = generate_main_task_id(df, project)
        st.markdown(f"**Generated Main Task ID:** `{main_task_id}`")
        desc = st.text_input("Task Description")
        start = pd.to_datetime(st.date_input("Start Date"))
        due = pd.to_datetime(st.date_input("Due Date"))
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
        comments = st.text_area("Comments")
        submit_main = st.form_submit_button("Add Main Task")
        if submit_main:
            task_id = main_task_id
            new_row = pd.DataFrame([[project, project_info["Purpose"], project_info["Project Start Date"],
                                     project_info["Project End Date"], main_task_id, "", task_id, desc,
                                     "", "", "", "", start, due, status, comments]],
                                   columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success(f"Main task {task_id} added.")

    # --- Add Subtask ---
    st.subheader("Add Subtask")
    main_tasks = sorted(df[df["Project"] == project]["Main Task"].dropna().astype(str).unique(), key=lambda x: int(x) if x.isdigit() else x)
    selected_main = st.selectbox("Select Main Task ID", main_tasks)
    if selected_main:
        sub_id = generate_subtask_id(df, project, selected_main)
        full_task_id = f"{selected_main}.{sub_id}"
        st.markdown(f"**Generated Subtask ID:** `{full_task_id}`")
        with st.form("subtask_form"):
            desc = st.text_input("Subtask Description")
            r = st.text_input("Responsible (R)")
            a = st.text_input("Accountable (A)")
            c = st.text_input("Consulted (C)")
            i = st.text_input("Informed (I)")
            start = pd.to_datetime(st.date_input("Subtask Start Date"))
            due = pd.to_datetime(st.date_input("Subtask Due Date"))
            status = st.selectbox("Subtask Status", ["Not Started", "In Progress", "Completed"])
            comments = st.text_area("Subtask Comments")
            submit_sub = st.form_submit_button("Add Subtask")
            if submit_sub:
                new_row = pd.DataFrame([[project, project_info["Purpose"], project_info["Project Start Date"],
                                         project_info["Project End Date"], selected_main, sub_id, full_task_id, desc,
                                         r, a, c, i, start, due, status, comments]],
                                       columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"Subtask {full_task_id} added.")

# --- Current Tasks View ---
st.subheader("📄 Current Tasks")
if project:
    filtered_df = df[df["Project"] == project]
    if not filtered_df.empty:
        st.markdown(f"**Project Purpose:** {filtered_df.iloc[0]['Purpose']}")
        st.markdown(f"**Timeline:** {filtered_df.iloc[0]['Project Start Date'].date()} to {filtered_df.iloc[0]['Project End Date'].date()}")
        st.dataframe(filtered_df.drop(columns=["Project", "Purpose", "Project Start Date", "Project End Date"]))
    else:
        st.info("No tasks found for this project.")

# --- Gantt Chart ---
if not df.empty and not df[df["Project"] == project].empty:
    timeline_df = df[df["Project"] == project].dropna(subset=["Start Date", "Due Date"]).copy()
    timeline_df["Start Date"] = pd.to_datetime(timeline_df["Start Date"], errors="coerce")
    timeline_df["Due Date"] = pd.to_datetime(timeline_df["Due Date"], errors="coerce")
    st.subheader("📊 Gantt-style Task Timeline (by Dates)")
    try:
        fig = px.timeline(
            timeline_df,
            x_start="Start Date",
            x_end="Due Date",
            y="Task Description",
            color="Status",
            hover_name="Task ID",
            title="Gantt-style Task Timeline (by Dates)"
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Plotting error: {e}")
