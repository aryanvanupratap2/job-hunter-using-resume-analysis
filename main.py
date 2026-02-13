from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pypdf
import io
import json
import uvicorn
from schemas import JobResponse
from graph import resume_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze", response_model=JobResponse)
async def analyze(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # Extract Text
        pdf_bytes = await file.read()
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = " ".join([page.extract_text() for page in reader.pages])

        # Run Agentic Workflow
        final_state = resume_agent.invoke([text])
        
        # Extract Parts
        real_links = final_state[3] # Tavily data
        ai_data = json.loads(final_state[1]) # Gemini data

        # Map real links to recommendation list
        job_list = []
        for item in real_links:
            job_list.append({
                "title": item.get("title", "Job Opening"),
                "company": "Company in Link",
                "link": item.get("url"),
                "location": "Remote / Hybrid"
            })

        return {
            "status": "success",
            "filename": file.filename,
            "analysis": {
                "resume_score": ai_data["resume_score"],
                "improvement_points": ai_data["improvement_points"],
                "job_recommendations": job_list
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)