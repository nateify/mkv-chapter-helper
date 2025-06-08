import os
import shutil
from pathlib import Path


def find_executable_path(tool_name, args_path=None, env_var_name=None):
    """
    Args:
        tool_name: Name of the executable
        args_path: Path from argparse arguments
        env_var_name: Environment variable name to check

    Returns:
        Path: Path to executable if found, None otherwise
    """

    if args_path:
        path = Path(args_path)
        if path.is_file():
            return path

    path_from_env = shutil.which(tool_name)
    if path_from_env:
        return Path(path_from_env)

    if env_var_name and env_var_name in os.environ:
        env_path = Path(os.environ[env_var_name])
        if env_path.is_file():
            return env_path

    return None


def path_validate(path_str):
    """Validates that a given path string points to an existing file."""
    if not path_str:
        return None
    input_path = Path(path_str)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return str(input_path)
