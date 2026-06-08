import os
from dotenv import load_dotenv


def load_env_variables():
    env = os.getenv("ENV_MODE", "dev")
    env_file = f".env.{env}"

    if os.path.exists(env_file):
        load_dotenv(env_file)

    border = "=" * 30
    print(border)
    print(f"  ENV_MODE : {env.upper()}")
    print(f"  UNMIX    : {os.getenv('ENABLE_UNMIX', 'false')}")
    print(border)

    return {
        "enable_unmix":        os.getenv("ENABLE_UNMIX", "false").lower() == "true",
        "unmix_worker_script": os.getenv("UNMIX_WORKER_SCRIPT", "/app/unmix_worker.py"),
        "python_sp_venv_path": os.getenv("PYTHON_SP_VENV_PATH", "python"),
        "temp_dir":            os.getenv("TEMP_DIR", "/tmp/song_processing"),
    }


env_vars = load_env_variables()

ENABLE_UNMIX        = env_vars["enable_unmix"]
UNMIX_WORKER_SCRIPT = env_vars["unmix_worker_script"]
PYTHON_SP_VENV_PATH = env_vars["python_sp_venv_path"]
TEMP_DIR            = env_vars["temp_dir"]
