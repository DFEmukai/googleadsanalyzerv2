"""Generate Google Ads API refresh token.

Run this script once to get a refresh token for the Google Ads API.
You need to have a Google Cloud project with the Google Ads API enabled
and OAuth 2.0 credentials (Desktop App) created.

Usage:
    python scripts/generate_refresh_token.py

The script will open a browser window for authentication.
After granting access, copy the refresh token to your .env file.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    client_id = input("Enter your Google OAuth Client ID: ").strip()
    client_secret = input("Enter your Google OAuth Client Secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("Refresh Token obtained successfully!")
    print("=" * 60)
    print(f"\nGOOGLE_ADS_REFRESH_TOKEN={credentials.refresh_token}")
    print("\nAdd this to your .env file.")
    print("=" * 60)


if __name__ == "__main__":
    main()
