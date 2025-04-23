#!/bin/bash -e
# 
# Hacer setup para desarrollo local

# Configure Git event
IFS= read -r -p "Enter event name (e.g. John Doe): " name
IFS= read -r -p "Enter event e-mail (e.g. john.dow@gmail.com): " email

git config event.name "$name"
git config event.email "$email"

# Give execution permissions to commands
chmod +x commands/*
