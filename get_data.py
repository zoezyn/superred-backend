from typing import Any, List, Dict
import pandas as pd
import time
import praw
import asyncpraw
import requests
import os
import ollama
from dotenv import load_dotenv
import heapq  # Add this import at the top

# Load environment variables
load_dotenv()

# Reddit API setup using AsyncPRAW
async def setup_reddit() -> asyncpraw.Reddit:
    """
    Set up and return a Reddit instance using AsyncPRAW
    Uses environment variables for API credentials
    """
    reddit = asyncpraw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "web app by /u/default")
    )
    return reddit

# Function to get posts from a subreddit using AsyncPRAW
async def get_reddit_posts_async(reddit, subreddit_name, limit=20, search_query="complain OR issue OR problem") -> List[asyncpraw.models.Submission]:
    """
    Fetch posts from a subreddit using AsyncPRAW
    
    Args:
        reddit: An asyncpraw.Reddit instance
        subreddit_name: Name of the subreddit to search
        limit: Maximum number of posts to retrieve
        search_query: Query to search for in the subreddit
        
    Returns:
        List of Reddit submission objects
    """
    subreddit = await reddit.subreddit(subreddit_name)
    posts = []
    # TODO: whether to use relevance or hot
    async for post in subreddit.search(search_query, limit=limit, sort="hot", time_filter="all"):
        posts.append(post)
    return posts

# Main function to fetch posts from subreddits
async def get_posts_from_subreddits(subreddits: List[str], search_limit: int = 30, search_query: str = "complain OR issue OR problem") -> List[Dict[str, Any]]:
    """
    Fetch posts from multiple subreddits using AsyncPRAW
    
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
        reddit = await setup_reddit()
        print("Successfully connected to Reddit API")
    except Exception as e:
        print(f"Error setting up Reddit API: {str(e)}")
        return []
    
    for subreddit_name in subreddits:
        print(f"Getting posts from r/{subreddit_name}...")
        
        try:
            # # Get subreddit
            # subreddit = await reddit.subreddit(subreddit_name)

            # # Get icon URL
            # icon_url = None
            # if hasattr(subreddit, 'community_icon') and subreddit.community_icon:
            #     icon_url = subreddit.community_icon
            # elif hasattr(subreddit, 'icon_img') and subreddit.icon_img:
            #     icon_url = subreddit.icon_img
            # print("icon_url1: ", icon_url)
            
            # Get posts from subreddit
            posts = await get_reddit_posts_async(reddit, subreddit_name, search_limit, search_query)
            
            # Process posts
            for post in posts:
                post_data = {
                    'subreddit': subreddit_name,
                    # 'subreddit_icon': icon_url,
                    'title': post.title,
                    'content': post.selftext,
                    'url': post.url,
                    'score': post.score,
                    'num_comments': post.num_comments
                }
                all_results.append(post_data)
                
        except Exception as e:
            print(f"Error processing subreddit {subreddit_name}: {str(e)}")
            continue
    
    return all_results

async def find_relevant_subreddits(query: str, limit: int = 20) -> List[Dict]:
    """
    Find subreddits relevant to a query using Reddit's API
    
    Args:
        query: Search term to find relevant subreddits
        limit: Maximum number of subreddits to return
        
    Returns:
        List of subreddit information dictionaries
    """
    # Set up Reddit API
    try:
        reddit = await setup_reddit()
    except Exception as e:
        print(f"Error setting up Reddit API: {str(e)}")
        return []
    
    subreddits = []
    
    try:
        # Search for subreddits
        results = reddit.subreddits.search_by_name(query)
        
        # Use a heap to maintain top N subreddits by subscriber count
        top_subreddits = []  # This will be our min-heap
        seen_names = set()
        
        async for subreddit in results:
            if subreddit.display_name.lower() in seen_names:
                continue
                
            seen_names.add(subreddit.display_name.lower())
            
            # Load subreddit data
            await subreddit.load()
            
            # Get subscriber count (default to 0 if not available)
            subscribers = getattr(subreddit, 'subscribers', 0) or 0

            # Get icon URL (community icon or default icon)
            icon_url = None
            if hasattr(subreddit, 'community_icon') and subreddit.community_icon:
                icon_url = subreddit.community_icon
            elif hasattr(subreddit, 'icon_img') and subreddit.icon_img:
                icon_url = subreddit.icon_img

            # print("icon_url2: ", icon_url)
                
            
            # Get basic information
            subreddit_info = {
                'name': subreddit.name,
                'display_name': subreddit.display_name,
                'description': subreddit.public_description if hasattr(subreddit, 'public_description') else None,
                'subscribers': subscribers,
                'url': f"https://www.reddit.com/r/{subreddit.display_name}",
                'subreddit_icon': icon_url,
            }
            
            # Add to heap
            if len(top_subreddits) < limit:
                heapq.heappush(top_subreddits, (subreddit.subscribers, subreddit_info))
            else:
                heapq.heappushpop(top_subreddits, (subreddit.subscribers, subreddit_info))
        
        # Convert heap to sorted list
        subreddits = [info for _, info in sorted(top_subreddits, reverse=True)]
        # subreddits = [item[1] for item in sorted(top_subreddits)]
        
    except Exception as e:
        print(f"Error searching subreddits: {str(e)}")
    
    return subreddits

# For direct testing
if __name__ == "__main__":
    results = get_posts_from_subreddits(["python"], search_limit=5)
    print(f"Retrieved {len(results)} posts")
