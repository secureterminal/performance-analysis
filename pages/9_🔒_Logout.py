# ============================================
# FILE 5: pages/9_🔒_Logout.py (Updated)
# ============================================
"""
Updated logout page
"""

import streamlit as st

st.set_page_config(page_title="Logout", page_icon="🔐", layout="centered")

# Check if logged in
if not st.session_state.get("logged_in", False):
    st.warning("You are not logged in.")
    if st.button("Go to Login"):
        st.switch_page("Login.py")
else:
    st.title("🔐 Logout")
    st.write(f"**User:** {st.session_state.user_info.get('full_name', 'Unknown')}")
    st.write("Are you sure you want to logout?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, Logout", use_container_width=True, type="primary"):
            # Clear session state
            st.session_state.logged_in = False
            st.session_state.user_info = None
            
            # Clear other session data
            for key in list(st.session_state.keys()):
                if key not in ['logged_in', 'user_info']:
                    del st.session_state[key]
            
            st.success("Logged out successfully!")
            st.switch_page("Login.py")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.switch_page("pages/1_🏠_Homepage.py")