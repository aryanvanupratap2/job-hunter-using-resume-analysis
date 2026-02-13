from pydantic import BaseModel, Field, AliasChoices
from typing import List

class JobRecommendation(BaseModel):
    # Flexible mapping for AI-generated keys
    title: str = Field(validation_alias=AliasChoices("title", "role", "job_title"))
    company: str = Field(validation_alias=AliasChoices("company", "organization"), default="Direct Hire")
    location: str = Field(default="Remote / India")
    link: str = Field(validation_alias=AliasChoices("link", "url", "job_url"))
  
class ResumeAnalysis(BaseModel):
    resume_score: int
    job_recommendations: List[JobRecommendation]
    improvement_points: List[str]

class JobResponse(BaseModel):
    status: str
    filename: str
    analysis: ResumeAnalysis