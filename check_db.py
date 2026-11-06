"""Standalone Aiven MySQL connectivity test.

Run:

    .\\.venv\\Scripts\\python.exe check_db.py

It checks that:
1. .env loads and every required variable is present.
2. DB_HOST is the Aiven hostname (not localhost).
3. The TLS handshake works with the Aiven CA certificate.
4. SELECT 1 and SELECT DATABASE() succeed.
5. The connection is encrypted (Ssl_cipher is reported when available).

Exit code 0 means the online database really answered. Any other code means the
test failed; the application must not be started without a working Aiven
connection.
"""

import sys

from app import create_app
from app.db import DatabaseError, verify_connection
from config import ConfigurationError, validate_config


def main():
    print("FitTrack - Aiven MySQL connectivity test")
    print("=" * 42)

    app = create_app()

    try:
        validate_config(app)
    except ConfigurationError as error:
        print("\nCONFIGURATION FAILED\n")
        print(error)
        return 2

    print("Configuration loaded: all required variables are present.")
    print(f"Target database: {app.config['DB_NAME']}")
    print(f"Target host: {app.config['DB_HOST']}:{app.config['DB_PORT']}")
    print("CA certificate:", app.config["DB_SSL_CA"])

    try:
        with app.app_context():
            details = verify_connection()
    except DatabaseError as error:
        print("\nCONNECTION FAILED\n")
        print(error)
        print("\nNothing was changed. The app did not fall back to another database.")
        return 3

    print("\nSELECT 1 succeeded.")
    print(f"SELECT DATABASE() -> {details['database']}")
    print(f"Server version    -> {details['server_version']}")
    print(
        "TLS cipher        ->",
        details["ssl_cipher"] or "not reported (the CA-verified TLS handshake succeeded)",
    )
    print("\nSUCCESS: connected to the online Aiven MySQL database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
