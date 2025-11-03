import streamlit as st

# Set page title
st.set_page_config(page_title="Logout", page_icon="🔐")

# Ensure login state is tracked
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.button("Log Out"):
    # Display logout message
    st.title("🔐 Logging Out...")

    # Perform logout
    st.session_state.logged_in = False
    

    # Set query param for redirection and rerun
    st.query_params["page"] = "login"
    # st.rerun()
    st.success("You have been logged out successfully!")
