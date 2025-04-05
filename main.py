from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from utils import categorize_posts, summarize_pain_points
from get_data import get_posts_from_subreddits, find_relevant_subreddits

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
    subreddit_icon: Optional[str] = None
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


# Add new Pydantic models for the subreddit search endpoint
class SubredditSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20

class SubredditInfo(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    subscribers: int
    url: str
    subreddit_icon: Optional[str] = None

class SubredditSearchResponse(BaseModel):
    subreddits: List[SubredditInfo]
    count: int

@app.post("/search-subreddits", response_model=SubredditSearchResponse)
async def search_subreddits(request: SubredditSearchRequest):
    """
    Search for relevant subreddits based on a keyword or name
    """
    try:
        # Get subreddits matching the query
        subreddits = find_relevant_subreddits(
            query=request.query,
            limit=request.limit
        )
        
        return SubredditSearchResponse(
            subreddits=subreddits,
            count=len(subreddits)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

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