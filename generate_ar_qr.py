import urllib.request
import os

def generate_qr_code(url, output_filename="ar_qr_code.png"):
    """
    Generates a QR code for the given URL using a free public API 
    and saves it to the specified output file.
    """
    print(f"Generating QR code for: {url}")
    
    # Using the goqr.me API for quick generation
    # 250x250 pixels
    api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={url}"
    
    try:
        urllib.request.urlretrieve(api_url, output_filename)
        print(f"✅ Success! QR code saved as: {output_filename}")
        print("You can embed this image in your PDF reports.")
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")

if __name__ == "__main__":
    # --- PROTOTYPE INSTRUCTIONS ---
    # 1. Start your frontend development server (e.g., npm run dev)
    # 2. Find out your local network IP address (e.g., 192.168.1.5)
    # 3. Replace the URL below with your local IP and the path to the AR viewer
    # Example: "http://192.168.1.5:5173/ar_viewer.html"
    
    # Change this to your computer's local IP address and port so your phone can reach it!
    LOCAL_IP_URL = "http://10.173.5.196:5173/ar_viewer.html"
    
    generate_qr_code(LOCAL_IP_URL)
