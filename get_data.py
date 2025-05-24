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
from pydantic import BaseModel, Field
# Load environment variables
load_dotenv()

class PainPointVerification(BaseModel):
    is_pain_point: str = Field(..., description="Whether the post describes a pain point (yes/no)")
    

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

search_query = """
(complain OR complaint OR rant OR vent) OR 
(issue OR problem OR bug OR glitch) OR 
(pain OR frustration OR struggle) OR 
(angry OR upset OR disappointed) OR 
(terrible OR awful OR horrible OR worst OR sucks)
"""

# Function to get posts from a subreddit using AsyncPRAW
# async def get_reddit_posts_async(reddit, subreddit_name, limit=20, search_query="complain OR complaint OR issue OR problem OR frustration OR annoying OR terrible OR awful OR horrible OR worst OR sucks OR hate OR disappointed OR upset OR angry OR rant") -> List[asyncpraw.models.Submission]:
async def get_reddit_posts_async(reddit, subreddit_name, limit=20, search_query="pain OR hate OR awful OR sucks") -> List[asyncpraw.models.Submission]:
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

# def verify_pain_point_llm(title: str, content: str) -> bool:

#     import os
#     from llama_api_client import LlamaAPIClient

#     prompt = f"""
#     Title: {title}
#     Content: {content}
    
#     Is this post describing a pain point, complaint, problem or frustration? 
#     Reply with ONLY True or False. Do not include any other text.
#     """

#     client = LlamaAPIClient(
#         api_key="LLM|1057903439523843|6el9gGOfbACHYHblcRudwDgdBW8",
#         base_url="https://api.llama.com/v1/",
#     )

#     response = client.chat.completions.create(
#         model="Llama-4-Maverick-17B-128E-Instruct-FP8",
#         messages=[
#             {"role": "user", "content": prompt},
#         ],
#         # response_format={
#         #     "type": "text",
#         #     "json_schema": {
#         #         "schema": {
#         #             "properties": {
#         #                 "is_pain_point": {
#         #                     "type": "boolean",
#         #                     "description": "True or False"
#         #                 }
#         #             },
#         #             "required": ["is_pain_point"]
#         #         },
#         #     },
#         # },
#     )

#     print("response: ", response.completion_message.content.text)
#     return response.completion_message.content.text=="True"


# def verify_pain_point_inferless(title: str, content: str) -> bool:
#     """
#     Use LLM to verify if a post is describing a pain point
#     """
#     # Truncate content if too long
#     # max_content_length = 1000
#     # if len(content) > max_content_length:
#     #     content = content[:max_content_length] + "..."
    
#     prompt = f"""
#     Title: {title}
#     Content: {content}
    
#     Is this post describing a pain point, complaint, problem or frustration? 
#     Reply with ONLY "yes" or "no". Do not include any other text.
#     """
    
#     try:

#         import requests 
#         import json
#         URL = 'https://serverless-v3.inferless.com/api/v1/qwen2-72b-instruct_1085bb85c3874347b752a91868521b9f/infer'
#         headers = {"Content-Type": "application/json", "Authorization": "Bearer 170698753362c103d43ec90d4659c4d94bb0980f6916b8a98e83b9eb1dd010e47b7e168b1315c697cbc024458cf33d3ff1aae93fb45b4b3db1d86a3ad2eb69d9"}

#         data = {
#             "inputs": [
#                 {
#                     "name": "prompt",
#             "shape": [
#                 1
#             ],
#                     "data": [
#                         prompt
#                     ],
#                     "datatype": "BYTES"
#                 },
#                 {
#                     "name": "temperature",
#                     "optional": True,
#                     "shape": [
#                 1
#             ],
#             "data": [
#                 0.7
#             ],
#                     "datatype": "FP32"
#                 },
#                 {
#                     "name": "top_p",
#                     "optional": True,
#                     "shape": [
#                 1
#             ],
#             "data": [
#                 0.1
#             ],
#             "datatype": "FP32"
#             },
#             {
#                     "name": "repetition_penalty",
#                     "optional": True,
#                     "shape": [
#                         1
#                     ],
#             "data": [
#                 1.18
#             ],
#             "datatype": "FP32"
#             },
#             {
#                     "name": "max_tokens",
#                     "optional": True,
#                     "shape": [
#                         1
#                     ],
#             "data": [
#                 512
#             ],
#             "datatype": "INT16"
#             },
#             {
#                     "name": "top_k",
#                     "optional": True,
#                     "shape": [
#                         1
#                     ],
#             "data": [
#                 40
#                     ],
#                     "datatype": "INT8"
#                 }
#             ]
#         }


#         response = requests.post(URL, headers=headers, data=json.dumps(data))
#         # print(response.json()['outputs'][0]['data'][0])



#         # Use Gemini (since you're already using it)
#         # client = genai.Client(api_key=GEMINI_API_KEY)
#         # response = client.models.generate_content(
#         #     model="gemini-2.0-flash",
#         #     contents=prompt
#         # )
        
#         answer = response.json()['outputs'][0]['data'][0]
#         print("answer: ", answer)
#         return "yes" in answer
        
#     except Exception as e:
#         print(f"Error using LLM for verification: {str(e)}")
#         # Fallback to rules-based approach
#         # return verify_pain_point(title, content)
    
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
                    # if verify_pain_point_llm(post.title, post.selftext):
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

    except Exception as e:
        print(f"Error setting up Reddit API: {str(e)}")
        # return []
    
    finally:
        await reddit.close()  # Ensure client is closed
    
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
    
    finally:
        await reddit.close()  # Ensure client is closed
    
    return subreddits

# For direct testing
if __name__ == "__main__":
    results = get_posts_from_subreddits(["python"], search_limit=5)
    print(f"Retrieved {len(results)} posts")
