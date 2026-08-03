import os
import webbrowser
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from googleapiclient.discovery import build
from fastapi import FastAPI, HTTPException
import uvicorn

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = your_new_youtube_api_key

# Ensure environment variables are set for Ollama
local_model_1 = OllamaModel(
    model_name="qwen3.5:4b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1")
)

# -------------------------------------------------------------------------
# 1. Define Structured Outputs using Pydantic
# -------------------------------------------------------------------------
class VideoDetails(BaseModel):
    title: str = Field(description="The title of the YouTube video.")
    video_id: str = Field(description="The unique YouTube video ID.")
    channel_title: str = Field(description="The name of the channel that uploaded the video.")
    view_count: Optional[str] = Field(description="Number of views if available.", default="N/A")
    url: str = Field(description="Direct URL to watch the video.")

class VideoSearchResponse(BaseModel):
    query: str = Field(description="The search query or category used.")
    videos: List[VideoDetails] = Field(description="List of trending or searched videos.")
    summary: str = Field(description="A brief AI-generated summary of the findings.")


# -------------------------------------------------------------------------
# 2. Initialize Pydantic AI Agent with Ollama
# -------------------------------------------------------------------------
agent = Agent(
    model=local_model_1,
    output_type=VideoSearchResponse,
)

@agent.system_prompt
def provide_agent_prompt() -> str:
    return "You are an expert YouTube assistant agent. Your task is to help users find trending . or relevant videos using the provided tools. Once videos are found, you can also open   them up in the user's web browser if requested."



# -------------------------------------------------------------------------
# 3. Define Tools for the Agent
# -------------------------------------------------------------------------
@agent.tool
def search_trending_youtube_videos(ctx: RunContext, category: str = "Technology", max_results: int = 5) -> List[dict]:
    """
    Search for trending or popular YouTube videos based on a topic or category.
    
    Args:
        category: The topic or search query (e.g., 'Python programming', 'Gaming', 'AI news').
        max_results: Number of results to return (default is 5).
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY environment variable is missing.")

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    search_response = youtube.search().list(
        q=category,
        part="snippet",
        maxResults=max_results,
        type="video",
        order="viewCount"
    ).execute()

    formatted_videos = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        formatted_videos.append({
            "title": snippet["title"],
            "video_id": video_id,
            "channel_title": snippet["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    return formatted_videos


@agent.tool
def open_video_in_browser(ctx: RunContext, video_url: str) -> str:
    """
    Opens a specific YouTube video URL in the system's default web browser.
    
    Args:
        video_url: The full valid YouTube watch URL to open.
    """
    try:
        webbrowser.open(video_url)
        return f"Successfully opened {video_url} in your default web browser."
    except Exception as e:
        return f"Failed to open browser: {str(e)}"


# -------------------------------------------------------------------------
# 4. Wrap with FastAPI Microservice
# -------------------------------------------------------------------------
app = FastAPI(title="YouTube Pydantic AI Service")

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/youtube-agent")
async def run_youtube_agent(request: PromptRequest):
    try:
        result = await agent.run(request.prompt)
        return {
            "status": "success",
            "query": result.output.query,
            "summary": result.output.summary,
            "videos": [v.dict() for v in result.output.videos]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Runs the FastAPI server on port 5001 to integrate directly with your Node.js app
    uvicorn.run(app, host="0.0.0.0", port=5001)
