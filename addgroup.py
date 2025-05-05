import streamlit as st
from datetime import datetime, timedelta
from db_handler import run_command, run_command_returning
from bulkgroup import bulk_upload  # Import Bulk Upload functionality

def fraction_packing_preview(participants, start_date, round_duration):
    assigned = []
    round_number = 1
    accum_fraction = 0.0

    for p in participants:
        frac = p["fraction"]
        if accum_fraction + frac > 1.000000001:
            round_number += 1
            accum_fraction = 0.0

        if round_duration.lower() == "weekly":
            round_dt = start_date + timedelta(weeks=round_number - 1)
        else:
            round_dt = start_date + timedelta(days=30 * (round_number - 1))

        assigned.append({
            "round": round_number,
            "round_date": round_dt
        })

        accum_fraction += frac
        if abs(accum_fraction - 1.0) < 1e-9:
            round_number += 1
            accum_fraction = 0.0

    return assigned, accum_fraction

def add_group():
    """
    Add a new Quraa group with two tabs:
      1) Manual Entry
      2) Bulk Upload (Excel)
    """
    st.title("Add Group")

    tab1, tab2 = st.tabs(["Manual Entry", "Bulk Upload"])

    with tab1:
        st.subheader("Manual Entry")
        group_name = st.text_input("Group Name")
        start_date = st.date_input("Starting Date", datetime.now())
        round_duration = st.selectbox("Round Duration", ["Weekly", "Monthly"])
        base_contribution = st.number_input("Base Contribution per Full Share", min_value=0.0, step=0.01)
        num_participants = st.number_input("Number of Participants", min_value=1, step=1, value=1)

        if "participants_data" not in st.session_state:
            st.session_state["participants_data"] = []

        # Adjust session length
        if len(st.session_state["participants_data"]) < num_participants:
            for _ in range(num_participants - len(st.session_state["participants_data"])):
                st.session_state["participants_data"].append({
                    "name": "",
                    "contact": "",
                    "share_amount": 0.0,
                    "fraction": 0.0,
                })
        elif len(st.session_state["participants_data"]) > num_participants:
            st.session_state["participants_data"] = st.session_state["participants_data"][:num_participants]

        # Render each row
        for i in range(num_participants):
            p = st.session_state["participants_data"][i]
            c1, c2, c3, c4, c5 = st.columns([2,2,2,2,2])

            with c1:
                p["name"] = st.text_input(f"Participant {i+1} Name", value=p["name"], key=f"name_{i}")
            with c2:
                p["contact"] = st.text_input(f"Contact {i+1}", value=p["contact"], key=f"contact_{i}")

            new_share_amt = c3.number_input(f"Share Amt {i+1}", value=p["share_amount"], min_value=0.0, step=0.01, key=f"share_amt_{i}")
            new_frac = c4.number_input(f"Fraction {i+1}", value=p["fraction"], min_value=0.0, max_value=1.0, step=0.1, key=f"fraction_{i}")

            if abs(new_share_amt - p["share_amount"]) > 1e-9:
                p["share_amount"] = new_share_amt
                if base_contribution > 1e-9:
                    p["fraction"] = p["share_amount"] / base_contribution
                else:
                    p["fraction"] = 0.0
            elif abs(new_frac - p["fraction"]) > 1e-9:
                p["fraction"] = new_frac
                p["share_amount"] = p["fraction"] * base_contribution

            with c5:
                st.write(f"Receivable: {p['share_amount']:.2f}")

        # Show fraction packing preview
        assigned_list, leftover = fraction_packing_preview(st.session_state["participants_data"], start_date, round_duration)
        st.write("### Round Assignments Preview:")
        for i, asg in enumerate(assigned_list):
            p = st.session_state["participants_data"][i]
            st.write(f"{p['name']} => Round {asg['round']} on {asg['round_date'].strftime('%Y-%m-%d')}")

        if leftover > 1e-9:
            st.warning("Final round partial leftover, must sum exactly to 1.0 each round.")

        # Save Group button
        if st.button("Save Group (Manual)"):
            if not group_name.strip():
                st.error("Group Name cannot be empty.")
                return

            for i, p in enumerate(st.session_state["participants_data"], start=1):
                if p["fraction"] > 1.0:
                    st.error(f"Participant {i}: fraction {p['fraction']:.2f} > 1.0.")
                    return
                if not p["name"]:
                    st.error(f"Participant {i}: missing name.")
                    return

            assigned_final, leftover_final = fraction_packing_preview(st.session_state["participants_data"], start_date, round_duration)
            if leftover_final > 1e-9:
                st.error("Final round leftover => must be exactly 1.0 each round.")
                return

            final_rounds_count = assigned_final[-1]["round"] if assigned_final else 1

            # Insert group
            insert_group_sql = """
            INSERT INTO groups (group_name, start_date, total_rounds, monthly_contribution)
            VALUES (%s, %s, %s, %s)
            RETURNING group_id
            """
            group_result = run_command_returning(insert_group_sql, (group_name.strip(), start_date, final_rounds_count, base_contribution))
            new_group_id = group_result[0][0]

            # Insert participants
            insert_part_sql = """
            INSERT INTO participants (participant_name, group_id, participant_order, share_fraction, participant_contact_info)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING participant_id
            """
            participant_ids = []
            for i, p in enumerate(st.session_state["participants_data"], start=1):
                round_assigned = assigned_final[i-1]["round"]
                part_row = run_command_returning(insert_part_sql, (p["name"].strip(), new_group_id, round_assigned, p["fraction"], p["contact"].strip()))
                pid = part_row[0][0]
                participant_ids.append(pid)

            # Insert rounds
            insert_round_sql = """
            INSERT INTO rounds (group_id, round_number, round_date, round_status)
            VALUES (%s, %s, %s, %s)
            """
            for r in range(1, final_rounds_count + 1):
                if round_duration.lower() == "weekly":
                    rdate = start_date + timedelta(weeks=r - 1)
                else:
                    rdate = start_date + timedelta(days=30*(r-1))
                run_command(insert_round_sql, (new_group_id, r, rdate, "Pending"))

            # Insert contributions
            insert_contrib_sql = """
            INSERT INTO contributions (group_id, round_number, participant_id, paid_yesno, paid_date)
            VALUES (%s, %s, %s, %s, %s)
            """
            for pid in participant_ids:
                for r in range(1, final_rounds_count + 1):
                    run_command(insert_contrib_sql, (new_group_id, r, pid, "No", None))

            # Insert receivables
            insert_recv_sql = """
            INSERT INTO receivables (group_id, round_number, participant_id, received_yesno, received_date, received_amount)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            for i, pid in enumerate(participant_ids):
                assigned_r = assigned_final[i-1]["round"]
                run_command(insert_recv_sql, (new_group_id, assigned_r, pid, "No", None, 0.0))

            st.success(f"Group '{group_name}' added successfully!")
            st.session_state["participants_data"] = []

    with tab2:
        bulk_upload()
