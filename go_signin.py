import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

def google_signin():
    st.title("Sign In with Google")

    if not st.experimental_user.is_logged_in:
        st.write("You are not logged in.")
        st.button("Log in with Google", on_click=st.login)
        st.stop()

    user_email = st.experimental_user.email
    user_name = st.experimental_user.name or "Unknown"
    default_role = "user"

    # Connect to DB
    conn = psycopg2.connect(st.secrets["neon"]["dsn"])
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Check if user exists
    cur.execute("SELECT * FROM users WHERE email = %s", (user_email,))
    user_record = cur.fetchone()

    if not user_record:
        # Insert user with default role
        cur.execute("""
            INSERT INTO users (username, email, role, created_at)
            VALUES (%s, %s, %s, %s)
        """, (user_name, user_email, default_role, datetime.datetime.now()))
        conn.commit()
        role = default_role
    else:
        role = user_record["role"]

    cur.close()
    conn.close()

    st.success(f"Logged in as {user_name} ({user_email}) - Role: {role}")

    return {"name": user_name, "email": user_email, "role": role}
