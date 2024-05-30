# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT 8051

# Create and set the working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt .

# Install the required dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the image
COPY . .

# Expose the port Streamlit will run on
EXPOSE 8051

# Run the Streamlit app
CMD ["streamlit", "run", "Streamlit_Map.py", "--server.port=$PORT", "--server.enableCORS=false"]
 

