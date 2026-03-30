from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.pdf_utils import extract_text_from_pdf
from backend.agent import app_graph
import uvicorn
import os
from typing import Dict, Any, List

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
async def upload_pdf(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
        
    try:
        pdf_texts = []
        for file in files:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            pdf_bytes = await file.read()
            text = extract_text_from_pdf(pdf_bytes)
            pdf_texts.append(text)
        
        # We start the graph
        initial_state = {
            "pdf_texts": pdf_texts, 
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
            "synthesis": result.get("synthesis", "")
        }
    except Exception as e:
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
