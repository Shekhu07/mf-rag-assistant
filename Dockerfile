# Use the official lightweight Python 3.11 image
FROM python:3.11-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /app

# Install basic system build dependencies (required for some compiled libraries like Chroma/hnswlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
# Note: We copy everything including the pre-ingested vector_store directory
COPY . .

# Expose port 8501 (the standard port Streamlit runs on)
EXPOSE 8501

# Run healthcheck to ensure Streamlit is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Grant execute permission to the startup script
RUN chmod +x start.sh

# Launch the services via startup script
CMD ["./start.sh"]
