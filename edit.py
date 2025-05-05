import streamlit as st
from db_handler import run_query, run_command

def edit():
    """
    Edit Groups or Participants in a DB-based Quraa system:
      - Edit Group Name (groups table)
      - Edit Participant Details (participants table)
      - Delete Group (remove from groups + references in participants, rounds, contributions, receivables)
    """

    st.title("Edit Groups or Participants")

    # For partial UI reset after deleting a group
    if "delete_confirmed" not in st.session_state:
        st.session_state["delete_confirmed"] = False

    st.subheader("Edit Options")
    option = st.selectbox(
        "Select an Option",
        ["Edit Group Name", "Edit Participant Details", "Delete Group"]
    )

    # ─────────────────────────────────────────────────────
    # 1) EDIT GROUP NAME
    # ─────────────────────────────────────────────────────
    if option == "Edit Group Name":
        # Fetch group_id + group_name from DB
        sql_groups = "SELECT group_id, group_name FROM groups ORDER BY group_name"
        group_rows = run_query(sql_groups)

        if not group_rows:
            st.info("No group data available to edit.")
            return

        # Convert to a dict {group_name -> group_id} for selection
        name_to_id = {}
        for (gid, gname) in group_rows:
            if gname:  # skip null
                name_to_id[gname] = gid

        if not name_to_id:
            st.warning("No valid group names found in 'groups' table.")
            return

        selected_name = st.selectbox("Select Group to Edit", list(name_to_id.keys()))
        new_group_name = st.text_input("New Group Name", value=selected_name)

        if st.button("Update Group Name"):
            group_id = name_to_id[selected_name]
            # Update the group_name in DB
            update_sql = """
            UPDATE groups
               SET group_name = %s
             WHERE group_id = %s
            """
            run_command(update_sql, (new_group_name.strip(), group_id))
            st.success(f"Group name updated from '{selected_name}' to '{new_group_name}' successfully!")

    # ─────────────────────────────────────────────────────
    # 2) EDIT PARTICIPANT DETAILS
    # ─────────────────────────────────────────────────────
    elif option == "Edit Participant Details":
        # Fetch participants
        sql_part = """
        SELECT participant_id, participant_name, contribution
          FROM participants
          ORDER BY participant_name
        """
        part_rows = run_query(sql_part)

        if not part_rows:
            st.info("No participant data available to edit.")
            return

        # Convert to a dict for easy selection
        # participant_name -> (participant_id, old_contribution)
        name_map = {}
        for (pid, pname, contrib) in part_rows:
            if pname:
                name_map[pname] = (pid, contrib if contrib else 0.0)

        if not name_map:
            st.warning("No valid participant names found in 'participants' table.")
            return

        selected_participant = st.selectbox("Select Participant", list(name_map.keys()))
        if selected_participant:
            pid, old_contribution = name_map[selected_participant]

            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("New Participant Name", value=selected_participant)
            with col2:
                new_contribution = st.number_input(
                    "New Participant Contribution",
                    value=float(old_contribution),
                    step=0.01
                )

            if st.button("Update Participant"):
                # Update the participant_name, contribution in DB
                update_part_sql = """
                UPDATE participants
                   SET participant_name = %s,
                       contribution = %s
                 WHERE participant_id = %s
                """
                run_command(update_part_sql, (new_name.strip(), new_contribution, pid))
                st.success(
                    f"Participant '{selected_participant}' updated to name='{new_name}', "
                    f"contribution={new_contribution}!"
                )

    # ─────────────────────────────────────────────────────
    # 3) DELETE GROUP
    # ─────────────────────────────────────────────────────
    elif option == "Delete Group":
        st.write(
            "Deleting a group will remove its row from the 'groups' table **and** "
            "any references in participants, rounds, contributions, and receivables, "
            "based on 'group_id'."
        )

        sql_groups = "SELECT group_id, group_name FROM groups ORDER BY group_name"
        group_rows = run_query(sql_groups)
        if not group_rows:
            st.info("No group data available for deletion.")
            return

        name_to_id = {}
        for (gid, gname) in group_rows:
            if gname:
                name_to_id[gname] = gid

        if not name_to_id:
            st.warning("No valid group names found.")
            return

        selected_gname = st.selectbox("Select Group to Delete", list(name_to_id.keys()))
        group_id = name_to_id[selected_gname]

        if not st.session_state["delete_confirmed"]:
            st.warning(f"You selected to delete group '{selected_gname}' (ID: {group_id}).")
            choice = st.selectbox("Are you sure?", ["Cancel", "Yes, Delete"])
            if choice == "Yes, Delete":
                st.error(f"This is permanent. Click below to confirm deletion of group '{selected_gname}'.")
                if st.button("Confirm Deletion"):
                    # Perform deletion from all relevant tables in correct order
                    try:
                        # 1) contributions (since it references participants)
                        run_command("DELETE FROM contributions WHERE group_id = %s", (group_id,))
                        # 2) receivables (references participants too)
                        run_command("DELETE FROM receivables WHERE group_id = %s", (group_id,))
                        # 3) rounds
                        run_command("DELETE FROM rounds WHERE group_id = %s", (group_id,))
                        # 4) participants
                        run_command("DELETE FROM participants WHERE group_id = %s", (group_id,))
                        # 5) groups
                        run_command("DELETE FROM groups WHERE group_id = %s", (group_id,))

                        st.success(
                            f"Group '{selected_gname}' (ID {group_id}) was deleted from 'groups' "
                            "and references removed from participants, rounds, contributions, receivables!"
                        )
                        st.session_state["delete_confirmed"] = True
                    except Exception as ex:
                        st.error(f"Error removing group references: {ex}")

        else:
            st.write("Group was deleted. You can now select another option.")
            if st.button("Reset Deletion State"):
                st.session_state["delete_confirmed"] = False

    return None
