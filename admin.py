# admin.py
import streamlit as st
import psycopg2
from db_handler import get_connection  # You must have a get_connection() function

def admin_panel():
    st.title("🔐 Admin Panel - Manage User Roles")

    conn = get_connection()
    cur = conn.cursor()

    # Fetch all users and roles
    cur.execute("SELECT user_id, username, email, role FROM users ORDER BY created_at;")
    users = cur.fetchall()

    st.subheader("All Registered Users")
    for user_id, username, email, role in users:
        col1, col2, col3 = st.columns([4, 4, 4])
        with col1:
            st.write(f"**{username}** ({email})")
        with col2:
            new_role = st.selectbox(
                "Change Role",
                options=["user", "participant", "admin"],
                index=["user", "participant", "admin"].index(role),
                key=f"role_{user_id}"
            )
        with col3:
            if st.button("Update", key=f"update_{user_id}"):
                cur.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
                conn.commit()
                st.success(f"Updated role for {username} to {new_role}")

    cur.close()
    conn.close()
