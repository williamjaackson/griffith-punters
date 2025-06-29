import os
import flask

import blueprints.auth as auth
import blueprints.markets as markets
import blueprints.users as users

from lib.db import markets_collection

app = flask.Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "")
app.context_processor(lambda: {"account": auth.get_account()})

def load_blueprint(blueprint):
    blueprint.context_processor(lambda: {"account": auth.get_account()})
    app.register_blueprint(blueprint)

load_blueprint(auth.blueprint)
load_blueprint(markets.blueprint)
load_blueprint(users.blueprint)

@app.route('/')
def index():
    return flask.redirect(flask.url_for('markets.markets'))

@app.route('/about')
def about():
    return flask.render_template('pages/about.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')