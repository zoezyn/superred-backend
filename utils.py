from typing import Dict, List
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import pandas as pd
from IPython.display import display, HTML
import ollama
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from google import genai
import json
from functools import lru_cache
from umap import UMAP
from hdbscan import HDBSCAN

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cache for models
@lru_cache(maxsize=1)
def get_bertopic_model():
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine')
    hdbscan_model = HDBSCAN(min_cluster_size=15, metric='euclidean', cluster_selection_method='eom', prediction_data=True)

    return BERTopic(
        embedding_model="all-MiniLM-L6-v2",
        min_topic_size=2,
        verbose=True,
        # umap_model=umap_model
    )

@lru_cache(maxsize=1)
def get_sentence_transformer():
    return SentenceTransformer('all-MiniLM-L6-v2')

def categorize_posts(posts_data: List[Dict]) -> Dict:
    """
    Group similar pain points into categories using BERTopic
    
    Args:
        posts_data: List of post dictionaries from Reddit
        
    Returns:
        Dict of post clusters keyed by cluster ID
    """
    # Extract content for topic modeling
    all_post_contents = [post['content'] for post in posts_data]
    print("len(all_post_contents): ", len(all_post_contents))
    
    # Skip categorization if there are not enough posts
    if len(all_post_contents) < 5:  # Minimum threshold
        print(f"Not enough posts ({len(all_post_contents)}) for topic modeling. Returning all posts in a single category.")
        return {0: posts_data}  # Return all posts in a single category
    
    try:
        # Use cached model
        topic_model = get_bertopic_model()
        
        # Process in batches if there are many posts
        # batch_size = 100
        # all_topics = []
        # all_probs = []
        
        # for i in range(0, len(all_post_contents), batch_size):
        #     batch = all_post_contents[i:i + batch_size]
        #     batch_topics, batch_probs = topic_model.fit_transform(batch)
        #     all_topics.extend(batch_topics)
        #     if batch_probs is not None:
        #         all_probs.extend(batch_probs)
            
        #     # Clear batch data
        #     del batch
        #     del batch_topics
        #     del batch_probs
        
        topics, probs = topic_model.fit_transform(all_post_contents)
        # Group posts by cluster
        categorized_posts = {}
        for i, cluster in enumerate(topics):
            if cluster not in categorized_posts:
                categorized_posts[cluster] = []
            categorized_posts[cluster].append(posts_data[i])
        
        # # Clear large data structures
        # del all_post_contents
        # del all_topics
        # del all_probs
        
        return categorized_posts
    
    except Exception as e:
        print(f"Error in topic modeling: {str(e)}")
        # Fallback: return all posts in a single category
        return {0: posts_data}

class CategoryResponse(BaseModel):
    category: str = Field(..., description="A category name that best describes these related issues")
    pain_points: str = Field(..., description="2-4 sentences summarizing the shared problems")
    
    @validator('category', 'pain_points')
    def not_empty(cls, v):
        if not v or v.isspace():
            raise ValueError("Field cannot be empty")
        return v

def summarize_pain_points(categorized_posts: Dict) -> Dict:
    """
    Summarize each category of posts using Ollama
    
    Args:
        categorized_posts: Dict of post clusters keyed by cluster ID
        
    Returns:
        Dict of categories with summaries keyed by cluster ID
    """
    # Get model name from environment or use default
    # model = os.getenv("LLM_MODEL", "qwen2.5:7b")
    
    
    # Summarize each category
    categories = {}
    for cluster, posts in categorized_posts.items():
        # Skip outlier topic
        if cluster == -1:
            continue
            
        try:
            # Process one cluster at a time
            post_contents = "\n".join([post['content'] for post in posts])

            print("Number of words: ", len(post_contents.split(' ')))

            
            prompt = f"""
            Based on these related posts, identify the common pain point or problem these users are experiencing.

            Posts:
            {post_contents}

            You must respond in valid JSON format with exactly these fields:

            category: A category name that best describes these related issues
            pain_points: 2-4 sentences summarizing the shared problems

            Do not include any other text, explanations, or formatting in your response.
            There should be only one category and one pain point.

            Make it short and concise.
            """
            
            # Clear post contents after creating prompt
            del post_contents
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            llm_response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': CategoryResponse,
                },
            )

            try:
                parsed_json = json.loads(llm_response.text)
                category_model = CategoryResponse(**parsed_json)
            except (json.JSONDecodeError, ValueError):
                category = "Uncategorized"
                pain_points = "No clear pain points identified."
                
                lines = llm_response.split('\n')
                for line in lines:
                    if line.lower().startswith("category:"):
                        category = line[line.find(":")+1:].strip()
                    elif line.lower().startswith("pain points:"):
                        pain_points = line[line.find(":")+1:].strip()
                
                category_model = CategoryResponse(
                    category=category,
                    pain_points=pain_points
                )
            
            # Store the validated and structured data
            categories[cluster] = {
                'category': category_model.category,
                'pain_points': category_model.pain_points,
                'posts': posts,
            }
            
            # Clear response data
            del llm_response
            del category_model
            
        except Exception as e:
            print(f"Error summarizing cluster {cluster}: {str(e)}")
            continue
    
    return categories

# def extract_pain_points_summary(categories: Dict) -> List[Dict]:
#     """
#     Extract and format the pain point summaries from categorized data
    
#     Args:
#         categories: Dict of categories with summaries
        
#     Returns:
#         List of pain point summaries with category info
#     """
#     summaries = []
    
#     for cluster_id, cluster_data in categories.items():
#         category_info = cluster_data['category_info']
#         posts = cluster_data['posts']
        
#         # Parse category and pain points from the LLM output
#         category = "Uncategorized"
#         pain_points = "No clear pain points identified."
        
#         for line in category_info.split('\n'):
#             if line.startswith('Category:'):
#                 category = line.replace('Category:', '').strip()
#             elif line.startswith('Pain Points:'):
#                 pain_points = line.replace('Pain Points:', '').strip()
        
#         # Create a summary object
#         summary = {
#             'cluster_id': cluster_id,
#             'category': category,
#             'pain_points': pain_points,
#             'post_count': len(posts),
#             'subreddits': list(set([post['subreddit'] for post in posts])),
#             'posts': posts
#         }
        
#         summaries.append(summary)
    
#     return summaries