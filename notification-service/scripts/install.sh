#!/bin/bash -e
# 
# Instalar el repositorio en el directorio actual

# Remove already existing virtualenv
if [ -d ".venv" ]; then rm -Rf venv; fi

# Configure poetry to use venv
pip install poetry 
poetry env use python3
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# Install poetry env with dependencies
poetry install

