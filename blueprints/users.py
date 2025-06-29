import flask
from lib.db import users_collection
from bson.objectid import ObjectId

blueprint = flask.Blueprint('users', __name__, template_folder='templates', url_prefix='/users')

@blueprint.route('/')
def users():
    return flask.render_template('pages/users/users.html', users=users_collection.find())

@blueprint.route('/<user>')
def user(user):
    print(f"Fetching user with ID: {user}")
    user = users_collection.find_one({
        "_id": ObjectId(user)
    })
    if not user: return flask.abort(404)

    return flask.render_template('pages/users/user.html', user=user)