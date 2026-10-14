"""Prints how many documents each Firestore collection has.

Run from the project root:  python -m scripts.check_firebase_connection
"""

from ecommerce.collection_names import ALL_COLLECTIONS
from ecommerce.firebase_connection import get_firestore


def count_documents(collection_name: str) -> int:
    """Return the number of documents in one collection."""
    # TODO: use an aggregation count query: get_firestore().collection(name).count().get()
    ...


def main() -> None:
    """Print one line per collection with its document count."""
    # TODO: for name in ALL_COLLECTIONS: print(f"{name}: {count_documents(name)}")
    # TODO: printing is fine here — this script is not the MCP server
    ...


if __name__ == "__main__":
    main()
