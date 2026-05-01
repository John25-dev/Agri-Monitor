# app.py
import datetime
import logging
from typing import Any

import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EMAIL_DOMAIN = "@jofarm.com"
DEFAULT_ROLE = "SUBORDINATE"

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder=".")
    CORS(app)

    # Attach bcrypt for password hashing
    app.config["BCRYPT_LOG_ROUNDS"] = 12
    bcrypt = Bcrypt(app)
    app.config["BCRYPT"] = bcrypt

    # Placeholder for DB client attachment
    # app.db = YourAsyncDBClient(...)  # Attach your real DB client here

    # Register routes
    _register_routes(app)

    return app

# Role-based access control
def roles_required(*allowed_roles: str):
    """
    Decorator to enforce role-based access using X-User-Role header.
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            role = request.headers.get("X-User-Role")
            if not role or role not in allowed_roles:
                return jsonify({"error": "Forbidden: Access restricted"}), 403
            return await f(*args, **kwargs)
        return wrapper
    return decorator

# Helpers
def _get_db(app: Flask) -> Any:
    db = getattr(app, "db", None)
    if db is None:
        raise RuntimeError("Database client not configured on app.")
    return db

def _handle_exception(e: Exception) -> tuple[dict, int]:
    logger.exception("Unhandled exception: %s", e)
    return {"error": "Internal server error"}, 500

def _serve_index():
    return send_from_directory(".", "index.html")

def _register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return _serve_index()

    @app.route("/api/register", methods=["POST"])
    async def register():
        try:
            data = request.get_json(silent=True) or {}
            email = (data.get("email") or "").strip().lower()
            username = (data.get("username") or "").strip()
            password = (data.get("password") or "")

            if not email or not username or not password:
                return jsonify({"error": "email, username, and password are required"}), 400

            if not email.endswith(ALLOWED_EMAIL_DOMAIN) or "@" not in email:
                return jsonify({"error": "Only valid @jofarm.com emails allowed"}), 403

            bcrypt: Bcrypt = app.config["BCRYPT"]
            hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

            role = DEFAULT_ROLE

            db = _get_db(app)
            # Adapt to your DB library: parameterized insert
            await db.execute(
                """
                INSERT INTO User (email, username, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (email, username, hashed_pw, role),
            )
            return jsonify({"status": "success"}), 201

        except Exception as e:
            logger.exception("Registration failed: %s", e)
            # Could refine by checking for duplicate key errors
            return jsonify({"error": "User already exists"}), 400

    @app.route("/api/login", methods=["POST"])
    async def login():
        try:
            data = request.get_json(silent=True) or {}
            username = (data.get("username") or "").strip()
            password = data.get("password") or ""

            if not username or not password:
                return jsonify({"error": "username and password are required"}), 400

            db = _get_db(app)
            row = await db.fetch_one(
                """
                SELECT * FROM User
                WHERE username = ? OR email = ?
                """,
                (username, username),
            )

            bcrypt: Bcrypt = app.config["BCRYPT"]
            if row and bcrypt.check_password_hash(row["password_hash"], password):
                return jsonify({
                    "status": "success",
                    "role": row["role"],
                    "username": row["username"]
                })

            return jsonify({"error": "Invalid credentials"}), 401

        except Exception as e:
            logger.exception("Login failed: %s", e)
            return jsonify({"error": "Invalid credentials"}), 401

    @app.route("/api/transaction", methods=["POST"])
    async def transaction():
        try:
            data = request.get_json(silent=True) or {}
            client_id = data.get("client_id")
            amount = data.get("amount")

            if client_id is None or amount is None:
                return jsonify({"error": "client_id and amount are required"}), 400

            timestamp = datetime.datetime.utcnow().isoformat()

            ip = request.remote_addr
            location_data = {}
            try:
                resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
                if resp.ok:
                    location_data = resp.json() or {}
            except Exception:
                location_data = {}

            location = location_data.get("city") or location_data.get("region") or "Unknown"

            db = _get_db(app)
            await db.execute(
                """
                INSERT INTO Transactions (client_id, amount, timestamp, location)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, amount, timestamp, location),
            )

            return jsonify({
                "status": "success",
                "amount": amount,
                "timestamp": timestamp,
                "location": location
            }), 201

        except Exception as e:
            logger.exception("Transaction failed: %s", e)
            return jsonify({"error": "Transaction failed"}), 500

    @app.route("/api/admin/financials", methods=["GET"])
    @roles_required("CEO", "COUNTRY MANAGER")
    async def get_financials():
        # This should query real metrics from the DB
        return jsonify({"revenue": "UGX 14,500,000", "scope": "Global"})

    # Optional: add more routes here

# Entry point
if __name__ == "__main__":
    app = create_app()
    # Attach a real async DB client if you have one, e.g.:
    # app.db = YourAsyncDBClient(...)
    app.run(host="0.0.0.0", port=5000, debug=False)
