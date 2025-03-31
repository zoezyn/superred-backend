# Reddit Pain Points API

A simple backend API system for analyzing and categorizing pain points from Reddit posts.

## Features

- Fetch posts from multiple subreddits with custom search queries
- Categorize posts into groups based on semantic similarity
- Summarize pain points from each category using LLMs
- Simple FastAPI endpoints with automatic documentation

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd superred
```

2. Create and configure environment variables:
```bash
cp .env.example .env
# Edit .env file with your Reddit API credentials
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the API server:
```bash
python app.py
```

The API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

## API Endpoints

### `GET /`
Returns basic information about the API.

### `GET /health`
Health check endpoint to verify the API is running.

### `GET /analyze`
Analyze pain points from specified subreddits.

Query parameters:
- `subreddits`: Comma-separated list of subreddit names (e.g., `python,devops`)
- `limit`: Maximum number of posts per subreddit (default: 30)
- `query`: Search query for filtering posts (default: "complain OR issue OR problem")

Example:
```
GET /analyze?subreddits=python,devops&limit=10&query=issue
```

### `POST /analyze`
Analyze pain points from specified subreddits.

Request body:
```json
{
  "subreddits": ["python", "devops"],
  "limit": 10,
  "query": "issue OR problem"
}
```

Response:
```json
{
  "analysis": {
    "subreddits": ["python", "devops"],
    "post_count": 20,
    "category_count": 3,
    "categories": {
      "0": {
        "category_name": "Package Management Issues",
        "pain_points": "Users are experiencing difficulties with pip installations...",
        "post_count": 4,
        "post_titles": ["Having issues with pip", "..."]
      },
      "1": {
        "category_name": "Deployment Challenges",
        "pain_points": "Users are encountering problems with Docker deployments...",
        "post_count": 6,
        "post_titles": ["Docker deployment issue", "..."]
      }
    }
  }
}
```

## Environment Variables

- `REDDIT_CLIENT_ID`: Your Reddit API client ID
- `REDDIT_CLIENT_SECRET`: Your Reddit API client secret
- `REDDIT_USER_AGENT`: User agent string for Reddit API
- `LLM_MODEL`: Ollama model to use for summarization (default: qwen2.5:7b)
- `PORT`: Port to run the API server on (default: 8000)

## Dependencies

- FastAPI: Modern, fast web framework
- Pydantic: Data validation and settings management
- Uvicorn: ASGI server for FastAPI
- PRAW: Reddit API wrapper
- BERTopic: Topic modeling
- Sentence Transformers: Embedding generation
- Ollama: Local LLM inference

## Running with Docker

Build and run the Docker image:

```bash
docker build -t reddit-pain-points-api .
docker run -p 8000:8000 --env-file .env reddit-pain-points-api
```

## License

MIT 