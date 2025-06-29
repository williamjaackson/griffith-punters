import flask
import jwt
import datetime
import os
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

# Path to the JSON database
DB_PATH = os.path.join(os.path.dirname(__file__), "../data/users.json")

blueprint = flask.Blueprint("auth", __name__)

users = [
    {        
        "username": "admin",
        "password": generate_password_hash("admin123"),
    }
]

@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        username = flask.request.form.get("username", "")
        password = flask.request.form.get("password", "")

        # Find the user in the database
        user = next((u for u in users if u["username"] == username), None)

        if user and check_password_hash(user["password"], password):
            # Generate JWT token
            token = jwt.encode(
                {
                    "username": username,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                },
                JWT_SECRET_KEY,
                algorithm="HS256",
            )

            # Set the JWT token in a cookie
            response = flask.make_response(flask.redirect(flask.url_for("markets")))
            response.set_cookie("jwt", token, httponly=True, samesite="Strict")
            return response
        else:
            flask.flash("Invalid username or password", "danger")

    return flask.render_template("pages/auth/login.html")

@blueprint.route("/logout")
def logout():
    # Clear the JWT token by setting an expired cookie
    response = flask.make_response(flask.redirect(flask.url_for("markets")))
    response.set_cookie("jwt", "", expires=0, httponly=True, samesite="Strict")
    return response

def jwt_required(func):
    """Decorator to protect routes with JWT authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = flask.request.cookies.get("jwt")
        if not token:
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

def get_current_user():
    """Retrieve the current user based on the JWT token in cookies."""
    token = flask.request.cookies.get("jwt")
    if not token:
        return None
    try:
        # Decode the JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username = payload.get("username")

        # Load users from the JSON database
        user = next((u for u in users if u["username"] == username), None)
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None