import flask
from lib.db import users_collection

blueprint = flask.Blueprint('users', __name__, template_folder='templates', url_prefix='/users')

@blueprint.route('/')
def users():
    return flask.render_template('pages/users/users.html', users=users_collection.find())

@blueprint.route('/<user_id>')
def user(user_id):
    print(f"Fetching user with ID: {user_id}")
    user = users_collection.find_one({
        "_id": user_id
    })
    if not user: return flask.abort(404)

    return flask.render_template('pages/users/user.html', user=user)