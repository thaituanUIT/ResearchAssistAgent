import pypdf
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF file bytes and split it robustly."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    raw_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            raw_text += page_text + "\n"
            
    # Utilize RecursiveCharacterTextSplitter to create robust, coherent chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_text(raw_text)
    
    # Reassemble with structural markers so the LangGraph agent can reliably parse large inputs
    structured_text = ""
    for i, chunk in enumerate(chunks):
        structured_text += f"\n--- Section '{i+1}' ---\n{chunk.strip()}\n"
        
    return structured_text
