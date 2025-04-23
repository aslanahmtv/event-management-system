#!/bin/bash -e
# 
# Hacer setup para desarrollo local

# Configure Git notification
IFS= read -r -p "Enter notification name (e.g. John Doe): " name
IFS= read -r -p "Enter notification e-mail (e.g. john.dow@gmail.com): " email

git config notification.name "$name"
git config notification.email "$email"

# Give execution permissions to commands
chmod +x commands/*
