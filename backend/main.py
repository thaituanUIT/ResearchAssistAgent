from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.pdf_utils import get_pdf_chunks, extract_paper_metadata
from backend.vector_store import add_paper_to_db
from backend.agent import app_graph
import uvicorn
import os
from typing import Dict, Any, List


class ChatRequest(BaseModel):
    user_prompt: str
    chat_history: List[Dict[str, str]] = []
    working_document: str = ""
    synthesis: str = ""

app = FastAPI(title="ResearchAssist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ResearchAssist API is running"}

@app.post("/upload")
async def upload_pdf(files: List[UploadFile] = File(...), user_prompt: str = Form("")):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
        
    try:
        paper_metadatas = []
        for file in files:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            pdf_bytes = await file.read()
            
            chunks, first_page = get_pdf_chunks(pdf_bytes)
            metadata = extract_paper_metadata(first_page)
            
            # Persist textual chunks directly into Pinecone DB
            add_paper_to_db(chunks, metadata)
            paper_metadatas.append(metadata)
        
        # We start the graph
        initial_state = {
            "paper_metadata": paper_metadatas, 
            "user_prompt": user_prompt,
            "route": "",
            "working_document": "",
            "evaluation": "", 
            "confidence_level": "",
            "retrieved_context": "",
            "synthesis": ""
        }
        result = app_graph.invoke(initial_state)
        
        return {
            "route": result.get("route", ""),
            "confidence_level": result.get("confidence_level", ""),
            "retrieved_context": result.get("retrieved_context", ""),
            "synthesis": result.get("synthesis", ""),
            "working_document": result.get("working_document", "")
        }
    except Exception as e:
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        initial_state = {
            "user_prompt": req.user_prompt,
            "chat_history": req.chat_history,
            "working_document": req.working_document,
            "synthesis": req.synthesis
        }
        result = app_graph.invoke(initial_state)
        return {"chat_response": result.get("chat_response", "")}
    except Exception as e:
        print(f"Error during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
