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
streamlit run ./src/weekly_report/main.py 
```
