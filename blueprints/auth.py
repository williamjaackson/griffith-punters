import flask
import jwt
import datetime
import os
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from lib.db import users_collection

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

blueprint = flask.Blueprint("auth", __name__)

##### ROUTES #####

@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        username = flask.request.form.get("username", "")
        password = flask.request.form.get("password", "")

        # Find the user in the MongoDB collection
        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user["password"], password):
            # Generate JWT token
            token = jwt.encode(
                {
                    "_id": user["_id"],
                    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
                },
                JWT_SECRET_KEY,
                algorithm="HS256",
            )

            # Set the JWT token in a cookie
            response = flask.make_response(flask.redirect(flask.url_for("markets.markets")))
            response.set_cookie("jwt", token, httponly=True, samesite="Strict")
            return response
        else:
            flask.flash("Invalid username or password", "danger")

    return flask.render_template("pages/auth/login.html")

@blueprint.route("/logout")
def logout():
    # Clear the JWT token by setting an expired cookie
    response = flask.make_response(flask.redirect(flask.url_for("markets.markets")))
    response.set_cookie("jwt", "", expires=0, httponly=True, samesite="Strict")
    return response

@blueprint.route("/register", methods=["GET", "POST"])
def register():
    if flask.request.method == "POST":
        username = flask.request.form.get("username", "").strip()
        password = flask.request.form.get("password", "").strip()
        confirm_password = flask.request.form.get("confirm_password", "").strip()

        if not username or not password or not confirm_password:
            flask.flash("All fields are required.", "danger")
            return flask.redirect(flask.url_for("auth.register"))

        if password != confirm_password:
            flask.flash("Passwords do not match.", "danger")
            return flask.redirect(flask.url_for("auth.register"))

        # Check if the username already exists
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            flask.flash("Username already exists. Please choose a different one.", "danger")
            return flask.redirect(flask.url_for("auth.register"))

        # Create a new user
        hashed_password = generate_password_hash(password)
        new_user = {
            "_id": str(uuid.uuid4()),
            "username": username,
            "password": hashed_password,
            "balance": 1000.0,  # Default balance
            "admin": False,
        }
        users_collection.insert_one(new_user)

        flask.flash("Registration successful! You can now log in.", "success")
        return flask.redirect(flask.url_for("auth.login"))

    return flask.render_template("pages/auth/register.html")

##### DECORATORS #####

def auth_required(func):
    """Decorator to protect routes with JWT authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = flask.request.cookies.get("jwt")
        if not token:
            flask.flash("You must be logged in to access this page.", "danger")
            return flask.redirect(flask.url_for("auth.login"))
        try:
            jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            flask.flash("Session expired. Please log in again.", "danger")
            return flask.redirect(flask.url_for("auth.login"))
        except jwt.InvalidTokenError:
            flask.flash("Invalid token. Please log in again.", "danger")
            return flask.redirect(flask.url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper

def admin_only(func):
    """Decorator to restrict access to admin users."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_account()
        if not user or not user.get("admin", False):
            flask.flash("You do not have permission to access this page.", "danger")
            return flask.redirect(flask.url_for("markets.markets"))
        return func(*args, **kwargs)
    return wrapper

##### HELPER FUNCTIONS #####

def get_account():
    """Retrieve the current user based on the JWT token in cookies."""
    token = flask.request.cookies.get("jwt")
    if not token:
        return None
    try:
        # Decode the JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("_id")

        # Load user from MongoDB
        user = users_collection.find_one({"_id": user_id})
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None