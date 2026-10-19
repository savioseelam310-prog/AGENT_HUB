import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import webbrowser
from googleapiclient.discovery import build

# Import native Ollama components
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

# -------------------------------------------------------------------------
# Page Configuration & Styling
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Multi-Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    .success-box { padding: 1rem; border-radius: 0.5rem; background-color: #d4edda; color: #155724; margin-bottom: 1rem; }
    .error-box { padding: 1rem; border-radius: 0.5rem; background-color: #f8d7da; color: #721c24; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# Shared Local Ollama Model Setup
# -------------------------------------------------------------------------
@st.cache_resource
def get_ollama_model():
    return OllamaModel(
        model_name="qwen3.5:4b",#use your local llm
        provider=OllamaProvider(base_url="http://localhost:11434/v1")
    )

local_model = get_ollama_model()

# -------------------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------------------
st.sidebar.title("🚀 Control Center")
app_mode = st.sidebar.selectbox("Choose an Agent Tool", ["📧 Email Automation Agent", "📺 YouTube Search Assistant"])

st.sidebar.markdown("---")
st.sidebar.info("Ensure your local Ollama instance is running (`ollama serve`) with model `qwen3.5:4b` active.")

# -------------------------------------------------------------------------
# Tool 1: Email Automation Agent Implementation
# -------------------------------------------------------------------------
if app_mode == "📧 Email Automation Agent":
    st.title("📧 AI Email Generator & Dispatcher")
    st.markdown("Provide a natural language prompt, and the agent will parse out the recipient, subject, and body to send via Gmail.")

    with st.form("email_form"):
        prompt_input = st.text_area("What email would you like to generate and send?", placeholder="e.g., Send an email to john@example.com about our project update meeting tomorrow at 10 AM.")
        
        col1, col2 = st.columns(2)
        with col1:
            sender_email = st.text_input("Sender Gmail Address", value="example@gmail.com")
        with col2:
            sender_password = st.text_input("App Password", type="password", value="YOUR APP PASSWORD")
            
        submit_email = st.form_submit_button("Generate & Send Email")

    if submit_email:
        if not prompt_input:
            st.warning("Please enter a prompt for the email agent.")
        else:
            with st.spinner("Agent is structuring and dispatching your email..."):
                try:
                    # 1. Pydantic Payload Layout
                    class EmailPayload(BaseModel):
                        to_email: str = Field(description="The recipient's email address")
                        subject: str = Field(description="The subject line of the email")
                        body: str = Field(default="", description="The full text body of the email")

                    # 2. Configure Agent
                    email_agent = Agent(model=local_model, output_type=EmailPayload)

                    @email_agent.system_prompt
                    def provide_email_agent_prompt() -> str:
                        return "### You are an Email Agent. Your task is to generate a structured email payload based on the user's prompt. ###"

                    # Run Agent
                    result = email_agent.run_sync(prompt_input)
                    payload = result.output

                    # 3. Dispatch Email
                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(sender_email, sender_password)

                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = payload.to_email
                    msg["Subject"] = payload.subject
                    msg.attach(MIMEText(payload.body, "plain"))

                    server.sendmail(sender_email, payload.to_email, msg.as_string())
                    server.quit()

                    st.markdown(f'<div class="success-box">Success: Email successfully sent to <b>{payload.to_email}</b>!</div>', unsafe_allow_html=True)
                    
                    with st.expander("View Generated Email Preview"):
                        st.json({
                            "to": payload.to_email,
                            "subject": payload.subject,
                            "body": payload.body
                        })

                except Exception as e:
                    st.markdown(f'<div class="error-box">Error: Failed to send email. Details: {str(e)}</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------------
# Tool 2: YouTube Search Assistant Implementation
# -------------------------------------------------------------------------
elif app_mode == "📺 YouTube Search Assistant":
    st.title("📺 YouTube Video Discovery Agent")
    st.markdown("Search for trending topics, review AI-summarized insights, and launch videos instantly.")

    youtube_api_key = st.text_input("YouTube Data API Key", value="YOUR YOUTUBE API", type="password")
    yt_prompt = st.text_input("What content are you looking for?", placeholder="e.g., Python programming tutorials, AI news")
    max_results = st.slider("Max Results", min_value=1, max_value=10, value=5)

    if st.button("Search YouTube with Agent"):
        if not yt_prompt:
            st.warning("Please enter a search topic.")
        else:
            with st.spinner("Agent is querying YouTube and summarizing results..."):
                try:
                    # 1. Structured Outputs
                    class VideoDetails(BaseModel):
                        title: str = Field(description="The title of the YouTube video.")
                        video_id: str = Field(description="The unique YouTube video ID.")
                        channel_title: str = Field(description="The name of the channel.")
                        url: str = Field(description="Direct URL to watch the video.")

                    class VideoSearchResponse(BaseModel):
                        query: str = Field(description="The search query used.")
                        videos: List[VideoDetails] = Field(description="List of videos.")
                        summary: str = Field(description="A brief AI-generated summary.")

                    # 2. Initialize Agent & Tools
                    yt_agent = Agent(model=local_model, output_type=VideoSearchResponse)

                    @yt_agent.system_prompt
                    def provide_yt_prompt() -> str:
                        return "You are an expert YouTube assistant agent. Help users find relevant videos using the tool."

                    @yt_agent.tool
                    def search_trending_youtube_videos(ctx: RunContext, category: str, max_res: int = 5) -> List[dict]:
                        youtube = build("youtube", "v3", developerKey=youtube_api_key)
                        search_response = youtube.search().list(
                            q=category, part="snippet", maxResults=max_res, type="video", order="viewCount"
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

                    # Run Agent synchronously
                    result = yt_agent.run_sync(f"Search for {max_results} videos about {yt_prompt}")
                    output = result.output

                    st.success("Search Complete!")
                    st.markdown("### 📝 Agent Summary")
                    st.write(output.summary)

                    st.markdown(f"### 🎬 Results for: `{output.query}`")
                    for idx, video in enumerate(output.videos):
                        with st.container():
                            col_info, col_btn = st.columns([4, 1])
                            with col_info:
                                st.markdown(f"**{idx+1}. {video.title}**")
                                st.caption(f"Channel: {video.channel_title} | [Watch on YouTube]({video.url})")
                            with col_btn:
                                if st.button("Open Browser", key=f"btn_{video.video_id}"):
                                    webbrowser.open(video.url)
                            st.divider()

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")