import pypdf
import io
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import dotenv

dotenv.load_dotenv()

llm = ChatGroq(model="mixtral-8x7b-32768")

class PaperMetadata(BaseModel):
    paper_title: str = Field(description="The title of the paper.")
    paper_author: str = Field(description="The authors of the paper. Use 'Unknown' if not found.")
    paper_date: str = Field(description="The publication or creation date. Use 'Unknown' if not found.")

def extract_paper_metadata(first_page_text: str) -> dict:
    """Uses LLM to intelligently extract metadata from the first page of a PDF."""
    sys_msg = "You are an expert Metadata Extractor. Given the first page text of an academic paper, extract the title, author(s), and date. If a field is completely missing, use 'Unknown'."
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "First page text:\n{first_page_text}")
    ])
    chain = prompt | llm.with_structured_output(PaperMetadata)
    try:
        res = chain.invoke({"first_page_text": first_page_text[:4000]})
        return {
            "paper_id": str(uuid.uuid4()),
            "paper_title": res.paper_title,
            "paper_author": res.paper_author,
            "paper_date": res.paper_date
        }
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {
            "paper_id": str(uuid.uuid4()),
            "paper_title": "Unknown Title",
            "paper_author": "Unknown Author",
            "paper_date": "Unknown Date"
        }

def get_pdf_chunks(pdf_bytes: bytes) -> tuple:
    """Extract and split text from PDF file bytes. Returns (chunks list, first_page_text)."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    raw_text = ""
    first_page_text = ""
    
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            if i == 0:
                first_page_text = page_text
            raw_text += page_text + "\n"
            
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_text(raw_text)
    return chunks, first_page_text
