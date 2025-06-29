import flask
import datetime
from lib.db import markets_collection
from .auth import admin_only

blueprint = flask.Blueprint('markets', __name__, template_folder='templates', url_prefix='/markets')

@blueprint.route('/')
def markets():
    return flask.render_template('pages/markets/markets.html', markets=markets_collection.find())

@blueprint.route('/<market>')
def detail(market):
    market_data = next((m for m in markets_collection.find() if str(m['_id']) == market), None)
    if not market_data: return flask.abort(404)
    return flask.render_template('pages/markets/market.html', market=market_data)

@blueprint.route('/create', methods=['GET', 'POST'])
@admin_only
def create():
    if flask.request.method == 'POST':
        market_name = flask.request.form.get('name', '')
        market_description = flask.request.form.get('description', '')
        if not market_name or not market_description:
            flask.flash('Market name and description are required.', 'danger')
            return flask.redirect(flask.url_for('markets.create'))
        markets_collection.insert_one({
            'name': market_name,
            'description': market_description,
            'created_at': datetime.datetime.utcnow()
        })        
        return flask.redirect(flask.url_for('markets.markets'))
    
    return flask.render_template('pages/markets/create.html')