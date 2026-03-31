import sqlite3
import pandas as pd

DB_NAME = "lost_found.db"

def get_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row 
    return conn

def create_tables():
    """Initialize database tables and default admin accounts."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        item_name TEXT, 
        item_type TEXT, 
        category TEXT,
        description TEXT, 
        location_name TEXT, 
        date TEXT, 
        contact_email TEXT, 
        contact_phone TEXT,
        image_path TEXT, 
        file_path TEXT, 
        status TEXT DEFAULT 'Active', 
        reported_by TEXT,
        reward TEXT, 
        claimed_by TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # 2. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        password TEXT, 
        email TEXT, 
        phone TEXT, 
        department TEXT, 
        roll_no TEXT, 
        role TEXT DEFAULT 'user', 
        otp TEXT
    )""")
    
    # 3. Messages Table (Chatroom)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        item_id INTEGER, 
        sender TEXT, 
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # --- DEFAULT ADMINS ---
    # Ensure nishmareddy and admin exist with correct roles
    admin_accounts = [
        (1, 'admin', 'admin123', 'admin', 'ownbacklostitfinditgetit@gmail.com'),
        (2, 'nishmareddy', 'hellonishma', 'admin', 'ownbacklostitfinditgetit@gmail.com')
    ]
    
    for acc in admin_accounts:
        cursor.execute("""
            INSERT OR REPLACE INTO users(id, username, password, role, email) 
            VALUES (?, ?, ?, ?, ?)
        """, acc)
        
    conn.commit()
    conn.close()

# --- AUTHENTICATION FUNCTIONS ---

def login_user(u, p):
    """Validate username and password."""
    conn = get_connection()
    res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
    conn.close()
    return res

def set_otp(e, o):
    """Store the generated OTP for a specific email."""
    conn = get_connection()
    conn.execute("UPDATE users SET otp=? WHERE email=?", (o, e))
    conn.commit()
    conn.close()

def verify_otp_db(e, o):
    """Check if the provided OTP matches the stored one."""
    conn = get_connection()
    res = conn.execute("SELECT * FROM users WHERE email=? AND otp=?", (e, o)).fetchone()
    conn.close()
    return res

def add_user(u, p, e, ph, d, r):
    """Register a new student user."""
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO users(username, password, email, phone, department, roll_no, role) 
            VALUES (?,?,?,?,?,?,'user')
        """, (u, p, e, ph, d, r))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # Username already exists

def get_user_profile(username):
    conn = get_connection()
    res = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return res

def get_user_profile_by_email(email):
    conn = get_connection()
    res = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return res

# --- ITEM MANAGEMENT FUNCTIONS ---

def insert_item(data):
    """Insert a newly reported lost/found item."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO items(
            item_name, item_type, category, description, location_name, 
            date, contact_email, contact_phone, image_path, file_path, 
            status, reported_by, reward
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()

def get_items():
    """Retrieve all active items for the gallery."""
    conn = get_connection()
    res = conn.execute("SELECT * FROM items WHERE status='Active' ORDER BY id DESC").fetchall()
    conn.close()
    return res

def search_items(q):
    """Search active items based on name or description."""
    conn = get_connection()
    res = conn.execute("""
        SELECT * FROM items 
        WHERE (item_name LIKE ? OR description LIKE ?) AND status='Active'
    """, ('%'+q+'%', '%'+q+'%')).fetchall()
    conn.close()
    return res

def claim_item(i, u):
    """Mark an item as resolved and record who claimed it."""
    conn = get_connection()
    conn.execute("UPDATE items SET status='Resolved', claimed_by=? WHERE id=?", (u, i))
    conn.commit()
    conn.close()

def delete_item(i):
    """Remove an item from the database."""
    conn = get_connection()
    conn.execute("DELETE FROM items WHERE id=?", (i,))
    conn.commit()
    conn.close()

# --- ADMIN & ANALYTICS FUNCTIONS ---

def analytics():
    """Get counts for dashboard metrics."""
    conn = get_connection()
    l = conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Lost' AND status='Active'").fetchone()[0]
    f = conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Found' AND status='Active'").fetchone()[0]
    r = conn.execute("SELECT COUNT(*) FROM items WHERE status='Resolved'").fetchone()[0]
    conn.close()
    return l, f, r

def get_user_data_csv():
    """Export the users table to a CSV format for admins."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT username, email, phone, department, roll_no, role FROM users", conn)
    conn.close()
    return df.to_csv(index=False).encode('utf-8')

def get_detailed_items_for_admin():
    """Get all items including details of the person who claimed them."""
    conn = get_connection()
    query = """
        SELECT items.*, 
               u.username as claimer_name, 
               u.phone as claimer_phone, 
               u.email as claimer_email, 
               u.department as claimer_dept 
        FROM items 
        LEFT JOIN users u ON items.claimed_by = u.username 
        ORDER BY items.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- MESSAGING FUNCTIONS ---

def add_message(item_id, sender, msg):
    conn = get_connection()
    conn.execute("INSERT INTO messages (item_id, sender, message) VALUES (?,?,?)", (item_id, sender, msg))
    conn.commit()
    conn.close()

def get_messages(item_id):
    conn = get_connection()
    res = conn.execute("SELECT sender, message, timestamp FROM messages WHERE item_id=? ORDER BY timestamp ASC", (item_id,)).fetchall()
    conn.close()
    return res

def get_user_data_csv():
    """Fetches all users from the database and returns a CSV-encoded object."""
    try:
        conn = get_connection()
        # Querying specific columns for the CSV
        query = "SELECT id, username, email, phone, department, roll_no, role FROM users"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert dataframe to CSV string and then to bytes for Streamlit download
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        print(f"Error exporting user data: {e}")
        return None
    
def get_items_data_csv():
    """Fetches all reported items (Lost & Found) for Admin export."""
    try:
        conn = get_connection()
        # Querying item details and joining with the users table to get reporter contact info
        query = """
            SELECT id, item_name, item_type, category, location_name, 
                   date, status, reported_by, contact_phone, reward 
            FROM items
            ORDER BY id DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        print(f"Error exporting items data: {e}")
        return None
# ... (Keep your existing imports and create_tables/auth functions) ...

def get_item_by_id(item_id):
    """Retrieve a single item's details by its ID."""
    conn = get_connection()
    res = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    conn.close()
    return res

def find_matches(new_item_name, new_location, new_description, new_type, new_category):
    """
    Improved Matching Algorithm for IT Expo:
    Scores based on Location (50%), Category (20%), and Name/Description (30%).
    """
    conn = get_connection()
    target_type = "Lost" if new_type == "Found" else "Found"
    
    potential_matches = conn.execute(
        "SELECT * FROM items WHERE item_type=? AND status='Active'", (target_type,)
    ).fetchall()
    
    matches = []
    for item in potential_matches:
        score = 0
        
        # 1. Location Match (Up to 50%)
        if new_location.lower().strip() == item['location_name'].lower().strip():
            score += 50
        elif new_location.lower() in item['location_name'].lower():
            score += 30
        
        # 2. Category Match (20%)
        if new_category == item['category']:
            score += 20
            
        # 3. Name & Description Keyword Match (Up to 30%)
        name_words = set(new_item_name.lower().split())
        target_name_words = set(item['item_name'].lower().split())
        common_name = name_words.intersection(target_name_words)
        
        if len(common_name) > 0:
            score += 20 # High weight for name match
            
        desc_words = set(new_description.lower().split())
        target_desc_words = set(item['description'].lower().split())
        common_desc = desc_words.intersection(target_desc_words)
        
        if len(common_desc) > 1:
            score += 10

        # Return matches that meet the 50% threshold for chatroom access
        if score >= 50:
            matches.append({"item": dict(item), "score": score})
            
    conn.close()
    # Sort by highest score first
    return sorted(matches, key=lambda x: x['score'], reverse=True)

# --- CLEANED EXPORT FUNCTIONS ---

def get_user_data_csv():
    """Export users for Admin."""
    try:
        conn = get_connection()
        query = "SELECT id, username, email, phone, department, roll_no, role FROM users"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        return None
    
def get_items_data_csv():
    """Export items for Admin."""
    try:
        conn = get_connection()
        query = "SELECT * FROM items ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        return None
def get_user_reported_items(username):
    """Retrieve all items reported by a specific user."""
    conn = get_connection()
    # Fetching both Active and Resolved items so the user can see their history
    res = conn.execute("SELECT * FROM items WHERE reported_by=? ORDER BY id DESC", (username,)).fetchall()
    conn.close()
    return res
def add_message(item_id, sender, msg):
    """Saves a chat message to the database so the other user can see it."""
    conn = get_connection()
    conn.execute("INSERT INTO messages (item_id, sender, message) VALUES (?,?,?)", (item_id, sender, msg))
    conn.commit()
    conn.close()

def get_messages(item_id):
    """Fetches all messages for a specific item match."""
    conn = get_connection()
    # Fetching as a list of dictionaries for easier use in Streamlit
    res = conn.execute("SELECT sender as user, message as text FROM messages WHERE item_id=? ORDER BY timestamp ASC", (item_id,)).fetchall()
    conn.close()
    return [dict(row) for row in res]