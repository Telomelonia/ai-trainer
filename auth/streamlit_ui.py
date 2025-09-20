"""
Streamlit Authentication UI Components for CoreSense
Complete user interface for login, registration, profile management, and authentication
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import re
from datetime import datetime, timezone

from .user_service import (
    user_service, UserRegistrationData, UserLoginData, 
    UserProfileUpdate, AuthResult
)
from .email_service import password_reset_service, email_verification_service
from .session_manager import session_manager
from .models import UserRole

class AuthUI:
    """Authentication UI components for Streamlit"""
    
    def __init__(self):
        self.user_service = user_service
        self.session_manager = session_manager
        
        # Initialize session manager
        self.session_manager.initialize_session()
    
    def show_auth_sidebar(self) -> Optional[str]:
        """
        Show authentication sidebar with login/logout controls
        
        Returns:
            Current page selection or None
        """
        st.sidebar.markdown("---")
        
        if self.session_manager.is_logged_in():
            # Show user info and logout
            user_data = self.session_manager.get_current_user()
            
            st.sidebar.markdown("### 👤 User Account")
            st.sidebar.markdown(f"**{user_data['full_name']}**")
            st.sidebar.markdown(f"*{user_data['email']}*")
            
            # Show role badge
            role = user_data.get('role', 'free')
            if role == 'premium':
                st.sidebar.markdown("🌟 **Premium Member**")
            elif role == 'admin':
                st.sidebar.markdown("⚡ **Administrator**")
            else:
                st.sidebar.markdown("🆓 **Free Account**")
            
            # Show verification status
            if not user_data.get('is_verified', False):
                st.sidebar.warning("📧 Email not verified")
            
            # Session info
            session_duration = self.session_manager.get_session_duration()
            if session_duration:
                hours = int(session_duration.total_seconds() // 3600)
                minutes = int((session_duration.total_seconds() % 3600) // 60)
                st.sidebar.caption(f"Session: {hours}h {minutes}m")
            
            # Navigation buttons
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button("👤 Profile", use_container_width=True):
                    return "profile"
            
            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout_user()
                    st.rerun()
            
            return None
        else:
            # Show login/register options
            st.sidebar.markdown("### 🔐 Authentication")
            
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button("🔑 Login", use_container_width=True):
                    return "login"
            
            with col2:
                if st.button("📝 Register", use_container_width=True):
                    return "register"
            
            return None
    
    def show_login_form(self) -> bool:
        """
        Show login form
        
        Returns:
            True if login successful, False otherwise
        """
        st.markdown("""
        <div style="background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%); 
                    padding: 30px; border-radius: 10px; color: white; text-align: center; margin-bottom: 30px;">
            <h1>🔑 Login to CoreSense</h1>
            <p>Access your intelligent core training platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Login to Your Account")
            
            email_or_username = st.text_input(
                "Email or Username",
                placeholder="Enter your email or username",
                key="login_email"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                remember_me = st.checkbox("Remember me")
            
            with col2:
                if st.form_submit_button("🔑 Login", type="primary", use_container_width=True):
                    return self._process_login(email_or_username, password, remember_me)
        
        # Additional options
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔒 Forgot Password?"):
                st.session_state["show_password_reset"] = True
                st.rerun()
        
        with col2:
            if st.button("📝 Create Account"):
                return "register"
        
        # Show password reset if requested
        if st.session_state.get("show_password_reset", False):
            self._show_password_reset_form()
        
        return False
    
    def show_registration_form(self) -> bool:
        """
        Show registration form
        
        Returns:
            True if registration successful, False otherwise
        """
        st.markdown("""
        <div style="background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%); 
                    padding: 30px; border-radius: 10px; color: white; text-align: center; margin-bottom: 30px;">
            <h1>📝 Join CoreSense</h1>
            <p>Create your account and start your core training journey</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("registration_form", clear_on_submit=False):
            st.subheader("Create Your Account")
            
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(
                    "First Name *",
                    placeholder="John",
                    key="reg_first_name"
                )
                
                username = st.text_input(
                    "Username *",
                    placeholder="Choose a unique username",
                    key="reg_username"
                )
                
                age = st.number_input(
                    "Age",
                    min_value=13,
                    max_value=120,
                    value=25,
                    key="reg_age"
                )
            
            with col2:
                last_name = st.text_input(
                    "Last Name *",
                    placeholder="Doe",
                    key="reg_last_name"
                )
                
                email = st.text_input(
                    "Email Address *",
                    placeholder="john@example.com",
                    key="reg_email"
                )
                
                fitness_level = st.selectbox(
                    "Fitness Level",
                    options=["beginner", "intermediate", "advanced"],
                    index=0,
                    key="reg_fitness_level"
                )
            
            # Password fields
            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Create a strong password",
                key="reg_password"
            )
            
            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="Confirm your password",
                key="reg_confirm_password"
            )
            
            # Training preferences
            st.subheader("Training Preferences")
            
            training_goals = st.multiselect(
                "Training Goals",
                options=["Core Strength", "Balance", "Stability", "Injury Prevention", "Athletic Performance"],
                default=["Core Strength", "Stability"],
                key="reg_goals"
            )
            
            preferred_duration = st.slider(
                "Preferred Session Duration (minutes)",
                min_value=10,
                max_value=60,
                value=30,
                key="reg_duration"
            )
            
            health_considerations = st.text_area(
                "Health Considerations",
                placeholder="Any injuries, limitations, or health conditions we should know about...",
                key="reg_health"
            )
            
            # Terms and conditions
            terms_accepted = st.checkbox(
                "I accept the Terms of Service and Privacy Policy *",
                key="reg_terms"
            )
            
            # Submit button
            if st.form_submit_button("🚀 Create Account", type="primary", use_container_width=True):
                return self._process_registration(
                    first_name, last_name, username, email, password, confirm_password,
                    age, fitness_level, training_goals, preferred_duration,
                    health_considerations, terms_accepted
                )
        
        # Back to login
        if st.button("🔑 Already have an account? Login"):
            return "login"
        
        return False
    
    def show_profile_page(self):
        """Show user profile management page"""
        if not self.session_manager.is_logged_in():
            st.error("🔒 Please log in to view your profile.")
            return
        
        user_data = self.session_manager.get_current_user()
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%); 
                    padding: 30px; border-radius: 10px; color: white; text-align: center; margin-bottom: 30px;">
            <h1>👤 User Profile</h1>
            <p>Manage your account and training preferences</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Profile Info", "🔒 Security", "⚡ Subscription", "📊 Statistics"])
        
        with tab1:
            self._show_profile_info_tab(user_data)
        
        with tab2:
            self._show_security_tab(user_data)
        
        with tab3:
            self._show_subscription_tab(user_data)
        
        with tab4:
            self._show_statistics_tab(user_data)
    
    def _process_login(self, email_or_username: str, password: str, remember_me: bool) -> bool:
        """Process login form submission"""
        if not email_or_username or not password:
            st.error("Please enter both email/username and password.")
            return False
        
        # Create login data
        login_data = UserLoginData(
            email_or_username=email_or_username.strip(),
            password=password,
            device_info=f"Streamlit-{st.get_option('browser.gatherUsageStats')}",
            ip_address="127.0.0.1",  # In production, get real IP
            user_agent="Streamlit-CoreSense"
        )
        
        # Attempt login
        with st.spinner("🔐 Logging you in..."):
            result = self.user_service.login_user(login_data)
        
        if result.success:
            # Login successful, establish session
            if self.session_manager.login_user(result.user, result.tokens):
                st.success(f"Welcome back, {result.user.full_name}! 🎉")
                
                # Show verification reminder if needed
                if not result.user.is_verified:
                    st.warning("📧 Don't forget to verify your email address for full access.")
                
                st.rerun()
                return True
            else:
                st.error("Login successful but failed to establish session. Please try again.")
                return False
        else:
            st.error(f"❌ {result.message}")
            if result.errors:
                for error in result.errors:
                    st.caption(f"• {error}")
            return False
    
    def _process_registration(self, first_name: str, last_name: str, username: str, 
                            email: str, password: str, confirm_password: str,
                            age: int, fitness_level: str, training_goals: List[str],
                            preferred_duration: int, health_considerations: str,
                            terms_accepted: bool) -> bool:
        """Process registration form submission"""
        
        # Validation
        errors = []
        
        if not first_name or not last_name:
            errors.append("First name and last name are required")
        
        if not username:
            errors.append("Username is required")
        
        if not email:
            errors.append("Email address is required")
        
        if not password:
            errors.append("Password is required")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not terms_accepted:
            errors.append("You must accept the Terms of Service and Privacy Policy")
        
        # Validate username format
        if username and not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            errors.append("Username must be 3-20 characters and contain only letters, numbers, and underscores")
        
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
            return False
        
        # Create registration data
        registration_data = UserRegistrationData(
            email=email.strip(),
            username=username.strip(),
            password=password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            age=age,
            fitness_level=fitness_level,
            training_goals=training_goals,
            preferred_session_duration=preferred_duration,
            health_considerations=health_considerations.strip() if health_considerations else None
        )
        
        # Attempt registration
        with st.spinner("🚀 Creating your account..."):
            result = self.user_service.register_user(registration_data)
        
        if result.success:
            st.success(f"🎉 {result.message}")
            
            # Send verification email
            verification_result = email_verification_service.send_verification_email(result.user.id)
            if verification_result.success:
                st.info("📧 A verification email has been sent to your inbox.")
            else:
                st.warning("Account created but verification email failed to send. You can request a new one from your profile.")
            
            st.balloons()
            return True
        else:
            st.error(f"❌ {result.message}")
            if result.errors:
                for error in result.errors:
                    st.caption(f"• {error}")
            return False
    
    def _show_password_reset_form(self):
        """Show password reset form"""
        st.subheader("🔒 Reset Password")
        
        with st.form("password_reset_form"):
            email = st.text_input(
                "Enter your email address",
                placeholder="john@example.com"
            )
            
            if st.form_submit_button("📧 Send Reset Instructions"):
                if email:
                    with st.spinner("Sending reset instructions..."):
                        result = password_reset_service.initiate_password_reset(email)
                    
                    if result.success:
                        st.success(result.message)
                        st.session_state["show_password_reset"] = False
                    else:
                        st.error(result.message)
                else:
                    st.error("Please enter your email address")
        
        if st.button("❌ Cancel"):
            st.session_state["show_password_reset"] = False
            st.rerun()
    
    def _show_profile_info_tab(self, user_data: Dict[str, Any]):
        """Show profile information tab"""
        st.subheader("📋 Profile Information")
        
        with st.form("profile_update_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(
                    "First Name",
                    value=user_data.get('first_name', ''),
                    key="profile_first_name"
                )
                
                age = st.number_input(
                    "Age",
                    min_value=13,
                    max_value=120,
                    value=user_data.get('age', 25),
                    key="profile_age"
                )
            
            with col2:
                last_name = st.text_input(
                    "Last Name",
                    value=user_data.get('last_name', ''),
                    key="profile_last_name"
                )
                
                fitness_level = st.selectbox(
                    "Fitness Level",
                    options=["beginner", "intermediate", "advanced"],
                    index=["beginner", "intermediate", "advanced"].index(user_data.get('fitness_level', 'beginner')),
                    key="profile_fitness_level"
                )
            
            # Get current training goals
            current_goals = user_data.get('training_goals', [])
            if isinstance(current_goals, str):
                try:
                    import json
                    current_goals = json.loads(current_goals)
                except:
                    current_goals = []
            
            training_goals = st.multiselect(
                "Training Goals",
                options=["Core Strength", "Balance", "Stability", "Injury Prevention", "Athletic Performance"],
                default=current_goals,
                key="profile_goals"
            )
            
            preferred_duration = st.slider(
                "Preferred Session Duration (minutes)",
                min_value=10,
                max_value=60,
                value=user_data.get('preferred_session_duration', 30),
                key="profile_duration"
            )
            
            health_considerations = st.text_area(
                "Health Considerations",
                value=user_data.get('health_considerations', ''),
                key="profile_health"
            )
            
            if st.form_submit_button("💾 Save Changes", type="primary"):
                self._update_profile(
                    first_name, last_name, age, fitness_level,
                    training_goals, preferred_duration, health_considerations
                )
    
    def _show_security_tab(self, user_data: Dict[str, Any]):
        """Show security settings tab"""
        st.subheader("🔒 Security Settings")
        
        # Email verification status
        if not user_data.get('is_verified', False):
            st.warning("📧 Your email address is not verified")
            if st.button("📧 Send Verification Email"):
                result = email_verification_service.send_verification_email(user_data['id'])
                if result.success:
                    st.success("Verification email sent!")
                else:
                    st.error(result.message)
        else:
            st.success("✅ Email address verified")
        
        # Password change
        st.markdown("---")
        st.subheader("Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                key="current_password"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                key="new_password"
            )
            
            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                key="confirm_new_password"
            )
            
            if st.form_submit_button("🔑 Change Password", type="primary"):
                self._change_password(current_password, new_password, confirm_new_password)
    
    def _show_subscription_tab(self, user_data: Dict[str, Any]):
        """Show subscription management tab"""
        st.subheader("⚡ Subscription Management")
        
        # Current subscription status
        if user_data.get('is_premium', False):
            st.success("🌟 **Premium Member**")
            st.write("You have access to all premium features!")
            
            # Premium features
            st.markdown("""
            **Premium Features:**
            - 🤖 Advanced AI coaching
            - 📊 Detailed analytics
            - 🎯 Personalized workout plans
            - ⚡ Priority support
            - 📱 Mobile app access
            """)
        else:
            st.info("🆓 **Free Account**")
            st.write("Upgrade to premium for advanced features!")
            
            # Upgrade options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **Monthly**
                - $9.99/month
                - All premium features
                - Cancel anytime
                """)
                if st.button("Upgrade Monthly", key="upgrade_monthly"):
                    self._upgrade_to_premium(1)
            
            with col2:
                st.markdown("""
                **Quarterly**
                - $24.99/3 months
                - Save 17%
                - All premium features
                """)
                if st.button("Upgrade Quarterly", key="upgrade_quarterly"):
                    self._upgrade_to_premium(3)
            
            with col3:
                st.markdown("""
                **Yearly**
                - $89.99/year
                - Save 25%
                - All premium features
                """)
                if st.button("Upgrade Yearly", key="upgrade_yearly"):
                    self._upgrade_to_premium(12)
    
    def _show_statistics_tab(self, user_data: Dict[str, Any]):
        """Show user statistics tab"""
        st.subheader("📊 Your Statistics")
        
        # Mock statistics - in production, get from database
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Sessions", "47", "+3 this week")
            st.metric("Avg Stability Score", "84.2%", "+2.1%")
        
        with col2:
            st.metric("Training Hours", "15.5h", "+2.3h")
            st.metric("Current Streak", "7 days", "🔥")
        
        with col3:
            st.metric("Personal Best", "94.7%", "New!")
            st.metric("Achievements", "12/20", "+2")
        
        # Progress chart placeholder
        st.markdown("---")
        st.subheader("Progress Over Time")
        st.info("📈 Detailed progress charts will be available here")
    
    def _update_profile(self, first_name: str, last_name: str, age: int,
                       fitness_level: str, training_goals: List[str],
                       preferred_duration: int, health_considerations: str):
        """Update user profile"""
        profile_update = UserProfileUpdate(
            first_name=first_name,
            last_name=last_name,
            age=age,
            fitness_level=fitness_level,
            training_goals=training_goals,
            preferred_session_duration=preferred_duration,
            health_considerations=health_considerations
        )
        
        user_id = self.session_manager.get_current_user_id()
        
        with st.spinner("💾 Saving changes..."):
            result = self.user_service.update_user_profile(user_id, profile_update)
        
        if result.success:
            st.success("✅ Profile updated successfully!")
            
            # Update session data
            current_user_data = self.session_manager.get_current_user()
            self.session_manager.update_user_session_data({
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}" if first_name and last_name else first_name or last_name or current_user_data.get('username', '')
            })
            
            st.rerun()
        else:
            st.error(f"❌ {result.message}")
    
    def _change_password(self, current_password: str, new_password: str, confirm_new_password: str):
        """Change user password"""
        if not current_password or not new_password:
            st.error("Please fill in all password fields")
            return
        
        if new_password != confirm_new_password:
            st.error("New passwords do not match")
            return
        
        user_id = self.session_manager.get_current_user_id()
        
        with st.spinner("🔑 Changing password..."):
            result = self.user_service.change_user_password(user_id, current_password, new_password)
        
        if result.success:
            st.success("✅ Password changed successfully!")
        else:
            st.error(f"❌ {result.message}")
            if result.errors:
                for error in result.errors:
                    st.caption(f"• {error}")
    
    def _upgrade_to_premium(self, months: int):
        """Upgrade user to premium"""
        user_id = self.session_manager.get_current_user_id()
        
        with st.spinner("⚡ Processing upgrade..."):
            result = self.user_service.upgrade_to_premium(user_id, months)
        
        if result.success:
            st.success("🎉 Upgraded to premium successfully!")
            
            # Update session data
            self.session_manager.update_user_session_data({
                'role': 'premium',
                'is_premium': True
            })
            
            st.balloons()
            st.rerun()
        else:
            st.error(f"❌ {result.message}")
    
    def logout_user(self):
        """Logout current user"""
        self.session_manager.logout_user()
        st.success("👋 Logged out successfully!")

# Global authentication UI instance
auth_ui = AuthUI()

# Export the auth UI
__all__ = ['AuthUI', 'auth_ui']