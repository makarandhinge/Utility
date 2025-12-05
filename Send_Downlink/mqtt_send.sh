#!/bin/bash
# Interactive MQTT Downlink Sender for ChirpStack
# No login required - MQTT doesn't need authentication

# MQTT Server Configuration
MQTT_HOST="192.168.0.24"
MQTT_PORT="1883"

# Default values
DEFAULT_DEV_EUI="0792fc1675531112"
DEFAULT_APP_ID="4f3d5d92-af2a-4466-9f1e-d2e56b764ea8"

echo "============================================================"
echo "   ChirpStack MQTT Downlink Sender"
echo "============================================================"
echo ""

# Step 1: Application ID
echo "📱 Application ID:"
echo "   Default: $DEFAULT_APP_ID"
read -p "   Use default? (Y/n): " use_default_app

if [[ "$use_default_app" =~ ^[Nn]$ ]]; then
    read -p "   Enter Application ID: " APP_ID
else
    APP_ID="$DEFAULT_APP_ID"
fi

echo ""
echo "------------------------------------------------------------"

# Step 2: Device EUI
echo "📟 Device EUI:"
echo "   Default: $DEFAULT_DEV_EUI (Grove E5)"
read -p "   Use default? (Y/n): " use_default_dev

if [[ "$use_default_dev" =~ ^[Nn]$ ]]; then
    read -p "   Enter DevEUI: " DEV_EUI
else
    DEV_EUI="$DEFAULT_DEV_EUI"
fi

echo ""
echo "------------------------------------------------------------"

# Step 3: FPort
while true; do
    read -p "📡 FPort (1-223): " FPORT
    if [[ "$FPORT" =~ ^[0-9]+$ ]] && [ "$FPORT" -ge 1 ] && [ "$FPORT" -le 223 ]; then
        break
    else
        echo "   ⚠️  FPort must be between 1 and 223"
    fi
done

echo ""
echo "------------------------------------------------------------"

# Step 4: Data input method
echo "📝 Data Input Method:"
echo "   1. Enter text (will be converted to hex)"
echo "   2. Enter hex directly"

while true; do
    read -p "   Choice (1/2): " choice
    if [[ "$choice" == "1" ]] || [[ "$choice" == "2" ]]; then
        break
    else
        echo "   ⚠️  Please enter 1 or 2"
    fi
done

echo ""

# Step 5: Get data
if [ "$choice" == "1" ]; then
    # Text input
    read -p "✍️  Enter text message: " text_data
    HEX_DATA=$(echo -n "$text_data" | xxd -p | tr -d '\n')
    echo "   📊 Converted to hex: $HEX_DATA"
else
    # Hex input
    read -p "🔢 Enter hex data (e.g., 0300 or AABBCC): " HEX_DATA
fi

# Convert to base64
DATA=$(echo -n "$HEX_DATA" | xxd -r -p | base64)

if [ -z "$DATA" ]; then
    echo "❌ Error: Failed to convert data"
    exit 1
fi

echo "   📦 Base64 encoded: $DATA"

echo ""

# Step 6: Confirmed downlink
read -p "🔔 Require confirmation from device? (y/N): " confirmed_input

if [[ "$confirmed_input" =~ ^[Yy]$ ]]; then
    CONFIRMED="true"
else
    CONFIRMED="false"
fi

echo ""
echo "------------------------------------------------------------"
echo ""

# Step 7: Summary
echo "📋 Summary:"
echo "   Application: $APP_ID"
echo "   Device:      $DEV_EUI"
echo "   FPort:       $FPORT"
echo "   Data (hex):  $HEX_DATA"
echo "   Data (b64):  $DATA"
echo "   Confirmed:   $CONFIRMED"
echo "   MQTT Server: $MQTT_HOST:$MQTT_PORT"
echo ""

read -p "➡️  Send downlink? (Y/n): " confirm

if [[ "$confirm" =~ ^[Nn]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""

# Step 8: Build and send
TOPIC="application/${APP_ID}/device/${DEV_EUI}/command/down"
MESSAGE="{\"devEui\":\"${DEV_EUI}\",\"confirmed\":${CONFIRMED},\"fPort\":${FPORT},\"data\":\"${DATA}\"}"

echo "📤 Sending downlink via MQTT..."

mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -t "$TOPIC" -m "$MESSAGE"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Downlink sent successfully via MQTT!"
    echo "   The device will receive it on its next uplink (Class A)"
    echo "============================================================"
else
    echo ""
    echo "============================================================"
    echo "❌ Failed to send downlink"
    echo "============================================================"
    exit 1
fi
