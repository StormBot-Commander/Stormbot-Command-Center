import streamlit as st
import requests
import base64
import os
from google.genai import Client
from elevenlabs.client import ElevenLabs

# ==========================================
# 1. CONFIGURATION & KEYS
# ==========================================
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
VOICE_ID = "6KcjEPr15ksjFhMMxIVy"

# ==========================================
# 2. INITIALIZATION
# ==========================================
@st.cache_resource
def init_clients():
    # FIXED: Changed from genai.Client to just Client
    ai_client = Client(api_key=GEMINI_API_KEY)
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

# --- Column 1: Live Alerts & SPC Outlook ---
with col1:
    st.header("📡 Live Alerts")
    try:
        # Fetching national alerts with a limit to keep the UI snappy
        response = requests.get("https://api.weather.gov/alerts/active?limit=20", headers={"User-Agent": "WeatherApp/1.0"}, timeout=5)
        alerts = response.json().get("features", [])
        
        if not alerts:
            st.success("No active weather alerts right now.")
        
        for alert in alerts:
            props = alert.get("properties", {})
            # Filtering for severe alerts to keep the list clean
            if props.get('severity') in ['Extreme', 'Severe']:
                st.error(f"**{props.get('event')}** - {props.get('areaDesc')}")
    except Exception as e:
        st.warning("Could not fetch live alerts right now. The Weather API might be busy.")

    st.subheader("⚠️ SPC Outlook")
    st.markdown("[View Full SPC Outlook Map](https://www.spc.noaa.gov/products/outlook/)")

# --- Column 2: Chat Interface ---
with col2:
    st.header("💬 Chat with StormBot")
    
    # 1. Display the Mascot
    render_svg("robot.svg")
    
    # 2. Initialize Chat History
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
        
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.write(user_question)
            
        # Context gathering
        current_alerts = [f"{a['properties']['event']} in {a['properties']['areaDesc']}" for a in alerts[:5]]
        alert_context = "Current National Alerts: " + ", ".join(current_alerts) if current_alerts else "No active alerts."

        # Define StormBot's personality
        # Updated Y'allbot-style personality
system_instruction = (
    "You are StormBot, a Southern-style severe weather meteorologist. "
    "Your personality is friendly, conversational, and uses slight Southern colloquialisms (like 'y'all', 'fixin' to', 'keep an eye on it'). "
    "You are obsessed with radar details—always mention what you're seeing on the screen in a plain, helpful way. "
    "When there is severe weather, you switch to 'alert mode': stay serious, clear, and urgent. "
    "Keep responses short, punchy, and sound like you're talking to a neighbor. "
    "Never sound like a robot; sound like a person sitting in the weather center."
)
        
        with st.chat_message("assistant"):
            try:
                ai_response = ai_client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=user_question, 
                    config={"system_instruction": system_instruction}
                )
                bot_response = ai_response.text
                st.write(bot_response)
                
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