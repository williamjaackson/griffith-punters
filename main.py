import os
import flask
import blueprints.auth as auth
import blueprints.markets as markets

from lib.db import markets_collection

app = flask.Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "")
app.context_processor(lambda: {"user": auth.get_user()})

def load_blueprint(blueprint):
    blueprint.context_processor(lambda: {"user": auth.get_user()})
    app.register_blueprint(blueprint)

load_blueprint(auth.blueprint)
load_blueprint(markets.blueprint)

@app.route('/')
def index():
    return flask.redirect(flask.url_for('markets.markets'))

if __name__ == "__main__":
    app.run(debug=True)