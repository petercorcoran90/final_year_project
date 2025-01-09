from pymongo import MongoClient

# Connect to MongoDB (adjust with your connection settings)
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']  # Change to your database name


def print_unique_attributes():
    """Print a single list of unique attribute names from all round collections."""
    unique_keys = set()  # Set to hold unique keys

    # Loop through round collections (adjust the range as needed)
    for round_number in range(1, 39):  # Assuming there are 38 rounds
        # Collection names format: round_1, round_2, ...
        round_collection = db[f'round_{round_number}']

        for document in round_collection.find():  # Iterate through documents in the collection
            unique_keys.update(document.keys())  # Add document keys to the set

    # Print the unique attributes as a single list
    print("Unique attributes across all rounds:")
    for key in sorted(unique_keys):  # Sort the keys for easier reading
        print(f"- {key}")


# Run the function
if __name__ == "__main__":
    print_unique_attributes()
