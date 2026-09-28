import os
import uuid
import streamlit as st
from google import genai
from PIL import Image

# --- API KEY CONFIGURATION ---
api_key = None
try:
  if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
  pass

if not api_key:
  api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="Myth of the Machine RP", page_icon="⚙️", layout="centered"
)

# Custom CSS for high-contrast white text on dark background
st.markdown(
    """
    <style>
    .stApp {
        background-color: #121214;
        color: #FFFFFF !important;
    }
    p, span, label, div, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #FFFFFF !important;
    }
    .stChatMessage {
        color: #FFFFFF !important;
    }
    .stTextInput input, .stTextArea textarea {
        color: #FFFFFF !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CHAT SESSION MANAGEMENT ---
if "sessions" not in st.session_state:
  default_id = str(uuid.uuid4())[:8]
  st.session_state.sessions = {default_id: {"title": "New Chat", "messages": []}}
  st.session_state.current_session_id = default_id

if st.session_state.current_session_id not in st.session_state.sessions:
  st.session_state.current_session_id = list(st.session_state.sessions.keys())[0]

current_id = st.session_state.current_session_id

# --- SIDEBAR FOR CHAT HISTORY ---
with st.sidebar:
  st.title("⚙️ Chats")

  if st.button("➕ New Chat", use_container_width=True):
    new_id = str(uuid.uuid4())[:8]
    st.session_state.sessions[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_session_id = new_id
    st.rerun()

  st.divider()

  for sess_id, sess_data in list(st.session_state.sessions.items()):
    is_active = sess_id == current_id
    button_label = (
        f"👉 {sess_data['title']}" if is_active else sess_data["title"]
    )
    if st.button(
        button_label, key=f"sess_{sess_id}", use_container_width=True
    ):
      st.session_state.current_session_id = sess_id
      st.rerun()

# --- MAIN CHAT INTERFACE ---
st.title("⚙️ Myth of the Machine")
st.caption(
    "Multi-Character Universe • Lore Source:"
    " https://www.tumblr.com/myth-of-the-machine"
)

MOTM_SYSTEM_PROMPT = """
You are the master roleplay engine for an interactive story set in the 'Myth of the Machine' (MOTM) universe by flygutxx and nortsauce (sourced from their official Tumblr: https://www.tumblr.com/myth-of-the-machine). 

CORE BEHAVIOR:
- You control ALL canon characters in this universe (including Cuphead, Mugman, Bendy, Boris, Mickey, etc.) dynamically depending on the scene. 
- Do NOT roleplay as the user. Let the user dictate their own actions and words. If the user does not specify a character, or if an image of an original character/design is provided, analyze the image details (clothing, features, style) and have the canon characters react to them seamlessly.
- Match the dark, gritty, rubber-hose aesthetic, emotional weight, and narrative pacing of the webcomic.

STRICT ROLEPLAY FORMATTING RULES:
1. Use asterisks for actions: *Bendy glances over his shoulder, gripping the map tightly.*
2. Use an em dash and quotes for spoken dialogue: — "We shouldn't stay here long."
3. Use parentheses for internal thoughts of characters: (Is this really going to work?)
4. Use double slashes for out-of-roleplay notes or system updates: // Let's move the scene to the ink bar.
"""

current_messages = st.session_state.sessions[current_id]["messages"]

# Display Past Messages (including images if attached)
for message in current_messages:
  with st.chat_message(message["role"]):
    if "image" in message and message["image"]:
      st.image(message["image"], caption="Character Reference", width=300)
    st.markdown(message["content"])

# Image uploader widget for character references
uploaded_image = st.file_uploader(
    "Upload Character Reference Image (Optional)",
    type=["png", "jpg", "jpeg"],
    key=f"uploader_{current_id}",
)

# User Input Box
if user_input := st.chat_input(
    "Type your roleplay action... (Actions with *, Speech with — "")"
):
  # Set automatic title based on first prompt
  if (
      st.session_state.sessions[current_id]["title"] == "New Chat"
      and len(user_input) > 0
  ):
    st.session_state.sessions[current_id]["title"] = (
        user_input[:25] + "..." if len(user_input) > 25 else user_input
    )

  # Process uploaded image PIL format if present
  pil_img = None
  if uploaded_image is not None:
    pil_img = Image.open(uploaded_image)

  # Append user input and image to session history
  current_messages.append(
      {"role": "user", "content": user_input, "image": pil_img}
  )

  with st.chat_message("user"):
    if pil_img:
      st.image(pil_img, caption="Character Reference", width=300)
    st.markdown(user_input)

  # Build contents payload for Gemini SDK supporting multimodal inputs
  contents_payload = []
  if pil_img:
    contents_payload.append(pil_img)

  # Add recent chat history context text
  chat_history_text = MOTM_SYSTEM_PROMPT + "\n\nConversation History:\n"
  for msg in current_messages[-10:]:
    role_label = "User" if msg["role"] == "user" else "World/Characters"
    chat_history_text += f"{role_label}: {msg['content']}\n"

  contents_payload.append(chat_history_text)

  # Generate Response from Gemini
  try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=contents_payload,
        config={
            "system_instruction": MOTM_SYSTEM_PROMPT,
            "temperature": 0.85,
        },
    )
    reply = response.text
  except Exception as e:
    reply = f"// Error connecting to AI engine: {e}"

  # Append assistant response
  current_messages.append({"role": "assistant", "content": reply, "image": None})
  with st.chat_message("assistant"):
    st.markdown(reply)
