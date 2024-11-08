import os
from dotenv import load_dotenv, set_key
from pathlib import Path
import secrets

# Load any existing .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Check if SECRET_KEY exists in the .env file
secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    # Generate a new secret key
    secret_key = secrets.token_hex(16)
    print("Generated a new secret key:", secret_key)

    # Save the new secret key to the .env file
    with open(env_path, 'a') as f:
        f.write(f'\nSECRET_KEY={secret_key}')

    print("Secret key saved to .env file.")
else:
    print("Using existing secret key.")