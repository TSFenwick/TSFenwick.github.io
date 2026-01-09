# /// script
# dependencies = [
#   "tomli",
#   "qrcode[pil]",
#   "pillow",
# ]
# ///

import tomli
import os
import qrcode
from PIL import Image

# === CONFIGURATION ===
TOML_FILE = 'data.toml'
OUTPUT_DIR = 'qrcodes'
# REPLACE THIS WITH YOUR ACTUAL LIVE URL AFTER HOSTING
BASE_URL = 'https://your-fast-map-site.netlify.app' 
# Path to your central logo image (e.g., 'branding/logo.png'). 
# Set to None if you don't want a logo.
LOGO_PATH = 'logo.png' 
# =====================

def create_qr_with_logo(url, output_path, logo_path=None):
    """
    Generates a QR code that points to the URL and optionally embeds a center logo.
    """
    # 1. Generate QR Code
    # We use ERROR_CORRECT_H (High) to allow data redundancy. 
    # This lets us cover up to 30% of the center with a logo and it still scans.
    qr = qrcode.QRCode(
        version=None, # Auto-determine size based on URL length
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Create standard black on white QR image
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # 2. Embed Logo (if provided)
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            
            # Calculate dimensions to ensure logo fits well.
            # Making the logo about 1/4th the width of the QR code usually works well.
            qr_width, qr_height = qr_img.size
            logo_size = int(qr_width / 4)
            
            # Resize logo maintaining aspect ratio
            logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate center position
            pos = ((qr_width - logo.size[0]) // 2, (qr_height - logo.size[1]) // 2)
            
            # Optional: Add a small white border around the logo for cleaner look
            # Paste the logo onto the QR image (using logo itself as mask if it has transparency)
            qr_img.paste(logo, pos, logo if 'A' in logo.getbands() else None)
            print(f"  - Embedded logo into {os.path.basename(output_path)}")

        except Exception as e:
            print(f"Warning: Could not process logo {logo_path}: {e}")

    # 3. Save final image
    qr_img.save(output_path)
    print(f"Generated: {output_path} -> {url}")


def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Reading {TOML_FILE}...")
    try:
        with open(TOML_FILE, "rb") as f:
            data = tomli.load(f)
    except FileNotFoundError:
        print(f"Error: {TOML_FILE} not found!")
        return

    targets = []
    
    # 1. Get generic locations
    if 'locations' in data:
        targets.extend(data['locations'])
        
    # 2. Get specific businesses (optional: if you want QR codes for specific shops too)
    if 'businesses' in data:
        targets.extend(data['businesses'])

    print(f"Found {len(targets)} locations to generate QR codes for.\n")

    for target in targets:
        # Ensure required fields exist
        if not all(k in target for k in ('id', 'lat', 'long')):
             print(f"Skipping item missing ID, lat, or long: {target.get('name', 'Unknown')}")
             continue

        # Construct URL parameters
        params = f"?lat={target['lat']}&lng={target['long']}"
        # Add zoom parameter if specified in TOML
        if 'zoom' in target:
            params += f"&zoom={target['zoom']}"
            
        full_url = BASE_URL + params
        file_name = os.path.join(OUTPUT_DIR, f"{target['id']}.png")
        
        create_qr_with_logo(full_url, file_name, LOGO_PATH)

    print(f"\n✅ Done! Check the '/{OUTPUT_DIR}' folder.")

if __name__ == "__main__":
    main();
