import streamlit as st

def get_notifications():
    """
    Fetch notifications stored in session state.
    """
    if "notifications" not in st.session_state:
        st.session_state["notifications"] = []  # Initialize as empty
    return st.session_state["notifications"]

def add_notification(message):
    """
    Adds a new notification if it's not already present.
    """
    if "notifications" not in st.session_state:
        st.session_state["notifications"] = []
    if message not in [n["message"] for n in st.session_state["notifications"]]:
        st.session_state["notifications"].append({"message": message, "read": False})

def clear_notifications():
    """
    Marks all notifications as read.
    """
    if "notifications" in st.session_state:
        for notification in st.session_state["notifications"]:
            notification["read"] = True

def render_sidebar(role="user"):
    """
    Renders the sidebar with navigation and notification features.
    The visible pages depend on the user's role.
    """
    st.sidebar.title("Quraa Management")

    # Pages based on user role
    if role == "admin":
        available_pages = [
            "Overview", "Add Group", "Edit", "Tracking", "Visualization", "Settings", "Admin Panel"
        ]
    elif role == "participant":
        available_pages = ["Overview", "Visualization"]
    else:  # default role: user
        available_pages = ["Overview"]

    # Navigation
    page = st.sidebar.radio("Navigate", available_pages)

    # Notifications
    st.sidebar.markdown("---")
    notifications = get_notifications()
    unread_count = sum(1 for n in notifications if not n["read"])

    # Display notification bell
    st.sidebar.write(f"🔔 **Notifications ({unread_count})**")

    # Show notification details
    if st.sidebar.button("View Notifications"):
        st.sidebar.markdown("### Notifications")
        if notifications:
            for idx, notification in enumerate(notifications, 1):
                status = "✅" if notification["read"] else "🔴"
                st.sidebar.write(f"{status} {idx}. {notification['message']}")
        else:
            st.sidebar.write("No notifications.")
        if st.sidebar.button("Clear All Notifications"):
            clear_notifications()
            st.experimental_rerun()

    st.sidebar.markdown("---")
    return page
