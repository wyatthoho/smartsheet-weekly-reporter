FROM python:3.12-slim

WORKDIR /app

# Copy configuration files first to optimize Docker layer caching
COPY pyproject.toml README.md LICENSE ./

# Install project dependencies directly from pyproject.toml
RUN pip install --no-cache-dir .

# Copy the rest of the application files (Docker will skip files in .dockerignore)
COPY . .

# Expose Streamlit's default port inside the container
EXPOSE 8502

# Run Streamlit pointing to your root app.py
CMD ["streamlit", "run", "main.py", "--server.port=8502", "--server.address=0.0.0.0", "--server.baseUrlPath=smartsheet-weekly-reporter"]
