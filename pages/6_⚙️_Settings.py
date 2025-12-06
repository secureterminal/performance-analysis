import streamlit as st

# Block unauthenticated access
if not st.session_state.get("logged_in", False):
    st.error("🔒 Please log in to view this page.")
    st.page_link("app.py", label="Login", icon="🔐")
    st.stop()

# Page content here
st.title("⚙️ Settings Page")
st.write("Welcome to the settings dashboard!")
