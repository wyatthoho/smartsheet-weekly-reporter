# Smartsheet Weekly Reporter

Fetch tasks from Smartsheet for the specified week and formats them for easy pasting straight into PowerPoint slides.

## Prerequisites

- OS: Windows (required for clipboard actions)
- Python: 3.12+

## Install Python Packages

Create a virtual environment and activate it:
```bash
py -m venv venv
.\venv\Scripts\activate
```

Use `pip` to install the required packages:
```bash
python -m pip install -e ".[dev]"
```

## Environmental Variables Setup

Create a file named `.env` in the root directory of the project:

```dotenv
API_TOKEN=your_smartsheet_api_token
SHEET_ID=your_smartsheet_id
EMPLOYEE=Your Email As It Appears In Smartsheet
```

## Usage
Run the script using one of the following commands:

```bash
weekly-report  # For current week
weekly-report --last-week  # For last week
weekly-report --next-week  # For next week
```

Once the terminal prints "Copied to clipboard", 
navigate to your slide deck and press Ctrl+V to paste the styled text.
