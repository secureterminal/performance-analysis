import streamlit as st

# ===== AUTHENTICATION CHECK (ADD THIS) =====
if not st.session_state.get("logged_in", False):
    st.error("🔒 Please log in to access this page.")
    st.switch_page("Login.py")

# Hide login from sidebar
hide_login_css = """
    <style>
        [data-testid="stSidebarNav"] li:first-child {
            display: none;
        }
    </style>
"""
st.markdown(hide_login_css, unsafe_allow_html=True)

# Show user info at top with compact design
if st.session_state.get("user_info"):
    user = st.session_state.user_info
    full_name = user.get('full_name', user.get('username', 'User'))
    first_name = full_name.split()[0] if full_name else 'User'
    role = user.get('role', 'user').capitalize()
    
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 0.6rem 1rem; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 8px; 
                        # margin-bottom: 1.0rem;
                        margin-top: -25.5rem;
                        color: white;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">👤</span>
                    <div>
                        <div style="font-size: 1rem; font-weight: 600; margin: 0; line-height: 1.2;">{first_name}</div>
                        <div style="font-size: 0.75rem; opacity: 0.9; margin: 0; line-height: 1.2;">Role: {role}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
# ===== END AUTHENTICATION =====

# Page content here
st.title("⚙️ Settings Page")
st.write("Welcome to the settings dashboard!")
