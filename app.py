from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Dict
from uuid import uuid4, UUID

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    text: str
    score: float
    options: List[str] = Field(min_items=2)
    correct: List[str] = Field(min_items=1)
    use_knowledge_base: bool

    @validator('correct', each_item=False)
    def correct_options_must_be_in_options(cls, correct, values):
        options = values.get('options', [])
        if not all(option in options for option in correct):
            missing_options = [option for option in correct if option not in options]
            raise ValueError(f"Correct options {missing_options} not present in the provided options list.")
        return correct

class ScorecardIn(BaseModel):  # Used for creating a new scorecard (POST request body)
    title: str
    questions: List[Question]

    @validator('questions', each_item=False)
    def check_scores_sum_to_100(cls, questions):
        total_score = sum(question.score for question in questions)
        if total_score != 100:
            raise ValueError('The sum of scores for all questions must add up to 100')
        return questions

class Scorecard(BaseModel):  # Used for output, including the ID
    id: UUID = Field(default_factory=uuid4)
    title: str
    questions: List[Question]

# In-memory database simulation
db: Dict[UUID, Scorecard] = {}

@app.post("/api/scorecards/", status_code=201, response_model=Scorecard)
async def create_scorecard(scorecard_in: ScorecardIn):
    scorecard = Scorecard(**scorecard_in.dict())
    db[scorecard.id] = scorecard
    return scorecard

@app.get("/api/scorecards/")
async def get_scorecards():
    return list(db.values())

@app.get("/api/scorecards/{id}/")
async def get_scorecard(id: UUID):
    if id not in db:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    return db[id]

@app.put("/api/scorecards/{id}/", response_model=Scorecard)
async def update_scorecard(id: UUID, scorecard_in: ScorecardIn):
    if id not in db:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    scorecard = Scorecard(**scorecard_in.dict(), id=id)
    db[id] = scorecard
    return scorecard

@app.delete("/api/scorecards/{id}/")
async def delete_scorecard(id: UUID):
    if id not in db:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    del db[id]
    return {"message": "Scorecard deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
