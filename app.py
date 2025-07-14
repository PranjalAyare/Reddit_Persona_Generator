import streamlit as st
from reddit_scraper import get_user_content
from persona_builder import generate_persona, save_persona, save_persona_text
import os
import glob

st.set_page_config(page_title="Reddit Persona Generator", layout="centered")

st.title("🧠 Reddit Persona Generator")
st.markdown("Enter a Reddit profile URL below to generate a user persona using LLaMA3-70B (Groq API).")

url_input = st.text_input("🔗 Reddit Profile URL", placeholder="https://www.reddit.com/user/One_Statistician3285/")
generate = st.button("🚀 Generate Persona")

# Define output folder
PERSONA_OUTPUT_DIR = "output"
os.makedirs(PERSONA_OUTPUT_DIR, exist_ok=True)

# Style block defined globally for reuse
style_block = """
<style>
    body { background-color: white; color: black; }
</style>
"""

# Generate persona and store in session state
if generate and url_input.strip():
    try:
        username = url_input.rstrip("/").split("/")[-1]
        st.info(f"Fetching content for u/{username}...")
        posts, comments = get_user_content(username)
        st.success(f"✅ Fetched {len(posts)} posts and {len(comments)} comments")

        if not posts and not comments:
            st.warning("⚠️ No content found for that user.")
        else:
            persona = generate_persona(posts, comments, username)
            save_persona(username, persona, PERSONA_OUTPUT_DIR)
            save_persona_text(username, persona, PERSONA_OUTPUT_DIR)

            html_path = os.path.join(PERSONA_OUTPUT_DIR, f"persona_{username}.html")
            txt_path = os.path.join(PERSONA_OUTPUT_DIR, f"persona_{username}.txt")

            st.session_state["persona"] = persona
            st.session_state["html_path"] = html_path
            st.session_state["txt_path"] = txt_path

            st.success("🎉 Persona generated and saved!")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# If persona exists in session state and files exist, show previews and download buttons
if "persona" in st.session_state:
    persona = st.session_state["persona"]
    html_path = st.session_state["html_path"]
    txt_path = st.session_state["txt_path"]

    if os.path.exists(html_path) and os.path.exists(txt_path):
        # === HTML Preview with Light Style ===
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = style_block + html_content

        st.markdown("### 📄 Persona HTML Preview")
        st.components.v1.html(html_content, height=600, scrolling=True)

        # === TXT Preview ===
        with open(txt_path, "r", encoding="utf-8") as f:
            txt_content = f.read()
        st.markdown("### 📜 Persona Text Preview")
        st.text_area("Persona Text File", txt_content, height=300)

        # === Download Buttons ===
        st.markdown("### ⬇️ Download Files")
        with open(html_path, "rb") as f:
            st.download_button("Download HTML", f, file_name=os.path.basename(html_path), mime="text/html")

        with open(txt_path, "rb") as f:
            st.download_button("Download TXT", f, file_name=os.path.basename(txt_path), mime="text/plain")

        # === Quick Summary ===
        with st.expander("🔍 Preview Persona Summary"):
            st.write(f"**Name:** {persona.get('name')}")
            st.write(f"**Age Range:** {persona.get('age_range')}")
            st.write(f"**Occupation:** {persona.get('occupation')}")
            st.write(f"**Archetype:** {persona.get('archetype')}")
            st.write(f"**Traits:** {', '.join(persona.get('traits', []))}")
            st.write(f"**Behaviors:** {', '.join(persona.get('behaviors', []))}")
            st.write(f"**Frustrations:** {', '.join(persona.get('frustrations', []))}")
            st.write(f"**Motivations:** {', '.join(persona.get('motivations', []))}")
            st.write(f"**Goals & Needs:** {', '.join(persona.get('goals_needs', []))}")
            st.caption(f"💡 Image prompt: {persona.get('profile_image_prompt')}")
    else:
        st.warning("⚠️ Generated persona files not found. Please regenerate.")

# === Persona History Viewer ===
st.markdown("### 📂 Persona History")
history_files = glob.glob(os.path.join(PERSONA_OUTPUT_DIR, "persona_*.html"))

if history_files:
    selected = st.selectbox("Select a Persona to View", ["-- Select --"] + [os.path.basename(f) for f in history_files])

    if selected != "-- Select --":
        view_path = os.path.join(PERSONA_OUTPUT_DIR, selected)

        try:
            with open(view_path, "r", encoding="utf-8") as f:
                html_data = f.read()

            with st.expander(f"📁 View {selected}", expanded=True):
                st.components.v1.html(style_block + html_data, height=600, scrolling=True)
                st.download_button("⬇️ Download Again", html_data, file_name=selected, mime="text/html")
        except FileNotFoundError:
            st.error("❌ Selected file not found. Please refresh the list.")

    if st.button("🧹 Clear All History"):
        for f in history_files:
            os.remove(f)
        st.rerun()
else:
    st.info("No persona history found.")