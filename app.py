import streamlit as st
import requests
import base64
import os
from google.genai import Client
from elevenlabs.client import ElevenLabs

# ==========================================
# 1. CONFIGURATION & KEYS
# ==========================================
# Replace your old lines with these:
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
VOICE_ID = "pNInz6obpgDQGcFmaJgB"

# ==========================================
# 2. INITIALIZATION
# ==========================================
@st.cache_resource
def init_clients():
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
    audio_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    return ai_client, audio_client

try:
    ai_client, audio_client = init_clients()
except Exception as e:
    st.error(f"Initialization Error: {e}")

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def render_svg(filename):
    # This safely finds your robot.svg no matter where you run the code
    base_path = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_path, filename)
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            svg_content = f.read()
        b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        st.markdown(f'<div style="display:flex; justify-content:center;"><img src="data:image/svg+xml;base64,{b64}" width="180"/></div>', unsafe_allow_html=True)
    except Exception as e:
        st.caption(f"🤖 Mascot offline: File not found at {filepath}")

# ==========================================
# 4. PAGE LAYOUT & UI
# ==========================================
st.set_page_config(page_title="StormBot", layout="wide")
st.title("⛈️ StormBot National Command Center")

col1, col2 = st.columns([1.2, 1])

# --- Column 1: Live Alerts ---
with col1:
    st.header("📡 Live Alerts")
    try:
        response = requests.get("https://api.weather.gov/alerts/active", headers={"User-Agent": "WeatherApp/1.0"}, timeout=5)
        alerts = response.json().get("features", [])
        if not alerts:
            st.success("No active weather alerts right now.")
        for alert in alerts[:20]:
            props = alert.get("properties", {})
            st.error(f"**{props.get('event')}** - {props.get('areaDesc')}")
    except Exception as e:
        st.warning("Could not fetch live alerts right now. The Weather API might be busy.")

# --- Column 2: Chat Interface ---
with col2:
    st.header("💬 Chat with StormBot")
    
    # 1. Display the Mascot
    render_svg("robot.svg")
    
    # 2. Initialize Chat History with your exact custom greeting
    if "messages" not in st.session_state:
        st.session_state.messages = []
        greeting = "Hello! I am StormBot. How can I help you today?"
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        
    # 3. Display Previous Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 4. Chat Input & AI Response Logic
    if user_question := st.chat_input("Ask about weather..."):
        
        # Show what the user typed
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.write(user_question)
            
        # Define StormBot's personality
        system_instruction = (
            "You are StormBot, an advanced severe weather console assistant. "
            "You are a world-class expert on every piece of meteorological history. "
            "Keep your explanations highly engaging, clear, and perfectly formatted for voice output."
        )
        
        # Generate and show the AI's response
        with st.chat_message("assistant"):
            try:
                full_prompt = f"User Question: {user_question}"
                ai_response = ai_client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=full_prompt, 
                    config={"system_instruction": system_instruction}
                )
                bot_response = ai_response.text
                st.write(bot_response)
                
                # Save response to history
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                # Generate and play Audio
                audio = audio_client.text_to_speech.convert(
                    text=bot_response, 
                    voice_id=VOICE_ID, 
                    model_id="eleven_turbo_v2_5"
                )
                st.audio(b"".join(audio), format="audio/mp3", autoplay=True)
                
            except Exception as e:
                st.error(f"System Error: Could not generate response. Check your API keys. ({e})")