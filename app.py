
import streamlit as st
import pandas as pd
import html

st.set_page_config(
    page_title="Priority Scheduling with Aging Simulator",
    page_icon="⏱️",
    layout="wide"
)

st.title("Priority Scheduling with Aging Simulator")
st.write(
    "An Operating System scheduling simulator that uses "
    "priority scheduling with aging to reduce starvation."
)

st.info(
    "Priority 1 is the highest priority. "
    "Aging improves a waiting process's priority by reducing "
    "its priority number after each aging interval."
)

# -------------------------------
# Process Input
# -------------------------------
st.header("1. Enter Process Details")

default_data = pd.DataFrame({
    "Process ID": ["P1", "P2", "P3", "P4"],
    "Arrival Time": [0, 1, 2, 3],
    "Burst Time": [7, 4, 2, 3],
    "Priority": [3, 1, 4, 2]
})

process_df = st.data_editor(
    default_data,
    num_rows="dynamic",
    use_container_width=True,
    key="process_editor",
    column_config={
        "Process ID": st.column_config.TextColumn(
            "Process ID", required=True
        ),
        "Arrival Time": st.column_config.NumberColumn(
            "Arrival Time", min_value=0, step=1, required=True
        ),
        "Burst Time": st.column_config.NumberColumn(
            "Burst Time", min_value=1, step=1, required=True
        ),
        "Priority": st.column_config.NumberColumn(
            "Priority (1 = highest)",
            min_value=1,
            step=1,
            required=True
        )
    }
)

aging_interval = st.number_input(
    "Aging Interval",
    min_value=1,
    value=3,
    step=1,
    help="Number of waiting time units needed to improve priority by one level."
)

# -------------------------------
# Scheduling Algorithm
# -------------------------------
def priority_scheduling(processes, aging_interval):
    remaining = processes.copy()
    current_time = 0
    timeline = []
    results = []

    while remaining:

        # Find processes that have arrived
        ready = [
            p for p in remaining
            if p["Arrival Time"] <= current_time
        ]

        # If no process has arrived, CPU remains idle
        if not ready:
            next_arrival = min(
                p["Arrival Time"] for p in remaining
            )

            timeline.append({
                "Process": "IDLE",
                "Start": current_time,
                "End": next_arrival
            })

            current_time = next_arrival

            ready = [
                p for p in remaining
                if p["Arrival Time"] <= current_time
            ]

        # Calculate effective priority for waiting processes
        def effective_priority(p):
            waiting = current_time - p["Arrival Time"]
            improvement = waiting // aging_interval

            return max(
                1,
                p["Priority"] - improvement
            )

        # Lower priority number means higher priority
        selected = min(
            ready,
            key=lambda p: (
                effective_priority(p),
                p["Arrival Time"],
                p["Order"]
            )
        )

        start_time = current_time
        completion_time = start_time + selected["Burst Time"]

        waiting_time = start_time - selected["Arrival Time"]
        turnaround_time = completion_time - selected["Arrival Time"]

        results.append({
            "Process ID": selected["Process ID"],
            "Arrival Time": selected["Arrival Time"],
            "Burst Time": selected["Burst Time"],
            "Original Priority": selected["Priority"],
            "Effective Priority": effective_priority(selected),
            "Start Time": start_time,
            "Completion Time": completion_time,
            "Waiting Time": waiting_time,
            "Turnaround Time": turnaround_time
        })

        timeline.append({
            "Process": selected["Process ID"],
            "Start": start_time,
            "End": completion_time
        })

        current_time = completion_time
        remaining.remove(selected)

    return pd.DataFrame(results), timeline


# -------------------------------
# Run Simulation
# -------------------------------
if st.button("Run Scheduling Simulation", type="primary"):

    if process_df.empty:
        st.error("Please enter at least one process.")
        st.stop()

    if process_df.isnull().any().any():
        st.error("Please fill in all process details.")
        st.stop()

    process_df = process_df.copy()
    process_df["Process ID"] = (
        process_df["Process ID"].astype(str).str.strip()
    )

    if (process_df["Process ID"] == "").any():
        st.error("Process IDs cannot be empty.")
        st.stop()

    if process_df["Process ID"].duplicated().any():
        st.error("Each Process ID must be unique.")
        st.stop()

    numeric_columns = ["Arrival Time", "Burst Time", "Priority"]

    for col in numeric_columns:
        values = pd.to_numeric(process_df[col], errors="coerce")

        if values.isnull().any():
            st.error(f"{col} must contain valid numbers.")
            st.stop()

        if (values % 1 != 0).any():
            st.error(f"{col} must contain whole numbers.")
            st.stop()

        process_df[col] = values.astype(int)

    if (process_df["Arrival Time"] < 0).any():
        st.error("Arrival time cannot be negative.")
        st.stop()

    if (process_df["Burst Time"] <= 0).any():
        st.error("Burst time must be greater than zero.")
        st.stop()

    if (process_df["Priority"] < 1).any():
        st.error("Priority must be at least 1.")
        st.stop()

    processes = []

    for index, row in process_df.reset_index(drop=True).iterrows():
        processes.append({
            "Process ID": row["Process ID"],
            "Arrival Time": int(row["Arrival Time"]),
            "Burst Time": int(row["Burst Time"]),
            "Priority": int(row["Priority"]),
            "Order": index
        })

    results, timeline = priority_scheduling(
        processes, int(aging_interval)
    )

    # -------------------------------
    # Display Results
    # -------------------------------
    st.header("2. Scheduling Results")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Processes",
        len(results)
    )

    col2.metric(
        "Average Waiting Time",
        f"{results['Waiting Time'].mean():.2f}"
    )

    col3.metric(
        "Average Turnaround Time",
        f"{results['Turnaround Time'].mean():.2f}"
    )

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------
    # Gantt Chart
    # -------------------------------
    st.header("3. Gantt Chart")

    total_time = max(item["End"] for item in timeline)

    if total_time > 0:
        blocks = []

        for item in timeline:
            width = (
                (item["End"] - item["Start"])
                / total_time * 100
            )

            process_name = html.escape(item["Process"])

            blocks.append(
                f'<div style="width:{width}%;'
                'box-sizing:border-box;'
                'border:1px solid white;'
                'background-color:#dbeafe;'
                'color:#1e3a8a;'
                'padding:12px 2px;'
                'text-align:center;'
                'overflow-wrap:anywhere;'
                'font-weight:bold;">'
                f'{process_name}<br>'
                f'<small>{item["Start"]} - {item["End"]}</small>'
                '</div>'
            )

        st.markdown(
            '<div style="display:flex;width:100%;'
            'overflow:hidden;border-radius:6px;">'
            + "".join(blocks) +
            '</div>',
            unsafe_allow_html=True
        )

    # -------------------------------
    # Execution Order
    # -------------------------------
    st.header("4. Execution Order")

    execution_order = " → ".join(
        item["Process"] for item in timeline
    )

    st.success(execution_order)

    # -------------------------------
    # Download Results
    # -------------------------------
    st.header("5. Download Results")

    csv_data = results.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Results as CSV",
        data=csv_data,
        file_name="priority_scheduling_results.csv",
        mime="text/csv"
    )

    st.success("Scheduling simulation completed successfully!")

st.divider()

st.caption(
    "Priority Scheduling with Aging Simulator | "
    "Python + Streamlit | Non-preemptive scheduling"
)
