import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
import dotenv

dotenv.load_dotenv()

# Using HuggingFace MiniLM for 384-dimensional embeddings (compact and extremely fast locally)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY", "dummy-key-replace-me"))
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "researchassist-index")

def get_vector_store():
    try:
        # Check if index exists, and create if it doesn't
        if INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=INDEX_NAME,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
    except Exception as e:
        print(f"Warning during Pinecone init: {e}")
        
    return PineconeVectorStore(index=pc.Index(INDEX_NAME), embedding=embeddings)

def add_paper_to_db(chunks: list, metadata: dict):
    """Embeds textual chunks and inserts them into Pinecone along with document metadata."""
    if not chunks:
        return
    vectorstore = get_vector_store()
    
    # Associate identical metadata down to every individual chunk
    metadatas = [metadata for _ in chunks]
    vectorstore.add_texts(texts=chunks, metadatas=metadatas)

def add_chat_to_db(message: str, user_id: str, session_id: str, role: str):
    """Embeds a chat message and inserts it into Pinecone with memory metadata."""
    if not message or not message.strip():
        return
    try:
        vectorstore = get_vector_store()
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "type": "chat_memory"
        }
        vectorstore.add_texts(texts=[message], metadatas=[metadata])
    except Exception as e:
        print(f"Error indexing chat memory: {e}")

def retrieve_relevant_context(query: str, k: int = 5, filter_dict: dict = None) -> str:
    """Retrieves relevant chunks from the vector store based on query. Optionally filter by metadata."""
    try:
        vectorstore = get_vector_store()
        results = vectorstore.similarity_search(query, k=k, filter=filter_dict)
        context = ""
        for res in results:
            title = res.metadata.get("paper_title", "Unknown")
            context += f"--- Document Section (from {title}) ---\n{res.page_content}\n\n"
        return context
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return "No relevant context found due to vector DB error."
