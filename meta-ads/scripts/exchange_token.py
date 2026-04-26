#!/usr/bin/env python3
"""Exchange a short-lived Meta user access token for a 60-day long-lived one.

This is the Path B workflow from references/setup.md. Graph API Explorer
hands you a short-lived user token (~1-2 hours); you exchange it here for
a 60-day token that's safe to put in .env.

Requires META_APP_ID and META_APP_SECRET to be set (in .env or exported).
Those come from your Meta developer app dashboard -> Settings -> Basic.

Usage:
  # Reads the short-lived token interactively (doesn't echo) and writes
  # the long-lived token to stdout as JSON.
  python scripts/exchange_token.py

  # Or pass the short-lived token as an arg (less safe — shows in shell history):
  python scripts/exchange_token.py --short-token EAAxxx...

  # Write the exchanged token into .env automatically (replaces META_ACCESS_TOKEN):
  python scripts/exchange_token.py --write-env

Exit code 0 on success, 1 on failure.

SECURITY NOTES:
  - App Secret is NEVER accepted via CLI argument. It must be set in .env
    or as an environment variable to avoid leaking into shell history.
  - When --write-env is used, the full token is NOT printed to stdout.
    Only a redacted preview (first 8 chars) is shown. This prevents the
    token from leaking into conversation context or log files.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

import requests

from meta_client import DEFAULT_VERSION, GRAPH_BASE, _load_dotenv, print_json


def exchange(app_id: str, app_secret: str, short_token: str, version: str) -> dict:
    """Call Meta's oauth/access_token endpoint. Returns parsed JSON."""
    url = f"{GRAPH_BASE}/{version}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    }
    resp = requests.get(url, params=params, timeout=30, verify=True)
    body = resp.json() if resp.content else {}
    if not resp.ok:
        raise RuntimeError(
            f"Token exchange failed (HTTP {resp.status_code}): {body.get('error', body)}"
        )
    return body


def write_env(env_path: Path, token: str) -> None:
    """Replace or append META_ACCESS_TOKEN in the .env file."""
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    out_lines = []
    replaced = False
    for line in lines:
        if line.strip().startswith("META_ACCESS_TOKEN="):
            out_lines.append(f"META_ACCESS_TOKEN={token}")
            replaced = True
        else:
            out_lines.append(line)
    if not replaced:
        out_lines.append(f"META_ACCESS_TOKEN={token}")
    env_path.write_text("\n".join(out_lines) + "\n")


def redact_token(token: str) -> str:
    """Show only the first 8 characters of a token for safe logging."""
    if len(token) <= 8:
        return token
    return token[:8] + "..." + f"({len(token)} chars)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--short-token",
        help="Short-lived user token. If omitted, you'll be prompted (hidden input).",
    )
    parser.add_argument(
        "--app-id",
        help="Meta app ID. Defaults to $META_APP_ID.",
    )
    # [SECURITY FIX H1] --app-secret CLI flag removed.
    # App Secret must come from .env or environment variable only,
    # to prevent it from appearing in shell history or process listings.
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write the long-lived token into .env (replaces META_ACCESS_TOKEN).",
    )
    parser.add_argument(
        "--show-full-token",
        action="store_true",
        help="Print the full token to stdout (use only if you need to copy it manually).",
    )
    parser.add_argument(
        "--env-path",
        default=".env",
        help="Path to .env file. Default: .env in the current directory.",
    )
    args = parser.parse_args()

    _load_dotenv()

    app_id = args.app_id or os.environ.get("META_APP_ID")
    # [SECURITY] App secret only from env — never from CLI args.
    app_secret = os.environ.get("META_APP_SECRET")
    version = os.environ.get("META_API_VERSION", DEFAULT_VERSION)

    if not app_id or not app_secret:
        print_json(
            {
                "ok": False,
                "error": (
                    "Missing META_APP_ID and/or META_APP_SECRET. Add them to .env "
                    "or export them as environment variables. Find them in your Meta "
                    "developer app dashboard -> Settings -> Basic. "
                    "(App Secret cannot be passed via CLI for security reasons.)"
                ),
            }
        )
        return 1

    short = args.short_token
    if not short:
        short = getpass.getpass("Paste short-lived token (input hidden): ").strip()
        if not short:
            print_json({"ok": False, "error": "No short token provided."})
            return 1

    try:
        resp = exchange(app_id, app_secret, short, version)
    except Exception as e:
        print_json({"ok": False, "error": str(e)})
        return 1

    long_token = resp.get("access_token")
    expires_in = resp.get("expires_in")
    if not long_token:
        print_json({"ok": False, "error": "Exchange succeeded but no access_token returned.", "raw": resp})
        return 1

    days = expires_in / 86400 if expires_in else None

    if args.write_env:
        env_path = Path(args.env_path)
        write_env(env_path, long_token)
        env_action = f"Wrote META_ACCESS_TOKEN to {env_path.resolve()}"
    else:
        env_action = "Not written to .env (pass --write-env to do so)."

    # [SECURITY FIX H2] By default, redact the token in output to prevent
    # it from leaking into conversation context, logs, or terminal scrollback.
    # Only show the full token if --show-full-token is explicitly passed AND
    # --write-env is NOT used (if it's already saved to .env, there's no
    # reason to also echo it).
    if args.show_full_token and not args.write_env:
        token_display = long_token
    else:
        token_display = redact_token(long_token)

    print_json(
        {
            "ok": True,
            "long_lived_token": token_display,
            "token_saved_to_env": args.write_env,
            "expires_in_seconds": expires_in,
            "expires_in_days": round(days, 1) if days else None,
            "env_action": env_action,
            "reminder": (
                "Delete the short-lived token from wherever you pasted it. "
                "The long-lived token is good for ~60 days — set a calendar "
                "reminder to regenerate."
            ),
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
