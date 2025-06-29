import math
import uuid
from datetime import datetime
from .db import markets_collection

def cost_function(outcome_shares, liquidity):
  total = sum(math.exp(q / liquidity) for q in outcome_shares.values())
  return liquidity * math.log(total)

def compute_delta_shares(
  outcome_shares, liquidity, outcome_id, spend_amount
):
  Z = sum(math.exp(q / liquidity) for q in outcome_shares.values())
  exp_qi = math.exp(outcome_shares[outcome_id] / liquidity)
  numerator = Z * math.exp(spend_amount / liquidity) - (Z - exp_qi)
  if numerator <= 0:
    raise ValueError("Spend too small; no positive solution for shares.")
  return liquidity * math.log(numerator / exp_qi)

def compute_new_prices(outcome_shares, liquidity):
  exps = {o: math.exp(q / liquidity) for o, q in outcome_shares.items()}
  total = sum(exps.values())
  return {o: v/total for o, v in exps.items()}

def buy_by_spend(market_id, user_id, outcome_id, spend_amount):
  market = markets_collection.find_one(
    {"_id":market_id},
    {"liquidityParameter":1, "outcomes":1}
  )
  if not market:
    raise LookupError("Market not found")
  b = market["liquidityParameter"]
  curr = market["outcomes"]

  delta = compute_delta_shares(curr, b, outcome_id, spend_amount)

  old_cost = cost_function(curr, b)
  new_outcomes = curr.copy()
  new_outcomes[outcome_id] += delta
  new_cost = cost_function(new_outcomes, b)
  actual_charge = new_cost - old_cost

  order = {
    "orderId": str(uuid.uuid4()),
    "userId": user_id,
    "timestamp": datetime.utcnow().isoformat()+"Z",
    "outcomeId": outcome_id,
    "delta": delta,
    "cost": actual_charge,
  }
  upd = markets_collection.update_one(
    {"_id":market_id},
    {
      "$inc": {f"outcomes.{outcome_id}": delta},
      "$push": {"orders": order}
    }
  )
  if upd.modified_count != 1:
    raise RuntimeError("Failed to update market document")

  new_prices = compute_new_prices(new_outcomes, b)
  return {
    "sharesBought": delta,
    "amountCharged": actual_charge,
    "newPrices": new_prices
  }