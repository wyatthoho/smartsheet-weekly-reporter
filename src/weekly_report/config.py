import os
import sys

from dotenv import find_dotenv, load_dotenv

ENV_API_TOKEN = "API_TOKEN"
ENV_SHEET_ID = "SHEET_ID"
ENV_EMPLOYEE = "EMPLOYEE"


def _get_env_variable(key: str) -> str:
    var = os.getenv(key)
    if not var:
        msg = f"{key} environment variable is not set."
        raise ValueError(msg)
    return var


def load_env_config() -> tuple[str, str, str]:
    try:
        load_dotenv(find_dotenv())
        api_token = _get_env_variable(ENV_API_TOKEN)
        sheet_id = _get_env_variable(ENV_SHEET_ID)
        employee = _get_env_variable(ENV_EMPLOYEE)
    except ValueError:
        sys.exit(1)
    return api_token, sheet_id, employee
