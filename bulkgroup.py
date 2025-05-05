import streamlit as st
import pandas as pd
import openpyxl
from datetime import datetime, timedelta
from db_handler import run_query, run_command_returning, run_command

def fraction_packing(df, start_date, round_duration):
    """
    Distribute participants into rounds based on each row's 'Share Fraction'.
    Return a list: assigned_rounds[i] = { "round": <int>, "round_date": <datetime> }
    where i indexes the same rows in df.
    """

    # Safety check: we must have 'Share Fraction' in df
    if "Share Fraction" not in df.columns:
        st.error("Missing 'Share Fraction' column in uploaded file!")
        return []

    assigned = []
    round_number = 1
    accum_fraction = 0.0

    for _, row in df.iterrows():
        frac = row["Share Fraction"]
        if pd.isnull(frac) or not isinstance(frac, (int, float)):
            st.error(f"Invalid Share Fraction value: {frac}. Please fix your Excel file.")
            return []

        # If adding fraction overshoots 1.0 => start new round
        if accum_fraction + frac > 1.0:
            round_number += 1
            accum_fraction = 0.0

        # Compute round date
        if round_duration.lower() == "weekly":
            round_dt = start_date + timedelta(weeks=round_number - 1)
        else:  # monthly
            round_dt = start_date + timedelta(days=30 * (round_number - 1))

        assigned.append({
            "round": round_number,
            "round_date": round_dt
        })

        accum_fraction += frac
        # If exactly 1.0 => next round
        if abs(accum_fraction - 1.0) < 1e-9:
            round_number += 1
            accum_fraction = 0.0

    return assigned

def bulk_upload():
    """
    Bulk upload Quraa groups from Excel, generating data for:
      - groups
      - participants
      - rounds
      - contributions
      - receivables
    Then show a "Save" button to commit them to Neon DB.
    """
    st.subheader("Bulk Upload via Excel")

    # Show example table
    example_data = {
        "Group Name": ["Example Group"] * 3,
        "Start Date": ["2025-02-01"] * 3,
        "Round Duration": ["Monthly"] * 3,
        "Base Contribution": [100.0] * 3,
        "Participant Name": ["Alice", "Bob", "Charlie"],
        "Contact Info": ["alice@mail.com", "bob@mail.com", "charlie@mail.com"],
        "Share Fraction": [1.0, 0.5, 0.5]
    }
    example_df = pd.DataFrame(example_data)

    st.write("### 📌 Example Table Format")
    st.write("Ensure your Excel file follows this format before uploading:")
    st.dataframe(example_df)

    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")

            # Strip column names to avoid trailing spaces
            df.columns = df.columns.str.strip()

            required_columns = [
                "Group Name", "Start Date", "Round Duration", "Base Contribution",
                "Participant Name", "Contact Info", "Share Fraction"
            ]

            missing_cols = [c for c in required_columns if c not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                return

            # Convert data types
            df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
            df["Share Fraction"] = pd.to_numeric(df["Share Fraction"], errors="coerce")

            st.session_state["bulk_data"] = df  # store in session
            st.write("### 📝 Preview of uploaded data:")
            st.dataframe(df)

        except Exception as e:
            st.error(f"Error processing Excel file: {e}")
            return

    # After preview, let user confirm "Save Data"
    if "bulk_data" in st.session_state and not st.session_state.get("data_saved_bulk", False):
        if st.button("Save Data to Database"):
            df = st.session_state["bulk_data"]

            # 1) Extract group info from first row
            group_name = str(df.iloc[0]["Group Name"]).strip()
            start_date = df.iloc[0]["Start Date"]
            if pd.isnull(start_date):
                st.error("Invalid Start Date in the first row.")
                return
            round_duration = str(df.iloc[0]["Round Duration"]).strip()
            base_contribution = float(df.iloc[0]["Base Contribution"])

            # Check if group already exists
            grp_exists = run_query("SELECT group_id FROM groups WHERE group_name=%s", (group_name,))
            if grp_exists:
                st.error(f"Group '{group_name}' already exists. Please pick a new group name.")
                return

            # Insert group
            ins_grp_sql = """
            INSERT INTO groups (group_name, start_date, total_rounds, monthly_contribution)
            VALUES (%s, %s, %s, %s) RETURNING group_id
            """
            grp_id = run_command_returning(ins_grp_sql, (group_name, start_date.strftime("%Y-%m-%d"), 0, base_contribution))[0][0]

            # 2) fraction-packing => assigned_rounds
            assigned_rounds = fraction_packing(df, start_date, round_duration)
            if not assigned_rounds:
                st.error("Could not assign participants to rounds. Please check your 'Share Fraction' data.")
                return

            total_rounds = max(asg["round"] for asg in assigned_rounds)

            # 3) Insert participants & update contributions
            participant_ids = []
            for i, row in df.iterrows():
                pname = str(row["Participant Name"]).strip()
                contact = str(row["Contact Info"]).strip()
                share_frac = row["Share Fraction"]
                contribution = share_frac * base_contribution  # ✅ Fix contribution calculation
                assigned_r = assigned_rounds[i]["round"]

                ins_part_sql = """
                INSERT INTO participants (participant_name, group_id, participant_order, contribution, share_fraction, participant_contact_info)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING participant_id
                """
                pid = run_command_returning(ins_part_sql, (pname, grp_id, assigned_r, contribution, share_frac, contact))[0][0]
                participant_ids.append(pid)

            # 4) Insert rounds
            ins_round_sql = """
            INSERT INTO rounds (group_id, round_number, round_date, round_status)
            VALUES (%s, %s, %s, %s)
            """
            for asg in assigned_rounds:
                run_command(ins_round_sql, (grp_id, asg["round"], asg["round_date"].strftime("%Y-%m-%d"), "Pending"))

            # 5) Insert contributions
            ins_contrib_sql = """
            INSERT INTO contributions (group_id, round_number, participant_id, paid_yesno, paid_date)
            VALUES (%s, %s, %s, %s, %s)
            """
            for pid in participant_ids:
                for r in range(1, total_rounds + 1):
                    run_command(ins_contrib_sql, (grp_id, r, pid, "No", None))

            # 6) Insert receivables
            ins_recv_sql = """
            INSERT INTO receivables (group_id, round_number, participant_id, received_yesno, received_date, received_amount)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            for i, pid in enumerate(participant_ids):
                assigned_r = assigned_rounds[i]["round"]
                run_command(ins_recv_sql, (grp_id, assigned_r, pid, "No", None, 0.0))

            st.success(f"Group '{group_name}' added with updated contributions!")
            st.session_state["data_saved_bulk"] = True
