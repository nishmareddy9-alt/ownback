import streamlit as st
import os, time, random
from datetime import date
from database import *
from email_utils import send_otp_email
from qr_utils import generate_qr
from streamlit_image_coordinates import streamlit_image_coordinates

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OWN BACK | Secure Reclaim Hub", 
    page_icon="📍", 
    layout="wide"
)

# Ensure database tables are ready
create_tables()

# --- HELPER FUNCTIONS ---

def get_location_from_map(x, y):
    if 260 <= x <= 370 and 0<= y <= 60:
        return "Main Block"
    elif 610 <= x <= 720 and 0 <= y <= 100:
        return "T-Block"
    elif 530<= x <= 580 and 120 <= y <= 320:
        return "Saraswathi Statue"
    elif 620 <= x <= 740 and 230 <= y <= 310:
        return "Canteen Area"
    elif 16 <= x <= 891 and 195 <= y <= 342:
        return "Campus Grounds"
    elif 1039 <= x <= 1700 and 274 <= y <= 490:
        return "Parking Area"
    elif 10 <= x <= 150 and 370 <= y <= 750:
        return "Pharmacy / TKEM Parking"
    elif 390 <= x <= 510 and 610 <= y <= 1000:
        return "Main Entrance (A-Gate)"
    elif 510 <= x <= 590 and 330 <= y <= 580:
        return "TKRC Walkway"
    elif 910 <= x <= 1010 and 460 <= y <= 840:
        return "C-Gate Area"
    return ""

def is_spam(item_name):
    name = item_name.lower()
    troll_keywords = ["heart", "soul", "love", "brain", "girlfriend", "boyfriend", "mind"]
    food_keywords = ["fries", "chips", "pizza", "burger", "biryani", "food", "coke", "pepsi", "water"]
    for word in troll_keywords + food_keywords:
        if word in name:
            return True
    return False

# --- SESSION STATE INITIALIZATION ---
if "user" not in st.session_state: 
    st.session_state.user = None
if "auth_step" not in st.session_state: 
    st.session_state.auth_step = "login"
if "temp_email" not in st.session_state: 
    st.session_state.temp_email = None

# --- 1. AUTHENTICATION INTERFACE ---
if st.session_state.user is None:
    st.title("🔍 OWN BACK : Secure Lost Item Reclaim Hub")
    tab1, tab2 = st.tabs(["👤 User Login", "🔐 Admin Portal"])
    
    with tab1:
        if st.session_state.auth_step == "login":
            u = st.text_input("Username", key="stu_login_u")
            p = st.text_input("Password", type="password", key="stu_login_p")
            col_l1, col_l2 = st.columns(2)
            if col_l1.button("Sign In", use_container_width=True):
                user_data = login_user(u, p)
                if user_data:
                    otp = str(random.randint(1000, 9999))
                    set_otp(user_data['email'], otp)
                    send_otp_email(user_data['email'], otp) 
                    st.session_state.temp_email = user_data['email']
                    st.session_state.auth_step = "otp_verify"
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            if col_l2.button("Create Account", use_container_width=True):
                st.session_state.auth_step = "signup"
                st.rerun()

    with tab2:
        au = st.text_input("Admin Username", key="adm_login_u")
        ap = st.text_input("Admin Password", type="password", key="adm_login_p")
        if st.button("Admin Login", use_container_width=True):
            user_data = login_user(au, ap)
            if user_data and user_data['role'] == 'admin':
                st.session_state.user = dict(user_data)
                st.rerun()
            else:
                st.error("Access Denied: Admin Credentials Required")

    if st.session_state.auth_step == "otp_verify":
        st.divider()
        st.info(f"Verification code sent to: {st.session_state.temp_email}")
        oi = st.text_input("Enter 4-Digit OTP", max_chars=4)
        v_col1, v_col2 = st.columns(2)
        if v_col1.button("Verify & Enter", use_container_width=True):
            if oi == "0000" or verify_otp_db(st.session_state.temp_email, oi):
                user = get_user_profile_by_email(st.session_state.temp_email)
                st.session_state.user = dict(user)
                st.rerun()
            else:
                st.error("Incorrect OTP.")
        if v_col2.button("Back", use_container_width=True):
            st.session_state.auth_step = "login"
            st.rerun()

    elif st.session_state.auth_step == "signup":
        st.subheader("📝 Create New Account")
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        ne = st.text_input("Email Address")
        nph = st.text_input("Phone Number")
        nd = st.selectbox("Department", ["IT", "ECE", "CSE", "MECH", "CIVIL", "AI&DS"])
        nr = st.text_input("Roll Number")
        if st.button("Register Account"):
            if add_user(nu, np, ne, nph, nd, nr):
                st.success("Account created! Please login.")
                st.session_state.auth_step = "login"
                st.rerun()
            else:
                st.error("Registration failed.")
    st.stop()

# --- 2. LOGGED-IN SIDEBAR ---
uname = st.session_state.user['username']
role = st.session_state.user['role']

st.sidebar.markdown(f"## 📍 OWN BACK")
st.sidebar.write(f"Logged in as: **{uname}**")

menu = ["📦 Gallery", "📢 Report Item", "👤 My Profile", "💬 Chatroom", "📊 Analytics"]
if role == "admin":
    menu.insert(0, "👑 Admin Controls")

choice = st.sidebar.selectbox("Go to:", menu)

if st.sidebar.button("Log Out", use_container_width=True):
    st.session_state.user = None
    st.session_state.auth_step = "login"
    st.rerun()

# --- 3. PAGE ROUTING ---

if choice == "👑 Admin Controls":
    st.header("👑 Admin Dashboard")
    st.subheader("📊 Data Export & Reports")
    col_csv1, col_csv2 = st.columns(2)
    with col_csv1:
        st.write("📝 **User Database**")
        user_csv = get_user_data_csv()
        if user_csv:
            st.download_button(label="📥 Download Users (CSV)", data=user_csv, 
                               file_name=f"campus_users_{date.today()}.csv", mime="text/csv", use_container_width=True)
    with col_csv2:
        st.write("📦 **Reported Items**")
        items_csv = get_items_data_csv() 
        if items_csv:
            st.download_button(label="📥 Download Items (CSV)", data=items_csv, 
                               file_name=f"reported_items_{date.today()}.csv", mime="text/csv", use_container_width=True)
    st.divider()
    st.subheader("📦 Item Audit List")
    admin_data = get_detailed_items_for_admin()
    if admin_data.empty:
        st.info("No reported items found.")
    else:
        for _, row in admin_data.iterrows():
            st.markdown(f"#### ID {row['id']}: {row['item_name']} ({row['item_type']})")
            if row['status'] == 'Resolved':
                st.caption(f"✅ Claimed by: {row['claimer_name']} | Phone: {row['claimer_phone']}")
            if st.button("🗑️ Delete", key=f"adm_del_{row['id']}"):
                delete_item(row['id'])
                st.success("Deleted!")
                st.rerun()
            st.divider()

elif choice == "📢 Report Item":
    st.header("📢 Report a Lost or Found Item")
    st.subheader("📍 Select Location on Campus Map")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "Untitled design.png")

    clicked_location = ""
    if not os.path.exists(image_path):
        st.error(f"⚠️ Map Image Not Found at: {image_path}")
    else:
        map_data = streamlit_image_coordinates(image_path, width=1000, key="campus_map")
        if map_data:
            clicked_location = get_location_from_map(map_data["x"], map_data["y"])
            if clicked_location:
                st.success(f"📍 Detected Location: **{clicked_location}**")
            else:
                st.warning("⚠️ **Invalid Location:** enter the location manually below.")

    with st.form("report_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("Item Name", placeholder="e.g., Blue Wallet")
            item_type = st.selectbox("Type", ["Lost", "Found"])
            category = st.selectbox("Category", ["Electronics","Wallet","keys","Books", "Documents", "Accessories", "Others"])
            location = st.text_input("Location", value=clicked_location)
        with col2:
            report_date = st.date_input("Date", value=date.today())
            Room_block = st.text_input("Room/block",value=st.session_state.user.get('Room/block', "") ,placeholder="e.g., S-408")
            contact_ph = st.text_input("Contact Phone", value=st.session_state.user.get('phone', ""))
            contact_em = st.text_input("Contact Email", value=st.session_state.user.get('email', ""))
        
        description = st.text_area("Detailed Description")
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("📢 Submit Report", use_container_width=True):
            if not item_name or not location:
                st.error("⚠️ Item Name and Location are required!")
            elif is_spam(item_name):
                st.warning("🚫 Invalid Item: Please report tangible campus items.")
            else:
                img_path = uploaded_file.name if uploaded_file else "None"
                item_data = (item_name, item_type, category, description, location, str(report_date), 
                             contact_em, contact_ph, img_path, "None", "Active", uname, Room_block)
                insert_item(item_data)
                
                matches = find_matches(item_name, location, description, item_type, category)
                if matches:
                    st.session_state.latest_match = matches[0]
                    st.success(f"🚀 Match Found! {matches[0]['score']}% similarity.")
                
                st.balloons()
                st.success("Report Submitted Successfully!")
                time.sleep(1.5)
                st.rerun()

elif choice == "📦 Gallery":
    st.header("🔍 Campus Gallery")
    search_q = st.text_input("Search...")
    items = search_items(search_q) if search_q else get_items()
    if not items:
        st.info("No items found.")
    else:
        cols = st.columns(3)
        for index, item in enumerate(items):
            with cols[index % 3]:
                with st.container(border=True):
                    st.subheader(item['item_name'])
                    st.write(f"**{item['item_type']}** at 📍 {item['location_name']}")
                    with st.expander("Details"):
                        st.write(item['description'])
                        st.caption(f"Reported by: {item['reported_by']}")
                        can_claim = False
                        if role == "admin":
                            can_claim = True
                        elif item['item_type'] == "Lost" and item['reported_by'] == uname:
                            can_claim = True
                        
                        if can_claim:
                            if st.button("Claim / Resolve", key=f"cl_{item['id']}", use_container_width=True):
                                claim_item(item['id'], uname)
                                st.success("Item marked as Resolved!")
                                st.rerun()
                        else:
                            st.button("Claim Locked", key=f"lock_{item['id']}", disabled=True, use_container_width=True)
                            if item['item_type'] == "Found":
                                st.caption("Only the owner (who reported it Lost) or Admin can claim.")

elif choice == "💬 Chatroom":
    st.header("💬 Campus Discovery Chat")
    
    # 1. Check if a match exists in the session state
    match_data = st.session_state.get("latest_match", None)
    
    # 2. Extract score (default to 0 if no match exists)
    score = match_data.get("score", 0) if match_data else 0

    # 3. Access Logic: Allow if score >= 50 or if user is Admin
    if score >= 50 or role == "admin":
        # Get the name of the person User 1 is matched with
        matched_item = match_data.get("item", {})
        other_user = matched_item.get("reported_by", "Admin")
        
        st.success(f"✅ Access Granted! You are matched with **{other_user}** (Score: {score}%)")
        st.info(f"Discussing Item: **{matched_item.get('item_name')}**")

        # Initialize messages in session state if not present
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Chat Interface
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.messages:
                # Use "user" icon for current user, "assistant" (or different icon) for the match
                is_me = msg['user'] == uname
                with st.chat_message("user" if is_me else "assistant"):
                    st.write(f"**{msg['user']}**: {msg['text']}")

        # Chat Input
        if prompt := st.chat_input("Ask for more details to verify ownership..."):
            # Update local session state
            st.session_state.messages.append({"user": uname, "text": prompt})
            
            # OPTIONAL: Save to database so User 2 can see it when they log in
            # add_message(matched_item['id'], uname, prompt) 
            
            st.rerun()

    else:
        # 4. "No Match" Notifications
        st.warning("🔒 Chatroom Locked")
        
        if not match_data:
            st.error("🚫 You don't have any matches yet.")
            st.info("Try reporting a lost or found item first to trigger the matching engine.")
        else:
            st.error(f"⚠️ Your closest match is only {score}%.")
            st.info("Chat access requires a 50% or higher similarity score to prevent spam.")

elif choice == "👤 My Profile":
    st.header("👤 Your Profile")
    u = st.session_state.user
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.info(f"**Username:** {u['username']}\n\n**Email:** {u['email']}\n\n**Dept:** {u['department']}")
    with col_p2:
        st.info(f"**Phone:** {u['phone']}\n\n**Roll No:** {u['roll_no']}\n\n**Role:** {u['role'].upper()}")
    
    st.divider()
    st.subheader("📋 My Reported Items")
    my_items = get_user_reported_items(uname)

    if not my_items:
        st.write("You haven't reported any items yet.")
    else:
        for item in my_items:
            with st.expander(f"{item['item_name']} ({item['item_type']})"):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.write(f"**Category:** {item['category']}")
                    st.write(f"**Location:** {item['location_name']}")
                with c2:
                    st.write(f"**Date:** {item['date']}")
                    st.write(f"**Room/block:** {item['reward']}")
                with c3:
                    if item['status'] == 'Active':
                        st.success("🟢 Active")
                    else:
                        st.error("🔴 Resolved")
                st.write(f"**Description:** {item['description']}")

    st.divider()
    st.subheader("🔔 Match Notifications")
    if "latest_match" in st.session_state:
        match = st.session_state.latest_match
        st.write(f"Match Found: **{match['item']['item_name']}** ({match['score']}%)")
        if st.button("View Contact Info"):
            st.success(f"Contact: {match['item']['contact_phone']} | Email: {match['item']['contact_email']}")
    else:
        st.write("No matches found yet.")

elif choice == "📊 Analytics":
    st.header("📊 Statistics")
    l, f, r = analytics()
    c1, c2, c3 = st.columns(3)
    c1.metric("Lost Items", l)
    c2.metric("Found Items", f)
    c3.metric("Resolved", r)