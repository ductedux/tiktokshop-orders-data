
#!/usr/bin/env python3
# refresh_token_cli.py
# Refresh access token for any shop by passing app credentials + refresh token via CLI.
import os, argparse
from importlib import import_module

def parse_args():
    p = argparse.ArgumentParser(description="Refresh TikTok Shop access token via CLI params (no .env needed).")
    p.add_argument("--app-key", required=True)
    p.add_argument("--app-secret", required=True)
    p.add_argument("--refresh-token", required=True)
    p.add_argument("--dotenv-path", default=".env", help="Where to update tokens if underlying script writes to .env (optional)")
    return p.parse_args()

def main():
    args = parse_args()
    # set env so the existing script picks them up
    os.environ["TTS_APP_KEY"] = args.app_key
    os.environ["TTS_APP_SECRET"] = args.app_secret
    os.environ["TTS_REFRESH_TOKEN"] = args.refresh_token
    os.environ["DOTENV_PATH"] = args.dotenv_path
    # import and run the existing script's logic
    mod = import_module("refresh_env_token")
    # it runs on import; if not, nothing to do (the module prints its result)

if __name__ == "__main__":
    main()
