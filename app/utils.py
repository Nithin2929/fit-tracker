"""Small shared helpers used by the Flask routes and templates."""

import hmac
import secrets
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlsplit

from flask import abort, flash, g, redirect, request, session, url_for


def login_required(view):
    """Redirect anonymous visitors to the login page."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if getattr(g, "user", None) is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def get_csrf_token():
    """Return the session CSRF token, creating it when necessary."""

    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def validate_csrf():
    """Reject a POST whose CSRF token is missing or wrong."""

    expected = session.get("_csrf_token")
    supplied = request.form.get("csrf_token", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        abort(400, description="The form expired. Refresh the page and try again.")


def safe_next_url(target, fallback):
    """Allow only same-site relative redirects after login.

    Rejects absolute URLs, protocol-relative URLs, backslash tricks, and
    embedded control characters so ``?next=`` cannot be used as an open
    redirect.
    """

    if not target:
        return fallback
    target = target.strip()
    if not target.startswith("/") or target.startswith("//"):
        return fallback
    if "\\" in target or any(ord(character) < 32 for character in target):
        return fallback

    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return fallback
    return target


def parse_date(value, field_name, required=True):
    """Parse an HTML date input (YYYY-MM-DD)."""

    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError(f"{field_name} must be a valid date (YYYY-MM-DD).") from error


def parse_datetime(value, field_name, required=True):
    """Parse an HTML datetime-local value (YYYY-MM-DDTHH:MM)."""

    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    for pattern in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    raise ValueError(f"{field_name} must be a valid date and time.")


def parse_int(value, field_name, minimum=None, maximum=None, required=True, default=None):
    """Parse an optional or required whole number with range checks."""

    value = (value or "").strip() if isinstance(value, str) else value
    if value in ("", None):
        if required:
            raise ValueError(f"{field_name} is required.")
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a whole number.") from error
    if minimum is not None and number < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"{field_name} must be at most {maximum}.")
    return number


def parse_decimal(value, field_name, minimum=None, maximum=None, required=False):
    """Parse an optional decimal value with range checks."""

    value = (value or "").strip() if isinstance(value, str) else value
    if value in ("", None):
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a number.") from error
    if minimum is not None and number < Decimal(str(minimum)):
        raise ValueError(f"{field_name} must be at least {minimum}.")
    if maximum is not None and number > Decimal(str(maximum)):
        raise ValueError(f"{field_name} must be at most {maximum}.")
    return number


def parse_choice(value, field_name, choices):
    """Accept only a value from a fixed list."""

    value = (value or "").strip()
    if value not in choices:
        raise ValueError(f"{field_name} must be one of: {', '.join(choices)}.")
    return value


def calculate_bmi(weight_kg, height_cm):
    """Return BMI rounded to one decimal place, or None for bad values."""

    if weight_kg is None or height_cm is None:
        return None
    try:
        weight = float(weight_kg)
        height_metres = float(height_cm) / 100
        if weight <= 0 or height_metres <= 0:
            return None
        return round(weight / (height_metres * height_metres), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def bmi_category(bmi):
    """Return a friendly BMI category."""

    if bmi is None:
        return "Not available"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def display_date(value):
    """Format a date for templates."""

    if not value:
        return "—"
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    return str(value)


def display_number(value, places=1):
    """Format a Decimal/float for templates without trailing noise."""

    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.{places}f}"


def register_template_helpers(app):
    """Register filters and globals used by the Jinja templates."""

    app.jinja_env.filters["display_date"] = display_date
    app.jinja_env.filters["display_number"] = display_number
    app.jinja_env.filters["bmi_category"] = bmi_category
    app.jinja_env.globals["csrf_token"] = get_csrf_token
