# Use a slim Python image for efficiency on Raspberry Pi
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the database directory exists and is writable
# We will use a volume for this in docker-compose
RUN mkdir -p /app/data

# Set the environment variable for the database to live in the persistent volume
ENV DATABASE_PATH=/app/data/threads_scheduler.db

# Command to run the scheduler
CMD ["python", "manage.py", "run"]
