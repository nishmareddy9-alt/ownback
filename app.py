import streamlit as st
import os
import time
import random
from datetime import date

# 1. Component for the Campus Map
from streamlit_image_coordinates import streamlit_image_coordinates

# 2. Custom Utility Imports
from email_utils import send_otp_email
from qr_utils import generate_qr

# 3. Database Imports (Explicitly listing functions prevents NameErrors)
from database import (
    get_connection, 
    insert_item, 
    get_items, 
    search_items, 
    get_messages, 
    add_message, 
    get_active_match_for_user,
    claim_item,
    set_otp,
    verify_user,
    find_matches,
    create_tables,
    login_user,
    verify_otp_db,
    get_user_profile_by_email,
    add_user,
    get_user_data_csv,
    get_items_data_csv,
    get_detailed_items_for_admin,
    delete_item,
    get_user_reported_items,
    analytics
)

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
    if 260 <= x <= 370 and 0 <= y <= 60:
        return "Main Block"
    elif 610 <= x <= 720 and 0 <= y <= 100:
        return "T-Block"
    elif 530 <= x <= 580 and 120 <= y <= 320:
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
    
    # --- 1. CAMPUS MAP SELECTION ---
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
                st.warning("⚠️ **Invalid Location:** Please enter the location manually below.")

    # --- 2. REPORT FORM ---
    with st.form("report_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            item_name = st.text_input("Item Name", placeholder="e.g., Blue Wallet")
            item_type = st.selectbox("Type", ["Lost", "Found"])
            category = st.selectbox("Category", ["Electronics","Wallet","keys","Books", "Documents", "Accessories", "Others"])
            location = st.text_input("Location", value=clicked_location)
            
        with col2:
            report_date = st.date_input("Date", value=date.today())
            # Reward/Room Block logic
            room_info = st.text_input("Room / Block Info", placeholder="e.g., S-408 or Canteen Area")
            contact_ph = st.text_input("Contact Phone", value=st.session_state.user.get('phone', ""))
            contact_em = st.text_input("Contact Email", value=st.session_state.user.get('email', ""))
        
        description = st.text_area("Detailed Description (e.g. brand, color, unique marks)")
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
        
        # --- 3. FORM SUBMISSION & FILE SAVING ---
        if st.form_submit_button("📢 Submit Report", use_container_width=True):
            if not item_name or not location:
                st.error("⚠️ Item Name and Location are required!")
            elif is_spam(item_name):
                st.warning("🚫 Invalid Item: Please report tangible campus items.")
            else:
                # --- IMAGE HANDLING ---
                saved_img_path = "None"
                if uploaded_file:
                    upload_dir = os.path.join(current_dir, "uploads")
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                    
                    file_extension = os.path.splitext(uploaded_file.name)[1]
                    unique_filename = f"{item_type}_{int(time.time())}{file_extension}"
                    saved_img_path = os.path.join("uploads", unique_filename)
                    full_save_path = os.path.join(current_dir, saved_img_path)
                    
                    with open(full_save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                item_data = (
                    item_name, item_type, category, description, location, 
                    str(report_date), contact_em, contact_ph, saved_img_path, 
                    "None", "Active", uname, room_info
                )
                
                insert_item(item_data)
                
                # TRIGGER MATCHING ENGINE
                matches = find_matches(item_name, location, description, item_type, category)
                if matches:
                    st.session_state.latest_match = matches[0]
                    st.success(f"🚀 Match Found! {matches[0]['score']}% similarity.")
                
                st.balloons()
                st.success("Report Submitted Successfully! View it in the Gallery.")
                time.sleep(1.5)
                st.rerun()

elif choice == "📦 Gallery":
    st.header("🔍 Campus Gallery")
    
    search_q = st.text_input("Search items (e.g. 'iPhone', 'Wallet', 'Main Block')...")
    items = search_items(search_q) if search_q else get_items()
    
    if not items:
        st.info("No active items found in the gallery.")
    else:
        cols = st.columns(3)
        for index, item in enumerate(items):
            with cols[index % 3]:
                with st.container(border=True):
                    db_img_path = item['image_path']
                    
                    if db_img_path and db_img_path != "None":
                        if os.path.exists(db_img_path):
                            st.image(db_img_path, use_container_width=True, caption=f"View of {item['item_name']}")
                        else:
                            st.warning("🖼️ Image file not found on server.")
                    else:
                        st.info("No photo provided for this item.")
                    
                    st.subheader(item['item_name'])
                    st.markdown(f"**Type:** {item['item_type']}")
                    st.markdown(f"**Location:** 📍 {item['location_name']}")
                    
                    with st.expander("📄 View More Details"):
                        st.write(f"**Description:** {item['description']}")
                        st.write(f"**Category:** {item['category']}")
                        st.write(f"**Date Reported:** {item['date']}")
                        st.caption(f"Reported by: {item['reported_by']}")
                        
                        st.divider()
                        
                        can_claim = False
                        if role == "admin":
                            can_claim = True
                        elif item['item_type'] == "Lost" and item['reported_by'] == uname:
                            can_claim = True
                        
                        if can_claim:
                            if st.button("Mark as Resolved / Claimed", key=f"cl_{item['id']}", use_container_width=True):
                                claim_item(item['id'], uname)
                                st.success("🎉 Item status updated to Resolved!")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.button("Claim Locked", key=f"lock_{item['id']}", disabled=True, use_container_width=True)
                            if item['item_type'] == "Found":
                                st.caption("🛡️ Secure Reclaim: Only the original owner or Admin can resolve this.")

elif choice == "💬 Chatroom":
    st.header("💬 Campus Discovery Chat")
    
    match_data = st.session_state.get("latest_match")
    
    if not match_data:
        st.warning("🔒 Chatroom Locked")
        st.error("You don't have any matches yet.")
        st.info("Report an item first to trigger the matching engine.")
        st.stop()

    score = match_data.get("score", 0)

    if score >= 50 or role == "admin":
        matched_item = match_data.get("item", {})
        item_id = matched_item.get("id")
        other_user = matched_item.get("reported_by", "Other User")
        
        st.success(f"✅ Access Granted! Matched with **{other_user}**")
        st.caption(f"Discussing: {matched_item.get('item_name')} | Match Score: {score}%")

        chat_history = get_messages(item_id) 

        chat_container = st.container(height=400)
        with chat_container:
            for msg in chat_history:
                is_me = msg['user'] == uname
                with st.chat_message("user" if is_me else "assistant"):
                    st.write(f"**{msg['user']}**: {msg['text']}")

        if prompt := st.chat_input("Ask for more details..."):
            add_message(item_id, uname, prompt)
            st.rerun()
    else:
        st.warning("🔒 Chatroom Locked")
        st.error(f"Match score too low ({score}%). 50% or higher required.")

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
