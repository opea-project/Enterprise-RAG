#!/bin/bash

ENV_FILE='.env'
CHAT_QNA_URL_ENV=VITE_CHAT_QNA_URL
DATA_INGESTION_URL_ENV=VITE_DATA_INGESTION_URL
NGINX_CONFIG_FILE='default.conf'

# Check if .env file exists
if ! test -f "$ENV_FILE"; then
  echo "Error: '$ENV_FILE' file does not exist"
  exit 1
fi

# Check if URL values exist inside .env file
CHAT_QNA_URL=$(grep "^$CHAT_QNA_URL_ENV=" "$ENV_FILE" | cut -d '=' -f 2-)
DATA_INGESTION_URL=$(grep "^$DATA_INGESTION_URL_ENV=" "$ENV_FILE" | cut -d '=' -f 2-)

if [ -z "$CHAT_QNA_URL" ]; then
    echo "Variable '$CHAT_QNA_URL_ENV' not found in '$ENV_FILE'."
    exit 1
fi

if [ -z "$DATA_INGESTION_URL" ]; then
    echo "Variable '$DATA_INGESTION_URL_ENV' not found in '$ENV_FILE'."
    exit 1
fi

# Check if nginx config file (default.conf) exists
if ! test -f "$NGINX_CONFIG_FILE"; then
  echo "Error: '$NGINX_CONFIG_FILE' (nginx config named 'default.conf') file does not exist"
  exit 1
fi

# Replace search strings with URL values inside nginx config file (default.conf)
CHAT_QNA_URL_SEARCH_STRING='<chatqna-url>'
DATA_INGESTION_URL_SEARCH_STRING='<dataprep-url>'

sed -i "s#$CHAT_QNA_URL_SEARCH_STRING#$CHAT_QNA_URL#g" "$NGINX_CONFIG_FILE"

if [ $? -eq 0 ]; then
    echo "Chat QnA URL have been set in $NGINX_CONFIG_FILE."
else
    echo "An error occurred while trying to set Chat QnA URL in $NGINX_CONFIG_FILE."
    exit 1
fi

sed -i "s#$DATA_INGESTION_URL_SEARCH_STRING#$DATA_INGESTION_URL#g" "$NGINX_CONFIG_FILE"

if [ $? -eq 0 ]; then
    echo "Data Prep URL have been set in $NGINX_CONFIG_FILE."
else
    echo "An error occurred while trying to set Data Prep URL in $NGINX_CONFIG_FILE."
    exit 1
fi
