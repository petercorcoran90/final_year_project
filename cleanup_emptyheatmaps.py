import re
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']


def clean_up_round_collections_and_drop_empty():
    """
    1) For each 'round_X' collection, delete "empty" docs:
         - only _id + match_id (2 fields total)
         - only _id + match_id + empty heatmap (3 fields total)
    2) If a round_X collection ends up with 0 docs, drop it entirely.
    """
    # List all collections in the DB
    all_collections = db.list_collection_names()

    # Process only collections like 'round_1', 'round_2', etc.
    for collection_name in all_collections:
        if re.match(r"^round_\d+$", collection_name):
            round_collection = db[collection_name]
            print(f"\nProcessing collection: {collection_name}")

            # Build a single query to catch BOTH scenarios using "$or":
            #  (A) 2 fields: _id + match_id
            #  (B) 3 fields: _id + match_id + empty heatmap

            query = {
                "$or": [
                    # (A) doc has exactly 2 fields => _id + match_id
                    {
                        "$and": [
                            {"_id": {"$exists": True}},
                            {"match_id": {"$exists": True}},
                            {
                                "$expr": {
                                    "$eq": [
                                        {"$size": {"$objectToArray": "$$ROOT"}},
                                        2
                                    ]
                                }
                            }
                        ]
                    },
                    # (B) doc has exactly 3 fields => _id + match_id + empty heatmap
                    {
                        "$and": [
                            {"_id": {"$exists": True}},
                            {"match_id": {"$exists": True}},
                            {
                                "$expr": {
                                    "$eq": [
                                        {"$size": {"$objectToArray": "$$ROOT"}},
                                        3
                                    ]
                                }
                            },
                            {"heatmap": {"$size": 0}}
                        ]
                    }
                ]
            }

            # Delete those "empty" docs
            result = round_collection.delete_many(query)
            print(f"  Deleted {result.deleted_count} documents from {
                  collection_name}")

            # Check if the collection is now empty; if so, drop it
            remaining_docs = round_collection.count_documents({})
            if remaining_docs == 0:
                db.drop_collection(collection_name)
                print(f"  Collection {
                      collection_name} was empty and has been dropped.")
            else:
                print(f"  Collection {collection_name} still has {
                      remaining_docs} documents left.")


def main():
    clean_up_round_collections_and_drop_empty()


if __name__ == "__main__":
    main()
