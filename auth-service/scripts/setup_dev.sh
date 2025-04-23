#!/bin/bash -e
# 
# Hacer setup para desarrollo local

# Configure Git user
IFS= read -r -p "Enter user name (e.g. John Doe): " name
IFS= read -r -p "Enter user e-mail (e.g. john.dow@gmail.com): " email

git config user.name "$name"
git config user.email "$email"

# Give execution permissions to commands
chmod +x commands/*
