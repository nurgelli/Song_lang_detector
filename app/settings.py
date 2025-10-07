import os
from dotenv import load_dotenv


def load_env_variables():
  try:
    env = os.getenv("ENV_MODE", "dev")
    load_dotenv(f'.env.{env}')

    line_length = len(f"ENV_MODE {env}") + 4
    border = '*' * line_length
    content = f"* ENV_MODE-{env} *"

    print(border)
    print(content.upper())
    print(border)
  except FileNotFoundError as e:
    print(f".env file not found: Error {e}")

  return {
    "api_token": os.getenv("API_TOKEN"),
    "api_base_url": os.getenv("API_BASE_URL"),
    "api_update_url": os.getenv("API_UPDATE_URL"),
    
  }

env_vars = load_env_variables()


API_TOKEN = env_vars['api_token']
API_BASE_URL = env_vars['api_base_url']
API_UPDATE_URL = env_vars['api_update_url']
