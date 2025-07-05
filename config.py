from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from a .env file if it exists
_env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=_env_path, override=False)

def get_env(name: str, default=None, required: bool = False):
    """Retrieve environment variable from os.environ.

    Args:
        name: The environment variable name.
        default: Optional default if the variable is not set.
        required: If True, raise an error when the variable is missing.

    Returns:
        The value of the environment variable or the default.
    """
    value = os.getenv(name, default)
    if required and value is None:
        raise EnvironmentError(f"Environment variable '{name}' is required")
    return value
