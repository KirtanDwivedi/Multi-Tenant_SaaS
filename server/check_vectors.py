from vector_store import get_knowledge_collection
import os

CHROMA_PATH = os.path.join("data", "chroma_db")
COLLECTION_NAME = "tenant_knowledge"

coll, _ = get_knowledge_collection(CHROMA_PATH, COLLECTION_NAME)
# Replace your line 8 with this:
try:
    # LangChain stores the native Chroma client inside '_collection'
    print("Number of stored vectors:", coll._collection.count())
except AttributeError:
    print("Still hitting Fallback. The database connection object itself failed to initialize.")
