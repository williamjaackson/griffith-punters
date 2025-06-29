import lib.db as db

db.markets_collection.delete_many({})
# db.markets_collection.insert_one(
# 	{
#         "title": "GPA > 6.0",
#         "description": "6.0 or above for Trimester 2, 2025?",
#         "status": "open",
#         "liquidityParameter": 1000,
#         "outcomes": {
#             "YES": 0, 
#             "NO":  0
#         },
#         "orders": []
#     }
# )