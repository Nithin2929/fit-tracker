"""Flask application entry point.

Start the development server with:

    .\\.venv\\Scripts\\python.exe run.py

The app validates the Aiven MySQL configuration and verifies the live database
connection before the web server starts. There is no local database fallback.
"""

import sys

from app import create_app
from app.db import DatabaseError, verify_connection
from config import ConfigurationError, validate_config


def main():
    app = create_app()

    # 1. Validate environment variables before serving any request.
    try:
        validate_config(app)
    except ConfigurationError as error:
        print("\nFitTrack configuration error\n" + "=" * 32)
        print(error)
        print("\nThe server was not started.")
        return 1

    # 2. Verify the Aiven database is reachable and TLS is working.
    try:
        with app.app_context():
            details = verify_connection()
    except DatabaseError as error:
        print("\nFitTrack could not verify Aiven MySQL\n" + "=" * 40)
        print(error)
        print("\nThe server was not started. Run `python check_db.py` for details.")
        return 1

    print("\nAiven MySQL connection verified.")
    print(f"  Database : {details['database']}")
    print(f"  Server   : {details['server_version']}")
    print(f"  TLS      : {details['ssl_cipher'] or 'cipher not reported, TLS handshake OK'}")

    # 3. Start the Flask development server. Debug must be enabled explicitly
    # through FLASK_DEBUG=true and must never be used in production.
    host = app.config.get("APP_HOST") or "127.0.0.1"
    port = int(app.config.get("APP_PORT") or 5000)
    print(f"\nStarting FitTrack at http://{host}:{port}\n")
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
