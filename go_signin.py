import streamlit as st

def google_signin():
    """
    Uses Streamlit's built-in OIDC authentication.
    If the user is not logged in, shows a login button.
    Once logged in, retrieves user info from `st.experimental_user`.
    """
    st.title("Sign In with Google")

    # 1️⃣ Check if the user is already logged in
    if not st.experimental_user.is_logged_in:
        st.write("You are not logged in.")
        # Show a button to trigger Google login
        st.button("Log in with Google", on_click=st.login)
        st.stop()  # Stop script execution until login is complete

    # 2️⃣ Retrieve user details after successful login
    user_info = {
        "name": st.experimental_user.name or "Unknown User",
        "email": st.experimental_user.email or "Unknown Email"
    }

    st.success(f"Logged in as {user_info['name']} ({user_info['email']})")
    return user_info
