#!/bin/bash

mkdir -p ~/.aws
echo "[default]" > ~/.aws/credentials
echo "aws_access_key_id = $Access_key_ID" >> ~/.aws/credentials
echo "aws_secret_access_key = $Secret_access_key" >> ~/.aws/credentials

echo "[default]" > ~/.aws/config
echo "region = us-east-1" >> ~/.aws/config

exec streamlit run insights.py --server.port 8000 --server.address 0.0.0.0

  
