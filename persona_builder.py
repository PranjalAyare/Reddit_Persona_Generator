import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime
import re

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def build_prompt(posts, comments, username):
    content_samples = []

    for post in posts[:5]:
        selftext = post.get('selftext') if post.get('selftext') else "[No selftext provided]"
        title = post.get('title', 'No Title')
        url = post.get('url', '')
        text = f"Post: {title}\n{selftext}\nURL: https://reddit.com{url}"
        content_samples.append(text)

    for comment in comments[:5]:
        body = comment.get('body') if comment.get('body') else "[No comment body provided]"
        url = comment.get('url', '')
        text = f"Comment: {body}\nURL: https://reddit.com{url}"
        content_samples.append(text)

    combined_text = "\n\n".join(content_samples)

    if not combined_text.strip():
        combined_text = "No recent posts or comments available for analysis for this user."

    prompt = f"""
You are a personality analyst AI. Based on the Reddit posts and comments below from user u/{username}, generate a **User Persona** that includes:

1.  **name** (realistic)
2.  **age_range** (inferred, e.g., "25-35")
3.  **occupation** or field of interest (inferred)
4.  **traits** (as a JSON array of strings, e.g., ["analytical", "curious", "supportive"])
5.  **behaviors** (as a JSON array of strings, e.g., ["engages in technical discussions", "shares personal anecdotes", "asks follow-up questions"])
6.  **frustrations** (as a JSON array of strings)
7.  **motivations** (as a JSON array of strings)
8.  **goals_needs** (as a JSON array of strings)
9.  **archetype** (e.g., "The Innovator", "The Learner", "The Advocate")
10. **citations** (Cite the specific Reddit post/comment and include the URL used to infer each characteristic. This should be a JSON object where keys are concise descriptions (strings) and values are URLs (strings). Each key-value pair must be correctly comma-separated. Example: {{"Expressed interest in programming": "https://reddit.com/r/learnprogramming/comments/123xyz", "Showed concern for privacy": "https://reddit.com/r/privacy/comments/abcde"}} )
11. **profile_image_prompt** (Suggest a potential profile image description for an AI image generator based on the persona, e.g., "A young woman with a laptop, smiling, in a cozy cafe setting, soft lighting.")

Respond in structured JSON format only, with no markdown wrappers (like ```json), no preambles, and no explanations outside of the JSON object itself. Ensure all string values are properly escaped within the JSON.

### Reddit Content for u/{username}:
{combined_text}
    """
    return prompt.strip()


def fetch_reddit_avatar(username):
    try:
        response = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers={"User-Agent": "PersonaApp/0.1 by u/Accomplished_Pop764"}
        )
        if response.status_code == 200:
            data = response.json()
            icon_img_url = data.get("data", {}).get("icon_img")
            if icon_img_url and ("default_avatar" in icon_img_url or "external_picture" in icon_img_url):
                return None
            return icon_img_url
        else:
            print(f"DEBUG: Failed to fetch Reddit avatar for {username}: Status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Error fetching Reddit avatar for {username}: {e}")
    return None


def generate_persona(posts, comments, username):
    prompt = build_prompt(posts, comments, username)

    print("📡 Sending prompt to Groq (LLaMA3-70B)...")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "You are a user persona generator that responds in strict JSON format only. No markdown wrappers. No explanation. Just the raw JSON object."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 8000
            },
            timeout=120
        )

        response.raise_for_status()
        raw_content = response.json()["choices"][0]["message"]["content"]
        print("🧾 Raw response preview:\n", raw_content[:500])

        cleaned = raw_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"❌ Initial JSON parsing failed: {e}")
            print("Attempting robust JSON parsing...")

            start_brace = cleaned.find('{')
            end_brace = cleaned.rfind('}')

            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                potential_json = cleaned[start_brace : end_brace + 1]
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError as inner_e:
                    print(f"❌ Robust JSON parsing failed too: {inner_e}")
                    print("Partial JSON content being attempted:")
                    print(potential_json[:500] + "...")
                    raise Exception(f"Failed to parse JSON response from LLM even after cleaning: {inner_e}") from inner_e
            else:
                raise Exception("Could not find valid JSON structure ({...}) in LLM response.")

    except requests.exceptions.HTTPError as e:
        error_message = f"Groq API HTTP Error: {e.response.status_code} - {e.response.text}"
        print(f"❌ {error_message}")
        raise Exception(error_message) from e
    except requests.exceptions.RequestException as e:
        error_message = f"Network or API connection error: {e}"
        print(f"❌ {error_message}")
        raise Exception(error_message) from e
    except Exception as e:
        print(f"❌ An unexpected error occurred during persona generation: {e}")
        raise e


def save_persona(username, persona_dict, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"persona_{username}.html")
    avatar_url = fetch_reddit_avatar(username)

    citations = persona_dict.get('citations', {})
    citations_html = "<ul>"
    if isinstance(citations, dict):
        if citations:
            for key, url in citations.items():
                citations_html += f"<li><strong>{key}:</strong> <a href='{url}' target='_blank'>{url}</a></li>"
        else:
            citations_html += "<li>No specific citations provided.</li>"
    elif isinstance(citations, list):
        if citations:
            for item in citations:
                match = re.match(r'^(.*?):\s*(https?://\S+)$', str(item))
                if match:
                    desc, url = match.groups()
                    citations_html += f"<li><strong>{desc.strip()}:</strong> <a href='{url}' target='_blank'>{url}</a></li>"
                else:
                    citations_html += f"<li>{item}</li>"
        else:
            citations_html += "<li>No specific citations provided.</li>"
    else:
        citations_html += f"<li>{citations}</li>"
    citations_html += "</ul>"

    traits_html = "<ul>" + "".join(f"<li>{trait}</li>" for trait in persona_dict.get('traits', ['N/A'])) + "</ul>"
    behaviors_html = "<ul>" + "".join(f"<li>{behavior}</li>" for behavior in persona_dict.get('behaviors', ['N/A'])) + "</ul>"
    frustrations_html = "<ul>" + "".join(f"<li>{frustration}</li>" for frustration in persona_dict.get('frustrations', ['N/A'])) + "</ul>"
    motivations_html = "<ul>" + "".join(f"<li>{motivation}</li>" for motivation in persona_dict.get('motivations', ['N/A'])) + "</ul>"
    goals_needs_html = "<ul>" + "".join(f"<li>{goal}</li>" for goal in persona_dict.get('goals_needs', ['N/A'])) + "</ul>"

    html = f"""
    <html>
    <head><title>Persona: {persona_dict.get('name', 'N/A')}</title><style>
    body {{ font-family: Arial, sans-serif; padding: 30px; max-width: 800px; margin: auto; }}
    img {{ max-width: 180px; border-radius: 10px; }}
    h1 {{ color: #e76f51; }}
    h2 {{ color: #264653; }}
    .trait {{ margin-bottom: 1em; }}
    .citations {{ font-size: 0.9em; color: gray; }}
    </style></head>
    <body>
    <h1>{persona_dict.get('name', 'N/A')}</h1>
    <p><strong>Age Range:</strong> {persona_dict.get('age_range', 'N/A')}</p>
    <p><strong>Occupation:</strong> {persona_dict.get('occupation', 'N/A')}</p>
    <p><strong>User Archetype:</strong> {persona_dict.get('archetype', 'N/A')}</p>
    {f'<img src="{avatar_url}" alt="Profile image">' if avatar_url else ''}

    <h2>Personality Traits</h2>
    <div class="trait">{traits_html}</div>

    <h2>Behavior Patterns</h2>
    <div class="trait">{behaviors_html}</div>

    <h2>Frustrations</h2>
    <div class="trait">{frustrations_html}</div>

    <h2>Motivations</h2>
    <div class="trait">{motivations_html}</div>

    <h2>Goals & Needs</h2>
    <div class="trait">{goals_needs_html}</div>

    <h2>Citations</h2>
    <div class="citations">{citations_html}</div>

    <p><em>Profile image inspiration: {persona_dict.get('profile_image_prompt', 'N/A')}</em></p>
    <footer><hr><p style="font-size:0.8em;color:gray;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></footer>
    </body></html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Persona saved to {filename}")


def save_persona_text(username, persona_dict, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"persona_{username}.txt")

    text_content = f"--- Persona for u/{username} ---\n\n"
    text_content += f"Name: {persona_dict.get('name', 'N/A')}\n"
    text_content += f"Age Range: {persona_dict.get('age_range', 'N/A')}\n"
    text_content += f"Occupation: {persona_dict.get('occupation', 'N/A')}\n"
    text_content += f"User Archetype: {persona_dict.get('archetype', 'N/A')}\n\n"

    text_content += "Personality Traits:\n"
    for trait in persona_dict.get('traits', ['N/A']):
        text_content += f"- {trait}\n"
    text_content += "\n"

    text_content += "Behavior Patterns:\n"
    for behavior in persona_dict.get('behaviors', ['N/A']):
        text_content += f"- {behavior}\n"
    text_content += "\n"

    text_content += "Frustrations:\n"
    for frustration in persona_dict.get('frustrations', ['N/A']):
        text_content += f"- {frustration}\n"
    text_content += "\n"

    text_content += "Motivations:\n"
    for motivation in persona_dict.get('motivations', ['N/A']):
        text_content += f"- {motivation}\n"
    text_content += "\n"

    text_content += "Goals & Needs:\n"
    for goal in persona_dict.get('goals_needs', ['N/A']):
        text_content += f"- {goal}\n"
    text_content += "\n"

    citations = persona_dict.get('citations', {})
    text_content += "Citations:\n"
    if isinstance(citations, dict):
        if citations:
            for key, url in citations.items():
                text_content += f"- {key}: {url}\n"
        else:
            text_content += "No specific citations provided.\n"
    elif isinstance(citations, list):
        if citations:
            for item in citations:
                match = re.match(r'^(.*?):\s*(https?://\S+)$', str(item))
                if match:
                    desc, url = match.groups()
                    text_content += f"- {desc.strip()}: {url}\n"
                else:
                    text_content += f"- {item}\n"
        else:
            text_content += "No specific citations provided.\n"
    else:
        text_content += f"- {citations}\n"
    text_content += "\n"

    text_content += f"Profile Image Inspiration: {persona_dict.get('profile_image_prompt', 'N/A')}\n\n"
    text_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text_content += "-----------------------------------\n"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text_content)

    print(f"✅ Persona text saved to {filename}")
