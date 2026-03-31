import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- SETTINGS ---
SENDER_EMAIL = "ownbacklostitfinditgetit@gmail.com"
# Ensure this 16-character string has NO spaces
APP_PASSWORD = "ltxwvntewtorhtzk" 

def send_email(receiver_email, subject, html_body):
    """Core function to handle SMTP connection and sending."""
    try:
        # 1. Create the message container first
        msg = MIMEMultipart()
        msg['From'] = f"OWN BACK <{SENDER_EMAIL}>"
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        # 2. Connect to Gmail SMTP Server
        # Port 587 + starttls is the most reliable method
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls() 
        server.login(SENDER_EMAIL, APP_PASSWORD)
        
        # 3. Send and Close
        server.send_message(msg)
        server.quit()
        return True
        
    except Exception as e:
        # Detailed error logging for your terminal
        print(f"📧 EMAIL SERVICE ERROR: {e}") 
        return False

def send_otp_email(receiver_email, otp):
    """Sends a styled OTP email for login verification."""
    body = f"""
    <div style="font-family: Arial, sans-serif; border: 2px solid #238636; padding: 20px; border-radius: 10px; max-width: 400px;">
        <h2 style="color: #238636; text-align: center;">🛡️ OWN BACK SECURITY</h2>
        <p>Your verification code is:</p>
        <div style="background: #f4f4f4; padding: 10px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px;">
            {otp}
        </div>
        <p style="font-size: 12px; color: #666; margin-top: 20px;">
            This code will expire in 10 minutes. If you did not request this, please ignore this email.
        </p>
    </div>
    """
    return send_email(receiver_email, "🔐 OWN BACK OTP", body)

def send_match_notification(receiver_email, item_name, match_percent):
    """Sends a notification when an AI match is found."""
    body = f"""
    <div style="font-family: Arial, sans-serif; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        <h2 style="color: #007bff;">🔔 Potential Match Found!</h2>
        <p>Our system found a <b>{match_percent}% match</b> for your item:</p>
        <h3 style="background: #e7f3ff; padding: 10px;">{item_name}</h3>
        <p>Login to the dashboard to view details and claim your item.</p>
    </div>
    """
    return send_email(receiver_email, "🔔 OWN BACK Match Found", body)