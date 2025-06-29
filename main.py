import os
import flask
import blueprints.auth as auth

app = flask.Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "")

def load_blueprint(blueprint):
    # add a context processor to inject the current user into the template context
    @blueprint.context_processor
    def inject_user():
        """Inject the current user into the template context."""
        return {"user": auth.get_current_user()}
    
    app.register_blueprint(blueprint)

load_blueprint(auth.blueprint)

MARKETS = [
    {
        "id": 1,
        "name": "will William's GPA be above 6.0?",
        "description": "will William Jackson achieve a GPA of HIGHER than 6.0 for Trimester 2.",
        "status": "Open",
        "start_time": "2025-10-01 10:00:00",
        "end_time": "2025-10-01 12:00:00"
    },
]

@app.context_processor
def inject_user():
    """Inject the current user into the template context."""
    return {"user": auth.get_current_user()}

@app.route('/')
def index():
    return flask.redirect(flask.url_for('markets'))

@app.route('/markets')
# @auth.jwt_required
def markets():
    return flask.render_template('markets.html', markets=MARKETS)

@app.route('/markets/<market>')
def market_detail(market):
    market_data = next((m for m in MARKETS if str(m['id']) == market), None)
    if not market_data: return flask.abort(404)
    return flask.render_template('market_detail.html', market=market_data)

# def register_blueprints():
#     # loop through all files in the blueprints directory
#     import os
    
#     for filename in os.listdir('blueprints'):
#         if filename.endswith('.py'):
#             module_name = filename[:-3]
#             module = __import__(f'blueprints.{module_name}', fromlist=['blueprint'])
#             app.register_blueprint(module.blueprint)

if __name__ == "__main__":
    # register_blueprints()
    app.run(debug=True)