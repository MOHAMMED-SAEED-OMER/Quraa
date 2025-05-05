import streamlit as st

from sidebar import render_sidebar
from theme import configure_theme, apply_theme
from overview import overview
from edit import edit
from addgroup import add_group
from tracking import tracking
from visualization import visualization
from settings import settings

# Email-based sign in and sign up
from signin import signin
from signup import signup

# New Google Sign-In method
from go_signin import google_signin

# Set page configuration
st.set_page_config(page_title="Quraa Management System", layout="wide")

def main():
    """
    Main entry point for the Quraa Streamlit app.
    1) Configures theme.
    2) Checks if user is logged in; if not, shows sign-in (email/google) or sign-up.
    3) If logged in, shows the main app interface with logout and navigation.
    """

    # 1️⃣ Configure theme
    configure_theme()
    apply_theme()

    # 2️⃣ Handle authentication
    if not st.user.is_logged_in:
        _show_auth_interface()
        return  # Stop execution until login is complete

    # 3️⃣ Show main app interface
    _show_main_interface()

def _show_auth_interface():
    """Displays authentication options: Email sign-in, sign-up, or Google sign-in."""
    st.title("Quraa - Please Sign In or Sign Up")

    auth_choice = st.radio("Select an action:", ["Sign In (Email)", "Sign Up", "Sign In with Google"])

    if auth_choice == "Sign In (Email)":
        signin()
    elif auth_choice == "Sign Up":
        signup()
    else:
        google_signin()

def _show_main_interface():
    """Displays the app interface for logged-in users: logout + page selection."""
    user = st.experimental_user
    st.sidebar.write(f"Logged in as: **{user.name}** ({user.email})")

    if st.sidebar.button("Logout"):
        st.logout()  # Streamlit handles the logout process
        st.success("You have been logged out.")
        st.stop()

    # Navigation
    page = render_sidebar()
    if page == "Overview":
        overview()
    elif page == "Add Group":
        add_group()
    elif page == "Edit":
        edit()
    elif page == "Tracking":
        tracking()
    elif page == "Visualization":
        visualization()
    elif page == "Settings":
        settings()

if __name__ == "__main__":
    main()
