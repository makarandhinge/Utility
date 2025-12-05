#!/usr/bin/env python3
"""
ChirpStack Downlink Sender
Interactive tool to send downlinks to LoRaWAN devices
"""

import subprocess
import json
import base64
import sys

# ChirpStack server configuration
SERVER = "192.168.0.24:8081"
DEV_EUI = "0792fc1675531112"  # Your Grove E5 device

def run_grpcurl(method, data, auth_token=None):
    """Run grpcurl command and return the result"""
    cmd = ["grpcurl", "-plaintext"]
    
    if auth_token:
        cmd.extend(["-H", f"authorization: Bearer {auth_token}"])
    
    cmd.extend(["-d", json.dumps(data), SERVER, method])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Failed to parse response")
        return None

def login(username, password):
    """Login to ChirpStack and get JWT token"""
    print("🔐 Logging in...")
    data = {
        "email": username,
        "password": password
    }
    
    result = run_grpcurl("api.InternalService/Login", data)
    
    if result and "jwt" in result:
        print("✅ Login successful!")
        return result["jwt"]
    else:
        print("❌ Login failed!")
        return None

def text_to_hex(text):
    """Convert text string to hex"""
    return text.encode('utf-8').hex()

def hex_to_base64(hex_string):
    """Convert hex string to base64"""
    # Remove any spaces or non-hex characters
    hex_string = hex_string.replace(" ", "").replace("0x", "")
    
    # Convert hex to bytes
    try:
        byte_data = bytes.fromhex(hex_string)
        # Convert bytes to base64
        b64_data = base64.b64encode(byte_data).decode('utf-8')
        return b64_data
    except ValueError as e:
        print(f"❌ Invalid hex string: {e}")
        return None

def send_downlink(jwt_token, dev_eui, fport, data_base64, confirmed=False):
    """Send downlink to device"""
    print(f"\n📤 Sending downlink to device {dev_eui}...")
    
    data = {
        "queueItem": {
            "devEui": dev_eui,
            "fPort": fport,
            "data": data_base64,
            "confirmed": confirmed
        }
    }
    
    result = run_grpcurl("api.DeviceService/Enqueue", data, jwt_token)
    
    if result and "id" in result:
        print(f"✅ Downlink queued successfully!")
        print(f"   Queue ID: {result['id']}")
        return True
    else:
        print("❌ Failed to send downlink")
        return False

def main():
    print("=" * 60)
    print("   ChirpStack LoRaWAN Downlink Sender")
    print("=" * 60)
    print()
    
    # Step 1: Login
    username = input("👤 Username: ").strip()
    password = input("🔑 Password: ").strip()
    
    jwt_token = login(username, password)
    if not jwt_token:
        sys.exit(1)
    
    print()
    print("-" * 60)
    
    # Step 2: Get device info
    print("📱 Device Selection:")
    print(f"   Default: Grove E5 (DevEUI: {DEV_EUI})")
    
    # Option to change device
    change_device = input("   Use default device? (Y/n): ").strip().lower()
    if change_device == 'n':
        dev_eui = input("   Enter DevEUI: ").strip()
    else:
        dev_eui = DEV_EUI
    
    print()
    print("-" * 60)
    
    # Step 3: Get FPort
    while True:
        try:
            fport = int(input("📡 FPort (1-223): ").strip())
            if 1 <= fport <= 223:
                break
            else:
                print("   ⚠️  FPort must be between 1 and 223")
        except ValueError:
            print("   ⚠️  Please enter a valid number")
    
    print()
    
    # Step 4: Get data input method
    print("📝 Data Input Method:")
    print("   1. Enter text (will be converted to hex)")
    print("   2. Enter hex directly")
    
    while True:
        choice = input("   Choice (1/2): ").strip()
        if choice in ['1', '2']:
            break
        print("   ⚠️  Please enter 1 or 2")
    
    print()
    
    # Step 5: Get data
    if choice == '1':
        # Text input
        text_data = input("✍️  Enter text message: ").strip()
        hex_data = text_to_hex(text_data)
        print(f"   📊 Converted to hex: {hex_data}")
    else:
        # Hex input
        hex_data = input("🔢 Enter hex data (e.g., 0300 or AABBCC): ").strip()
    
    # Convert to base64
    base64_data = hex_to_base64(hex_data)
    
    if not base64_data:
        print("❌ Failed to convert data")
        sys.exit(1)
    
    print(f"   📦 Base64 encoded: {base64_data}")
    
    print()
    
    # Step 6: Confirmed downlink?
    confirmed = input("🔔 Require confirmation from device? (y/N): ").strip().lower() == 'y'
    
    print()
    print("-" * 60)
    print()
    
    # Step 7: Summary
    print("📋 Summary:")
    print(f"   Device:    {dev_eui}")
    print(f"   FPort:     {fport}")
    print(f"   Data (hex): {hex_data}")
    print(f"   Data (b64): {base64_data}")
    print(f"   Confirmed: {'Yes' if confirmed else 'No'}")
    print()
    
    confirm = input("➡️  Send downlink? (Y/n): ").strip().lower()
    
    if confirm == 'n':
        print("❌ Cancelled")
        sys.exit(0)
    
    print()
    
    # Step 8: Send downlink
    success = send_downlink(jwt_token, dev_eui, fport, base64_data, confirmed)
    
    print()
    print("=" * 60)
    
    if success:
        print("✅ Downlink sent successfully!")
        print("   The device will receive it on its next uplink (Class A)")
    else:
        print("❌ Failed to send downlink")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
