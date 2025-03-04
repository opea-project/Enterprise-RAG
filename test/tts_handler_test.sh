#!/bin/bash

# Define the URL for the TorchServe inference API
URL="http://localhost:8090/predictions/speecht5_tts"

# Define the input JSON payload
INPUT_JSON=$(cat <<EOF
{
  "inputs": ["Hello, how can I help you today?"]
}
EOF
)

# Send the request to the TorchServe inference API
RESPONSE=$(curl -X POST "$URL" -H "Content-Type: application/json" -d "$INPUT_JSON")

# Check if the response contains valid data
if [[ $RESPONSE == *"["* ]]; then
  # Write the response to a file
  echo $RESPONSE > output.json
#   echo $RESPONSE | jq -r '.[0]' > output.json
  echo "Inference successful, output saved to output.json"

  # Convert the JSON array to a numpy array and save as WAV file
  python3 - <<EOF
import json
import numpy as np
import soundfile as sf

# Load the JSON data
with open("output.json", "r") as f:
    data = json.load(f)

# Convert the list to a numpy array
audio_data = np.array(data)

# Save the numpy array as a WAV file
sf.write("output.wav", audio_data, samplerate=16000)

# Verify the WAV file
with open("output.wav", "rb") as f:
    bytes = f.read()

import base64
b64_str = base64.b64encode(bytes).decode()
assert b64_str[:3] == "Ukl"

print("WAV file created successfully: output.wav")
EOF

else
  echo "Inference failed"
fi
#!/bin/bash

# # Define the URL for the TorchServe inference API
# URL="http://localhost:8090/predictions/speecht5_tts"

# # Define the input JSON payload
# INPUT_JSON=$(cat <<EOF
# {
#   "inputs": ["Hello, how can I help you today?"]
# }
# EOF
# )

# # Send the request to the TorchServe inference API
# curl -X POST "$URL" -H "Content-Type: application/json" -d "$INPUT_JSON" -o output.wav

# # Check if the output file was created
# if [ -f "output.wav" ]; then
#   echo "Inference successful, output saved to output.wav"
# else
#   echo "Inference failed"
# fi
