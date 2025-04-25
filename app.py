import streamlit as st
import openai
import os
import requests
from dotenv import load_dotenv
from PIL import Image
import io
import base64
import re

# --- Setup ---
load_dotenv()
st.set_page_config(
    page_title="AI Art Con", 
    page_icon="🎨", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling and tighter spacing
st.markdown("""
    <style>
        textarea, .stTextArea textarea {
            margin-bottom: -50px !important;
            padding: 0.5em 0.7em;
        }

        .button-row {
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            gap: 5px;
            margin-top: 0px;
            margin-bottom: 0px;
        }

        .footer {
            text-align: center;
            color: #888888;
            font-size: 0.85rem;
            margin-top: 5px;
            font-weight: bold;
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: auto;
        }
    </style>
""", unsafe_allow_html=True)

# Load API keys
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

# --- State Initialization ---
for key in ["image", "generated_prompt", "gallery", "page"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["image", "generated_prompt"] else [] if key == "gallery" else "main"

# --- Main App Page ---
def main_page():
    st.title("🎨 AI Art Companion")
    st.write("Describe your idea and let the AI help you bring it to life with vivid art.")
    
    st.markdown('<div style="margin-top: -20px; margin-bottom: -15px;">', unsafe_allow_html=True)
    user_input = st.text_area("🧠What do you imagine?", placeholder="e.g. A dragon flying over a neon city at night...", height=150)

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        generate_btn = st.button("✨ Generate Image", key="generate_image")
    with col2:
        gallery_btn = st.button("🖼️ View Gallery", key="view_gallery")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        💡 Models used: Prompt by DeepSeek · Art by Stability AI
    </div>
    """, unsafe_allow_html=True)

    if generate_btn:
        if not user_input.strip():
            st.warning("Please describe your idea.")
        else:
            with st.spinner("Generating creative prompt..."):
                try:
                    st.session_state.generated_prompt = get_ai_prompt(user_input)
                    st.success("Prompt ready!")
                except Exception as e:
                    st.error(f"Prompt generation failed: {e}")
                    return

            with st.spinner("Creating image..."):
                try:
                    st.session_state.image = generate_image_stability(st.session_state.generated_prompt)
                    st.session_state.gallery.append(st.session_state.image)
                except Exception as e:
                    st.error(f"Image generation failed: {e}")
                    return

    if gallery_btn:
        st.session_state.page = "gallery"
        st.rerun()

    if st.session_state.image:
        st.image(st.session_state.image, caption="🖼️ AI-Generated Art", use_container_width=True)
        with st.expander("📜 View Prompt"):
            st.markdown(st.session_state.generated_prompt)

        buf = io.BytesIO()
        st.session_state.image.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button("📥 Download This Image", data=byte_im, file_name="ai_art.png", mime="image/png")

# --- Gallery Page ---
def gallery_page():
    st.title("🖼️ Your Art Gallery")
    
    if st.button("← Back to Generator"):
        st.session_state.page = "main"
        st.rerun()
    
    if st.session_state.gallery:
        for i, img in enumerate(reversed(st.session_state.gallery)):
            st.image(img, width=350, caption=f"Artwork #{len(st.session_state.gallery)-i}")
    else:
        st.info("You haven't generated any art yet.")

    st.markdown("""
    <div class="footer">
        💡 Models used: Prompt by DeepSeek · Art by Stable Diffusion XL
    </div>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def get_ai_prompt(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="deepseek/deepseek-r1-zero:free",
            messages=[
                {"role": "system", "content": "You help turn ideas into vivid prompts for AI art generators."},
                {"role": "user", "content": f"Turn this into a detailed prompt for an AI art generator: {user_input}"}
            ]
        )
        raw_prompt = response['choices'][0]['message']['content']
        cleaned = re.sub(r"\\boxed\{?|[{}]", "", raw_prompt).strip()
        return cleaned
    except Exception as e:
        raise Exception(f"Error generating prompt: {e}")

def generate_image_stability(prompt):
    try:
        engine_id = "stable-diffusion-xl-1024-v1-0"
        api_host = "https://api.stability.ai"
        response = requests.post(
            f"{api_host}/v1/generation/{engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {STABILITY_API_KEY}"
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            },
        )
        if response.status_code != 200:
            raise Exception(f"Non-200 response: {response.text}")
        data = response.json()
        image_data = base64.b64decode(data["artifacts"][0]["base64"])
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise Exception(f"Error generating image: {e}")

# --- Run App ---
if st.session_state.page == "main":
    main_page()
elif st.session_state.page == "gallery":
    gallery_page()
