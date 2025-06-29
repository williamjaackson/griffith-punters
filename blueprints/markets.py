import flask
import math
import uuid
import datetime
from lib.db import markets_collection, users_collection
from .auth import admin_only, get_account, auth_required
from lib.lmsr import (
  cost_function,
  buy_by_spend,
  compute_new_prices,
)
from pymongo import ReturnDocument

blueprint = flask.Blueprint(
  'markets',
  __name__,
  template_folder='templates',
  url_prefix='/markets',
)

@blueprint.route('/<market_id>/trade', methods=['POST'])
@auth_required
def trade(market_id):
  account = get_account() or {}
  uid = account['_id']

  side = flask.request.form.get('side')
  outcome_id = flask.request.form.get('outcome')
  try:
    amount = float(flask.request.form.get('amount', '0'))
  except ValueError:
    amount = 0.0

  if side not in ('buy','sell') or amount <= 0 or not outcome_id:
    flask.flash('Invalid parameters.','danger')
    return flask.redirect(flask.url_for('markets.market', market_id=market_id))

  if side == 'buy':
    # debit up front
    user = users_collection.find_one_and_update(
      {"_id":uid, "balance":{"$gte":amount}},
      {"$inc":{"balance":-amount}},
      return_document=ReturnDocument.AFTER
    )
    if not user:
      flask.flash('Insufficient balance.','danger')
      return flask.redirect(flask.url_for('markets.market', market_id=market_id))

    try:
      result = buy_by_spend(
        market_id=market_id,
        user_id=uid,
        outcome_id=outcome_id,
        spend_amount=amount
      )
    except Exception as e:
      # refund on failure
      users_collection.update_one({"_id":uid}, {"$inc":{"balance":amount}})
      flask.flash(f'Trade failed: {e}','danger')
      return flask.redirect(flask.url_for('markets.market', market_id=market_id))

    actual = result['amountCharged']
    refund = amount - actual
    if refund > 1e-6:
      users_collection.update_one({"_id":uid}, {"$inc":{"balance":refund}})
    flash_msg = f'Bought {result["sharesBought"]:.2f} shares for ${actual:.2f}.'

  else:  # sell
    m = markets_collection.find_one({"_id":market_id})
    if not m:
      flask.flash('Market not found.','danger')
      return flask.redirect(flask.url_for('markets.market', market_id=market_id))

    b = m['liquidityParameter']
    # compute user's current holdings of this outcome
    held = sum(
      o['delta']
      for o in m.get('orders',[])
      if o['userId']==uid and o['outcomeId']==outcome_id
    )
    if amount > held:
      flask.flash('Not enough shares to sell.','danger')
      return flask.redirect(flask.url_for('markets.market', market_id=market_id))

    old_cost = cost_function(m['outcomes'], b)
    new_q = m['outcomes'].copy()
    new_q[outcome_id] -= amount
    new_cost = cost_function(new_q, b)
    refund = old_cost - new_cost

    users_collection.update_one({"_id":uid}, {"$inc":{"balance":refund}})
    order = {
      "orderId": str(uuid.uuid4()),
      "userId": uid,
      "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
      "outcomeId": outcome_id,
      "delta": -amount,
      "cost": -refund,
    }
    markets_collection.update_one(
      {"_id":market_id},
      {
        "$inc": {f"outcomes.{outcome_id}": -amount},
        "$push": {"orders": order},
      }
    )
    flash_msg = f'Sold {amount:.2f} shares for ${refund:.2f}.'

  flask.flash(flash_msg,'success')
  return flask.redirect(flask.url_for('markets.market', market_id=market_id))


@blueprint.route('/')
def markets():
    # Open markets: either no status field or status != 'resolved'
    open_markets = list(markets_collection.find({
        "$or": [
            {"status": {"$exists": False}},
            {"status": {"$ne": "resolved"}}
        ]
    }))
    # Resolved markets
    resolved_markets = list(markets_collection.find({
        "status": "resolved"
    }))

    # decorate each with topOutcome / topProbability
    def decorate(markets):
        for m in markets:
            prices = compute_new_prices(m['outcomes'], m['liquidityParameter'])
            top_outcome, top_prob = max(prices.items(), key=lambda kv: kv[1])
            m['topOutcome'] = top_outcome
            m['topProbability'] = top_prob
    decorate(open_markets)
    decorate(resolved_markets)

    return flask.render_template(
        'pages/markets/markets.html',
        open_markets=open_markets,
        resolved_markets=resolved_markets
    )

@blueprint.route('/<market_id>')
def market(market_id):
    m = markets_collection.find_one({"_id": market_id})
    if not m: return flask.abort(404)

    b = m['liquidityParameter']
    # current prices
    prices = compute_new_prices(m['outcomes'], b)
    # max loss
    num_outcomes = len(m['outcomes'])
    max_loss = b * math.log(num_outcomes)

    # build price history by replaying orders
    running = {o: 0.0 for o in m['outcomes'].keys()}
    orders = sorted(m.get('orders', []), key=lambda o: o['timestamp'])
    price_history = []
    for o in orders:
        running[o['outcomeId']] += o['delta']
        ph = compute_new_prices(running, b)
        price_history.append({
            't': o['timestamp'],
            'prices': ph
        })

    # user holdings
    account = get_account() or {}
    uid = account.get('_id')
    holdings = {o: 0.0 for o in m['outcomes'].keys()}
    for o in m.get('orders', []):
        if o['userId'] == uid:
            holdings[o['outcomeId']] += o['delta']

    return flask.render_template(
        'pages/markets/market.html',
        market=m,
        prices=prices,
        max_loss=max_loss,
        holdings=holdings,
        price_history=price_history,
    )

@blueprint.route('/<market_id>/delete')
@admin_only
def delete_market(market_id):
  result = markets_collection.delete_one({"_id":market_id})
  if result.deleted_count:
    flask.flash('Market deleted successfully.','success')
  else:
    flask.flash('Market not found or could not be deleted.','danger')
  return flask.redirect(flask.url_for('markets.markets'))

@blueprint.route('/create', methods=['GET','POST'])
@admin_only
def create():
  if flask.request.method == 'POST':
    name = flask.request.form.get('name','').strip()
    desc = flask.request.form.get('description','').strip()
    liquidity = flask.request.form.get('liquidity', '1000')
    labels = [
      lbl.strip() 
      for lbl in flask.request.form.getlist('outcomes')
      if lbl.strip()
    ]
    if not name or not desc:
      flask.flash('Market name and description are required.','danger')
      return flask.redirect(flask.url_for('markets.create'))
    if len(labels) < 2:
      flask.flash('Please enter at least two outcomes.','danger')
      return flask.redirect(flask.url_for('markets.create'))

    outcomes = {lbl: 0.0 for lbl in labels}
    markets_collection.insert_one({
      '_id': str(uuid.uuid4()),
      'title': name,
      'description': desc,
      'created_at': datetime.datetime.utcnow(),
      'liquidityParameter': float(liquidity),
      'outcomes': outcomes,
      'orders': [],
    })
    return flask.redirect(flask.url_for('markets.markets'))

  return flask.render_template('pages/markets/create.html')

@blueprint.route('/<market_id>/resolve', methods=['GET','POST'])
@admin_only
def resolve_market(market_id):
    m = markets_collection.find_one({"_id": market_id})
    if not m:
        flask.flash('Market not found.', 'danger')
        return flask.redirect(flask.url_for('markets.markets'))

    # if already resolved, redirect back
    if m.get('status') == 'resolved':
        flask.flash('Market already resolved.', 'warning')
        return flask.redirect(
            flask.url_for('markets.market', market_id=market_id)
        )

    if flask.request.method == 'POST':
        winner = flask.request.form.get('winning_outcome')
        if winner not in m['outcomes']:
            flask.flash('Invalid outcome selected.', 'danger')
            return flask.redirect(
                flask.url_for('markets.resolve_market', market_id=market_id)
            )

        # compute user payouts: $1 per share held in winner
        # first, compute net holdings per user:
        holdings = {}
        for o in m.get('orders', []):
            uid = o['userId']
            if o['outcomeId'] == winner:
                holdings[uid] = holdings.get(uid, 0.0) + o['delta']

        # credit each user their payout
        for uid, qty in holdings.items():
            if qty > 0:
                users_collection.update_one(
                    {"_id": uid},
                    {"$inc": {"balance": qty}}
                )

        # mark market resolved
        markets_collection.update_one(
            {"_id": market_id},
            {"$set": {
                "status": "resolved",
                "winningOutcome": winner,
                "resolved_at": datetime.datetime.utcnow()
            }}
        )
        flask.flash(f'Market resolved: "{winner}" wins.', 'success')
        return flask.redirect(
            flask.url_for('markets.market', market_id=market_id)
        )

    # GET: render form
    return flask.render_template(
        'pages/markets/resolve.html',
        market=m
    )