# 🧠 Reddit Persona Generator

A Streamlit-based web app that scrapes a Reddit user's posts and comments and uses the **LLaMA3-70B model via the Groq API** to generate a structured, detailed **User Persona**. Outputs are saved as HTML and TXT with citations linking back to the original Reddit content.

---

## ✨ Features

- 🔗 Input any Reddit profile URL
- 📥 Scrapes recent posts and comments
- 🧠 Analyzes content using LLaMA3-70B (via Groq)
- 📝 Generates a persona with traits, behaviors, frustrations, motivations, and goals
- 🧾 Includes citations from Reddit content
- 💾 Saves HTML and TXT persona files
- 📂 View past persona generations

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/PranjalAyare/Reddit_Persona_Generator.git
cd Reddit_Persona_Generator

2. Install Dependencies
Make sure you're using Python 3.8 or newer.

pip install -r requirements.txt

3. Set Up Environment Variables
Copy the example .env file and fill in your credentials.

cp .env.example .env
Then edit .env and add the following:

REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
USER_AGENT=PersonaApp/0.1 by u/your_reddit_username
GROQ_API_KEY=your_groq_api_key

🔑 You'll need:

"A Reddit API app from https://www.reddit.com/prefs/apps"

"A Groq API key from https://console.groq.com"

4. Run the App
streamlit run app.py
"Then open http://localhost:8501 in your browser."

Sample Output
The output/ folder includes example personas generated for:

u/kojied - url - https://www.reddit.com/user/kojied/
u/Hungry-Move-6603 - url - https://www.reddit.com/user/Hungry-Move-6603/

You’ll find both .html and .txt persona formats inside the folder.

Powered By-
Python 
Streamlit
PRAW (Python Reddit API Wrapper)
Groq API + LLaMA3-70B
dotenv

License
This project is for assignment and educational purposes only. All API keys and generated data remain private to the user.

Author
Made with ❤️ by Pranjal Ayare
