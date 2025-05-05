import streamlit as st
import bcrypt
from db_handler import run_query, run_command_returning

def hash_password(plain_pw: str) -> str:
    """Hash the plain text password using bcrypt."""
    hashed = bcrypt.hashpw(plain_pw.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_username_exists(username: str) -> bool:
    """Check if a username already exists in the 'users' table."""
    rows = run_query("SELECT user_id FROM users WHERE username=%s", (username,))
    return len(rows) > 0

def check_email_exists(email: str) -> bool:
    """Check if an email already exists in the 'users' table."""
    rows = run_query("SELECT user_id FROM users WHERE email=%s", (email,))
    return len(rows) > 0

def signup():
    st.title("Sign Up")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        # Basic validations
        if not username or not email or not password:
            st.error("All fields (username, email, password) are required.")
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return

        # Check if username or email is taken
        if check_username_exists(username):
            st.error("That username is already taken.")
            return
        if check_email_exists(email):
            st.error("That email is already taken.")
            return

        # Hash the password
        hashed_pw = hash_password(password)

        # Insert new user row
        insert_sql = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING user_id
        """
        result = run_command_returning(insert_sql, (username.strip(), email.strip(), hashed_pw))
        new_user_id = result[0][0]

        st.success("Account created successfully! You can now sign in.")
        st.info(f"Your user ID is {new_user_id} (for reference).")

# Optional: If you want to run just this page directly
if __name__ == "__main__":
    signup()
