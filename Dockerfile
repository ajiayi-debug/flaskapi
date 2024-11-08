# Use an official lightweight Python image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary files and folders
COPY backend /app
COPY .env /app/.env
COPY games_description.csv /app/games_description.csv

# Expose the Flask port
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Run the Flask app
CMD ["python", "main.py"]