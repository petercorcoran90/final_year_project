import re
from pymongo import MongoClient

# 1) Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]


def remove_duplicate_cards():
    """
    Loops over all collections named 'round_X' (where X is a number),
    finds docs with a 'cards' array, and removes duplicate card objects.
    Updates each doc in-place in MongoDB.
    """
    # List all collections in the DB
    all_collections = db.list_collection_names()

    # Process only collections like 'round_1', 'round_2', etc.
    for col_name in all_collections:
        if re.match(r"^round_\d+$", col_name):
            print(f"\nProcessing collection: {col_name}")
            round_col = db[col_name]

            # Find documents that have a non-empty 'cards' array
            docs_with_cards = round_col.find(
                {"cards": {"$exists": True, "$ne": []}})

            # Loop over each doc and remove duplicates
            for doc in docs_with_cards:
                doc_id = doc["_id"]
                cards = doc["cards"]

                # Deduplicate the 'cards' array
                deduplicated_cards = []
                seen = set()

                for card in cards:
                    # Example approach: build a tuple using some combination of fields
                    # If you have a unique 'incidentId', use that; otherwise, combine relevant fields
                    # e.g. 'incidentId' or ('time', 'reason', 'incidentClass', 'incidentType')

                    # Option A: If each card has 'incidentId', do:
                    # key = card.get("incidentId")

                    # Option B: If no 'incidentId', but time, reason, etc. exist:
                    key = (
                        card.get("time"),
                        card.get("reason"),
                        card.get("incidentClass"),
                        card.get("incidentType")
                    )

                    if key not in seen:
                        seen.add(key)
                        deduplicated_cards.append(card)

                # If anything changed, update in MongoDB
                if len(deduplicated_cards) != len(cards):
                    round_col.update_one(
                        {"_id": doc_id},
                        {"$set": {"cards": deduplicated_cards}}
                    )
                    print(f"  - Removed duplicates in doc _id={doc_id}, old={
                          len(cards)}, new={len(deduplicated_cards)}")
                else:
                    print(f"  - No duplicates found in doc _id={doc_id}")


def main():
    remove_duplicate_cards()


if __name__ == "__main__":
    main()
