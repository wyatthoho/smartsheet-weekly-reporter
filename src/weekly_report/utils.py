import logging
import os


logger = logging.getLogger(__name__)


def get_env_variable(key: str) -> str:
    var = os.getenv(key)
    if not var:
        msg = f'{key} environment variable is not set.'
        raise ValueError(msg)
    return var
