#!/bin/bash
# MQTT Downlink Sender for ChirpStack
# Usage: ./mqtt_send.sh <hex_data> [fport] [confirmed]

HEX_DATA="$1"
FPORT="${2:-2}"
CONFIRMED="${3:-false}"

# Configuration
APP_ID="4f3d5d92-af2a-4466-9f1e-d2e56b764ea8"
DEV_EUI="0792fc1675531112"
MQTT_HOST="192.168.0.24"
MQTT_PORT="1883"

# Check if hex data provided
if [ -z "$HEX_DATA" ]; then
    echo "Usage: $0 <hex_data> [fport] [confirmed]"
    echo ""
    echo "Examples:"
    echo "  $0 0300              # Send hex 0300 on port 2"
    echo "  $0 AABBCC 3          # Send hex AABBCC on port 3"
    echo "  $0 0300 2 true       # Send confirmed downlink"
    exit 1
fi

# Convert hex to base64
DATA=$(echo -n "$HEX_DATA" | xxd -r -p | base64)

if [ -z "$DATA" ]; then
    echo "❌ Error: Failed to convert hex data"
    exit 1
fi

# Build MQTT topic
TOPIC="application/${APP_ID}/device/${DEV_EUI}/command/down"

# Build JSON message
MESSAGE="{\"devEui\":\"${DEV_EUI}\",\"confirmed\":${CONFIRMED},\"fPort\":${FPORT},\"data\":\"${DATA}\"}"

# Send via MQTT
echo "📤 Sending downlink via MQTT..."
echo "   Device:    $DEV_EUI"
echo "   FPort:     $FPORT"
echo "   Hex Data:  $HEX_DATA"
echo "   Base64:    $DATA"
echo "   Confirmed: $CONFIRMED"
echo ""

mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -t "$TOPIC" -m "$MESSAGE"

if [ $? -eq 0 ]; then
    echo "✅ Downlink sent successfully via MQTT!"
else
    echo "❌ Failed to send downlink"
    exit 1
fi
