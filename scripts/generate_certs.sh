#!/bin/bash
# Milestone 22: Generate mTLS certificates for Secure Aggregation

mkdir -p certs
cd certs

echo "Generating CA certificate..."
openssl req -new -x509 -days 3650 -nodes -text -out ca.crt -keyout ca.key -subj "/CN=FL-Root-CA"

echo "Generating Server certificate..."
openssl req -new -nodes -text -out server.csr -keyout server.key -subj "/CN=fl_server"
openssl x509 -req -in server.csr -text -days 3650 -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

echo "Generating Client certificate..."
openssl req -new -nodes -text -out client.csr -keyout client.key -subj "/CN=fl_client"
openssl x509 -req -in client.csr -text -days 3650 -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt

echo "mTLS certificates generated successfully in certs/"
