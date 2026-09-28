import os
import streamlit as st
from google import genai

# --- API KEY CONFIGURATION ---
# 1. Try loading from Streamlit secrets first
api_key = None
try:
  if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
  pass

# 2. Fallback: If you want to paste your key directly here as a quick fix, 
# replace None with your key string like: api_key = "AIzaSy..."
if not api_key:
  api_key = os.environ.get("GEMINI_API_KEY")

# Initialize Gemini Client with the explicit key
client = genai.Client(api_key=api_key)

# Page configuration for a clean app UI
st.set_page_config(
    page_title="Myth of the Machine RP", page_icon="⚙️", layout="centered"
)

# Custom CSS for dark-mode interface with high-contrast white text
st.markdown(
    """
    <style>
    .stApp {
        background-color: #121214;
        color: #FFFFFF !important;
    }
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    .stChatMessage {
        color: #FFFFFF !important;
    }
    .stTextInput input {
        color: #FFFFFF !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# App Header
st.title("⚙️ Myth of the Machine")
st.caption(
    "Multi-Character Universe • Lore Source:"
    " https://www.tumblr.com/myth-of-the-machine"
)

# System Instructions embedding the Tumblr source context and multi-character roleplay rules
MOTM_SYSTEM_PROMPT = """
You are the master roleplay engine for an interactive story set in the 'Myth of the Machine' (MOTM) universe by flygutxx and nortsauce (sourced from their official Tumblr: https://www.tumblr.com/myth-of-the-machine). 

CORE BEHAVIOR:
- You control ALL canon characters in this universe (including Cuphead, Mugman, Bendy, Boris, Mickey, etc.) dynamically depending on the scene. 
- Do NOT roleplay as the user. Let the user dictate their own actions and words. If the user does not specify a character, you can have relevant canon characters react, speak, or drive the scene forward.
- Match the dark, gritty, rubber-hose aesthetic, emotional weight, and narrative pacing of the webcomic.

STRICT ROLEPLAY FORMATTING RULES:
1. Use asterisks for actions: *Bendy glances over his shoulder, gripping the map tightly.*
2. Use an em dash and quotes for spoken dialogue: — "We shouldn't stay here long."
3. Use parentheses for internal thoughts of characters: (Is this really going to work?)
4. Use double slashes for out-of-roleplay notes or system updates: // Let's move the scene to the ink bar.
"""

# Initialize Chat History
if "messages" not in st.session_state:
  st.session_state.messages = []

# Display Past Messages
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# User Input Box
if user_input := st.chat_input(
    "Type your roleplay action... (Actions with *, Speech with — "")"
):
  # Append user input
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

  # Build conversation history context for Gemini
  chat_history_text = ""
  for msg in st.session_state.messages[
      -12:
  ]:  # Keeps the last 12 messages for active memory
    role_label = "User" if msg["role"] == "user" else "World/Characters"
    chat_history_text += f"{role_label}: {msg['content']}\n"

  # Generate Response from Gemini
  try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=chat_history_text,
        config={
            "system_instruction": MOTM_SYSTEM_PROMPT,
            "temperature": 0.85,  # High creativity for immersive roleplay
        },
    )
    reply = response.text
  except Exception as e:
    reply = f"// Error connecting to AI engine: {e}"

  # Append assistant response
  st.session_state.messages.append({"role": "assistant", "content": reply})
  with st.chat_message("assistant"):
    st.markdown(reply)
    
