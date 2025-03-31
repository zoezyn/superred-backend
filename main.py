from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from utils import categorize_posts, summarize_pain_points
from get_data import get_posts_from_subreddits

app = FastAPI(
    title="Reddit Pain Points Analyzer",
    description="API for analyzing pain points from Reddit posts"
)

# Pydantic models for request/response
class RedditAnalysisRequest(BaseModel):
    subreddits: List[str]
    search_limit: Optional[int] = 30

class RedditPost(BaseModel):
    subreddit: str
    title: str
    content: str
    url: str
    score: int
    num_comments: int

class Category(BaseModel):
    category: str
    pain_points: str
    posts: List[RedditPost]

class RedditAnalysisResponse(BaseModel):
    categories: dict
    total_posts: int

@app.post("/analyze", response_model=RedditAnalysisResponse)
async def analyze_subreddits(request: RedditAnalysisRequest):
    """
    Analyze pain points from specified subreddits
    """
    try:
        # Get posts
        results = get_posts_from_subreddits(
            subreddits=request.subreddits,
            search_limit=request.search_limit
        )
        
        # Categorize and summarize
        categorized_posts = categorize_posts(results)
        categories = summarize_pain_points(categorized_posts)
        
        return RedditAnalysisResponse(
            categories=categories,
            total_posts=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}