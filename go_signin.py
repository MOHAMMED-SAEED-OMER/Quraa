import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

def google_signin():
    # Auto-trigger Google login
    if not st.experimental_user.is_logged_in:
        st.login()  # This immediately opens Google login popup
        st.stop()

    user_email = st.experimental_user.email
    user_name = st.experimental_user.name or "Unknown"
    default_role = "participant"  # or "user", depending on your model

    try:
        # Connect to DB
        with psycopg2.connect(st.secrets["neon"]["dsn"]) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if user already exists
                cur.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                user_record = cur.fetchone()

                if not user_record:
                    # Optionally auto-assign 'admin' to specific emails
                    admin_emails = st.secrets.get("admin_emails", [])
                    role = "admin" if user_email in admin_emails else default_role

                    # Insert new user
                    cur.execute("""
                        INSERT INTO users (username, email, role, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (user_name, user_email, role, datetime.datetime.now()))
                    conn.commit()
                else:
                    role = user_record["role"]

    except Exception as e:
        st.error("Error connecting to the database or fetching user info.")
        st.stop()

    return {"name": user_name, "email": user_email, "role": role}
