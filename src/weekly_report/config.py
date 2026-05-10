import sys
from dotenv import load_dotenv, find_dotenv
from weekly_report.env import get_env_variable


ENV_API_TOKEN = "API_TOKEN"
ENV_SHEET_ID = "SHEET_ID"
ENV_EMPLOYEE = "EMPLOYEE"

FIELD_ASSIGN = "Assigned To"
FIELD_START = "Start Date"
FIELD_END = "End Date"
FIELD_TASK = "Task"


def load_env_config() -> tuple[str, str, str]:
    try:
        load_dotenv(find_dotenv())
        api_token = get_env_variable(ENV_API_TOKEN)
        sheet_id = get_env_variable(ENV_SHEET_ID)
        employee = get_env_variable(ENV_EMPLOYEE)
    except ValueError:
        sys.exit(1)
    return api_token, sheet_id, employee
