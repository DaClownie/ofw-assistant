from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings as SentenceTransformerEmbeddings
from pathlib import Path

VECTOR_DIR = Path("data/chroma_db")
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

def persist_chunks(documents, doc_id):
    vectordb = Chroma(
        collection_name="ofw",
        embedding_function=embedding,
        persist_directory=str(VECTOR_DIR)
    )
    vectordb.add_documents(documents, ids=[f"{doc_id}_{i}" for i in range(len(documents))])
    vectordb.persist()

def search_similar(query, k=5):
    vectordb = Chroma(
        collection_name="ofw",
        embedding_function=embedding,
        persist_directory=str(VECTOR_DIR)
    )
    results = vectordb.similarity_search(query, k=k)
    return results

def get_chunks_by_file(filepath: str) -> list[str]:
    db = Chroma(
        collection_name="ofw",
        embedding_function=embedding,
        persist_directory=str(VECTOR_DIR)
    )

    # Use a wildcard query to get a broad result set
    results = db.similarity_search(query="*", k=100)

    # Normalize the path to ensure consistency
    filepath = str(Path(filepath).resolve())

    matching = [
        r for r in results
        if filepath in str(Path(r.metadata.get("source", "")).resolve())
    ]

    print(f"🔎 get_chunks_by_file: {len(matching)} matching chunks found for {filepath}")
    return matching
