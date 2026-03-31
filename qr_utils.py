import qrcode
import os

QR_FOLDER = "qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)

def generate_qr(item_name, phone, reward, filename):
    """
    Generates a QR code including the item name, contact, and reward info.
    """
    # Constructing the data string to be stored in the QR
    qr_data = f"📦 Item: {item_name}\n📞 Contact: {phone}"
    if reward:
        qr_data += f"\n🎁 Reward: {reward}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save path
    path = os.path.join(QR_FOLDER, f"{filename}.png")
    img.save(path)
    return path