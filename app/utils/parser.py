from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

def load_and_split_pdf(path):
    loader = PyPDFLoader(path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(pages)

    # Add source metadata to each chunk
    for i in range(len(chunks)):
        chunks[i].metadata["source"] = path

    return chunks
