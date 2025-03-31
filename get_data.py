from typing import Any, List, Dict
import pandas as pd
import time
import praw
import requests
import os
import ollama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reddit API setup using PRAW
def setup_reddit() -> praw.Reddit:
    """
    Set up and return a Reddit instance using PRAW
    Uses environment variables for API credentials
    """
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "web app by /u/default")
    )
    return reddit

# Function to get posts from a subreddit using PRAW
def get_reddit_posts_praw(reddit, subreddit_name, limit=20, search_query="complain OR issue OR problem") -> List[praw.models.Submission]:
    """
    Fetch posts from a subreddit using PRAW
    
    Args:
        reddit: A praw.Reddit instance
        subreddit_name: Name of the subreddit to search
        limit: Maximum number of posts to retrieve
        search_query: Query to search for in the subreddit
        
    Returns:
        List of Reddit submission objects
    """
    subreddit = reddit.subreddit(subreddit_name)
    posts = subreddit.search(search_query, limit=limit)
    return list(posts)

# # Function to filter posts that likely contain complaints
# def filter_complaint_posts(posts) -> List[praw.models.Submission]:
#     """
#     Filter posts that likely contain complaints based on keywords and patterns
#     """
#     complaint_keywords = [
#         'problem', 'issue', 'hate', 'annoying', 'frustrated', 'disappointing',
#         'terrible', 'awful', 'wish', 'should', 'need to', 'can\'t stand',
#         'difficult', 'struggle', 'pain', 'annoyed', 'tired of', 'sick of',
#         'why isn\'t there', 'why can\'t', 'doesn\'t work', 'broken'
#     ]
    
#     filtered_posts = []
    
#     for post in posts:
#         title = post.title.lower()
#         selftext = post.selftext.lower() if hasattr(post, 'selftext') else ''
        
#         # Check if any complaint keywords are in the title or text
#         if any(keyword in title or keyword in selftext for keyword in complaint_keywords):
#             filtered_posts.append(post)
    
#     return filtered_posts


# def summarize_pain_point1(text, model="qwen2.5:7b") -> str:
#     """
#     Use Ollama to summarize the pain point from a post
#     """
#     # Truncate text if it's too long (many models have context limits)
#     max_length = 4000
#     if len(text) > max_length:
#         text = text[:max_length] + "..."
    
#     prompt = f"""
#     The following is a post from Reddit. Identify and summarize the main pain point or problem the user is experiencing in 1-2 sentences.
#     If there's a potential business opportunity or startup idea to solve this problem, briefly mention it.
#     If no clear pain point exists, respond with "No clear pain point identified."
    
#     POST:
#     {text}
    
#     PAIN POINT SUMMARY:
#     """
    
#     try:
#         response = ollama.generate(model=model, prompt=prompt)
#         return response['response'].strip()
#     except Exception as e:
#         return f"Error: {str(e)}"

# Main function to fetch posts from subreddits
def get_posts_from_subreddits(subreddits: List[str], search_limit: int = 30, search_query: str = "complain OR issue OR problem") -> List[Dict[str, Any]]:
# def analyze_subreddit_pain_points(subreddits, posts_per_subreddit=5):
    """
    Fetch posts from multiple subreddits using PRAW
    
    Args:
        subreddits: List of subreddit names
        search_limit: Maximum number of posts per subreddit
        search_query: Query to search for in subreddits
        
    Returns:
        List of post dictionaries
    """
    all_results = []
    
    # Set up Reddit API
    try:
        reddit = setup_reddit()
        print("Successfully connected to Reddit API")
    except Exception as e:
        print(f"Error setting up Reddit API: {str(e)}")
        return []
    
    for subreddit_name in subreddits:
        print(f"Getting posts from r/{subreddit_name}...")
        
        try:
            # Get posts from subreddit
            subreddit = reddit.subreddit(subreddit_name)
            posts = subreddit.search(search_query, limit=search_limit)
            
            # Process each post
            for post in posts:
                # Combine title and text for analysis
                content = post.selftext if hasattr(post, 'selftext') else '[No content]'
                
                # Get comments (limited to avoid rate limiting)
                comments = []
                post.comments.replace_more(limit=0)  # Only get top-level comments
                for comment in list(post.comments)[:3]:  # Limit to first 3 comments
                    comments.append(comment.body)
                
                # Add to results
                result = {
                    'subreddit': subreddit_name,
                    'title': post.title,
                    'content': content,
                    'comments': comments,
                    'url': f"https://www.reddit.com{post.permalink}",
                    'score': post.score,
                    'num_comments': post.num_comments,
                }
                
                all_results.append(result)
                
                # Avoid rate limiting
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error processing r/{subreddit_name}: {str(e)}")
    
    return all_results

# For direct testing
if __name__ == "__main__":
    results = get_posts_from_subreddits(["python"], search_limit=5)
    print(f"Retrieved {len(results)} posts")
