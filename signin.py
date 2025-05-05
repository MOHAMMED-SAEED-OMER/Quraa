import streamlit as st
import bcrypt
from db_handler import run_query

def signin():
    """
    Sign In page with Email & Password only.
    Renders the login form only if the user is not logged in.
    Otherwise, shows a 'already logged in' message.
    """
    st.title("Sign In")

    # If user is already logged in, skip the login form
    if st.session_state.get("user"):
        st.success(f"Already logged in as {st.session_state['user']['name']}")
        st.info("Use the sidebar to navigate.")
        return  # Do NOT call st.stop()

    # Otherwise, show manual Email/Password form
    st.subheader("Login with Email & Password")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign In with Email"):
        if not email or not password:
            st.warning("Please enter both email and password.")
            return

        # Check if user is in DB
        row = run_query(
            "SELECT user_id, username, password_hash FROM users WHERE email=%s",
            (email,)
        )
        if not row:
            st.error("Invalid email or password!")
            return

        user_id, db_username, db_hash = row[0]

        # Compare bcrypt
        if bcrypt.checkpw(password.encode("utf-8"), db_hash.encode("utf-8")):
            # Set user in session
            st.session_state["user"] = {"id": user_id, "name": db_username, "email": email}
            st.success(f"Logged in as {db_username} ({email})")
            st.info("Use the sidebar to navigate to other pages.")
        else:
            st.error("Invalid email or password!")
