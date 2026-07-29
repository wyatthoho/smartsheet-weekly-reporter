# Smartsheet Weekly Reporter

Fetch tasks from Smartsheet for the specified user and week, via a Streamlit web app that runs in your browser.

## Prerequisites

- OS: Ubuntu Linux
- Python: 3.12+

## Install Python Packages

Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate
```

Use `pip` to install the required packages:
```bash
pip install -e ".[dev]"
```

## Environmental Variables Setup

Create a file named `.env` in the root directory of the project:

```dotenv
API_TOKEN=your_smartsheet_api_token
SHEET_ID=your_smartsheet_id
```

## Usage

Get the streamlit running in minutes:

```bash
streamlit run main.py
```

---

## Deployment

This app is deployed on an Ubuntu VM.
The Streamlit app runs inside a Docker container.
Nginx acts as a reverse proxy to serve the application.

**Nginx Configuration**

This app shares the same Nginx server block (port 80, `localhost`) as other apps on the same host.

Add a `location` entry for this app to the existing shared config
(e.g. `/etc/nginx/sites-available/apps`), alongside the other apps' locations:

```nginx
server {
    listen 80;
    server_name localhost;

    client_max_body_size 50M;

    # ...other apps' location blocks...

    location /smartsheet-weekly-reporter {
        proxy_pass http://127.0.0.1:8502/smartsheet-weekly-reporter;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    location / {
        return 404;
    }
}
```

Then test and reload Nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**Docker Setup**

Build and run the container:

```bash
# Stop and remove the old container
docker rm -f smartsheet-weekly-reporter

# Re-compile the Docker image
docker build -t smartsheet-weekly-reporter:latest .

# Launch the container
docker run -d \
  --name smartsheet-weekly-reporter \
  -p 127.0.0.1:8502:8502 \
  -v $(pwd)/.env:/app/.env \
  --restart unless-stopped \
  smartsheet-weekly-reporter:latest
```

Confirm the container:

```bash
docker ps -a | grep smartsheet-weekly-reporter
docker logs smartsheet-weekly-reporter
```

**Access the Dashboard**

The dashboard is accessible on the company network at
`http://10.0.0.36/smartsheet-weekly-reporter/`
