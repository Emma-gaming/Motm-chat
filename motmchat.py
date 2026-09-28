import os
import time
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

# Custom CSS for high-contrast white text on dark background & input styling
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
        background-color: #1e1e24 !important;
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

if "user_text_input" not in st.session_state:
  st.session_state.user_text_input = ""

# --- SIDEBAR FOR CHAT HISTORY & RENAMING ---
with st.sidebar:
  st.title("⚙️ Chats")

  if st.button("➕ New Chat", use_container_width=True):
    new_id = str(uuid.uuid4())[:8]
    st.session_state.sessions[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_session_id = new_id
    st.session_state.user_text_input = ""
    st.rerun()

  st.divider()

  # Active chat rename section
  st.subheader("Rename Current Chat")
  current_title = st.session_state.sessions[current_id]["title"]
  new_chat_name = st.text_input(
      "Chat Title", value=current_title, key=f"rename_{current_id}"
  )
  if new_chat_name != current_title:
    st.session_state.sessions[current_id]["title"] = new_chat_name

  st.divider()
  st.subheader("Your Conversations")

  # List past chats
  for sess_id, sess_data in list(st.session_state.sessions.items()):
    is_active = sess_id == current_id
    button_label = (
        f"👉 {sess_data['title']}" if is_active else sess_data["title"]
    )
    if st.button(
        button_label, key=f"sess_{sess_id}", use_container_width=True
    ):
      st.session_state.current_session_id = sess_id
      st.session_state.user_text_input = ""
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

# Display Past Messages
for message in current_messages:
  with st.chat_message(message["role"]):
    if "image" in message and message["image"]:
      st.image(message["image"], caption="Character Reference", width=300)
    st.markdown(message["content"])

# --- INPUT CONTROLS ---
with st.container():
  uploaded_image = st.file_uploader(
      "Upload Character Reference Image (Optional)",
      type=["png", "jpg", "jpeg"],
      key=f"uploader_{current_id}",
  )

  user_input = st.text_area(
      "Type your roleplay action... (Actions with *, Speech with —)",
      value=st.session_state.user_text_input,
      key=f"input_box_{current_id}",
      height=100,
  )

  col1, col2 = st.columns([6, 1])
  with col2:
    send_clicked = st.button("Send", use_container_width=True)

# Trigger send logic
if send_clicked and user_input.strip():
  pil_img = None
  if uploaded_image is not None:
    pil_img = Image.open(uploaded_image)

  current_messages.append(
      {"role": "user", "content": user_input.strip(), "image": pil_img}
  )

  contents_payload = []
  if pil_img:
    contents_payload.append(pil_img)

  chat_history_text = MOTM_SYSTEM_PROMPT + "\n\nConversation History:\n"
  for msg in current_messages[-10:]:
    role_label = "User" if msg["role"] == "user" else "World/Characters"
    chat_history_text += f"{role_label}: {msg['content']}\n"

  contents_payload.append(chat_history_text)

  # Generate Response from Gemini with an auto-retry loop to handle 503 spikes gracefully
  reply = None
  for attempt in range(3):
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
      break
    except Exception as e:
      if "503" in str(e) and attempt < 2:
        time.sleep(2)  # Wait 2 seconds before retrying
        continue
      reply = f"// Error connecting to AI engine: {e}"

  current_messages.append({"role": "assistant", "content": reply, "image": None})

  st.session_state.user_text_input = ""
  st.rerun()
