FROM python:3.11-slim

WORKDIR /app

# First copy only what's needed for dependency installation
COPY pyproject.toml README.md poetry.lock* ./
COPY scripts ./scripts/

# Make scripts executable
RUN chmod +x ./scripts/*.sh

# Copy the Python code before installation
COPY ./app ./app/

# Now run installation with all the necessary files
RUN ./scripts/install.sh

# Copy the rest of the files
COPY . .

EXPOSE 3001

CMD ["./scripts/run_app.sh"]