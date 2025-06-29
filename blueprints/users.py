import flask
from lib.db import users_collection, markets_collection
from lib.lmsr import compute_new_prices
from collections import defaultdict

blueprint = flask.Blueprint('users', __name__, template_folder='templates', url_prefix='/users')

@blueprint.route('/')
def users():
    # Get all users and markets
    all_users = list(users_collection.find())
    all_markets = list(markets_collection.find({}))
    
    # Calculate enhanced statistics for each user
    users_with_stats = []
    
    for user in all_users:
        user_id = user['_id']
        
        # Initialize user stats
        user_stats = {
            '_id': user['_id'],
            'username': user['username'],
            'balance': user.get('balance', 0.0),
            'portfolio_value': 0.0,
            'total_value': 0.0,
            'trading_volume': 0.0,
            'total_trades': 0,
            'active_markets': 0
        }
        
        # Track user's holdings across all markets
        user_holdings = defaultdict(lambda: defaultdict(float))
        active_markets_set = set()
        
        # Process each market for this user
        for market in all_markets:
            market_id = market['_id']
            market_orders = market.get('orders', [])
            user_orders = [order for order in market_orders if order.get('userId') == user_id]
            
            if user_orders:
                active_markets_set.add(market_id)
                
                # Calculate holdings and trading stats for this market
                market_holdings = defaultdict(float)
                
                for order in user_orders:
                    # Update holdings
                    outcome = order['outcomeId']
                    shares = order['delta']
                    cost = abs(order['cost'])
                    
                    market_holdings[outcome] += shares
                    user_stats['trading_volume'] += cost
                    user_stats['total_trades'] += 1
                
                # Store non-zero holdings
                for outcome, shares in market_holdings.items():
                    if shares != 0:
                        user_holdings[market_id][outcome] = shares
                
                # Calculate portfolio value for this market
                if any(shares > 0 for shares in market_holdings.values()):
                    # Calculate current prices for this market
                    b = market['liquidityParameter']
                    current_prices = compute_new_prices(market['outcomes'], b)
                    
                    # Add value of positive holdings in this market
                    for outcome, shares in market_holdings.items():
                        if shares > 0:
                            user_stats['portfolio_value'] += shares * current_prices.get(outcome, 0)
        
        # Set active markets count
        user_stats['active_markets'] = len(active_markets_set)
        
        # Calculate total value (cash + portfolio)
        user_stats['total_value'] = user_stats['balance'] + user_stats['portfolio_value']
        
        users_with_stats.append(user_stats)
    
    return flask.render_template('pages/users/users.html', users_with_stats=users_with_stats)

@blueprint.route('/<user_id>')
def user(user_id):
    print(f"Fetching user with ID: {user_id}")
    user = users_collection.find_one({
        "_id": user_id
    })
    if not user: 
        return flask.abort(404)

    # Fetch all markets to find user's trading activity
    all_markets = list(markets_collection.find({}))
    
    # Collect user's trades from all markets
    user_trades = []
    holdings = {}
    active_markets = set()
    total_volume = 0.0
    
    for market in all_markets:
        market_orders = market.get('orders', [])
        user_orders = [order for order in market_orders if order.get('userId') == user_id]
        
        if user_orders:
            active_markets.add(market['_id'])
            
            # Calculate holdings for this market
            market_holdings = {outcome: 0.0 for outcome in market['outcomes'].keys()}
            
            for order in user_orders:
                # Add to user trades list
                trade_data = {
                    'market_id': market['_id'],
                    'market_title': market.get('title', 'Unknown Market'),
                    'outcomeId': order['outcomeId'],
                    'delta': order['delta'],
                    'cost': order['cost'],
                    'timestamp': order['timestamp']
                }
                user_trades.append(trade_data)
                
                # Update holdings
                market_holdings[order['outcomeId']] += order['delta']
                
                # Add to total volume
                total_volume += abs(order['cost'])
            
            # Only include markets where user has non-zero holdings
            non_zero_holdings = {k: v for k, v in market_holdings.items() if v != 0}
            if non_zero_holdings:
                holdings[market['_id']] = {
                    'market_title': market.get('title', 'Unknown Market'),
                    'outcomes': market_holdings
                }
    
    # Sort trades by timestamp (most recent first)
    user_trades.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate portfolio value
    portfolio_value = 0.0
    for market in all_markets:
        if market['_id'] in holdings:
            # Calculate current prices for this market
            b = market['liquidityParameter']
            current_prices = compute_new_prices(market['outcomes'], b)
            
            # Add value of holdings in this market
            for outcome, shares in holdings[market['_id']]['outcomes'].items():
                if shares > 0:  # Only count positive holdings
                    portfolio_value += shares * current_prices.get(outcome, 0)
    
    return flask.render_template(
        'pages/users/user.html', 
        user=user,
        user_trades=user_trades,
        holdings=holdings,
        active_markets=list(active_markets),
        total_volume=total_volume,
        portfolio_value=portfolio_value
    )