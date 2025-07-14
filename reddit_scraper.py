import praw
import os
from dotenv import load_dotenv

load_dotenv()  
def init_reddit():
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("USER_AGENT")

    print("📡 DEBUG: Initializing Reddit client with:")
    print("CLIENT ID:", client_id)
    print("CLIENT SECRET:", client_secret[:5] + "..." if client_secret else "None")
    print("USER AGENT:", user_agent)

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        check_for_async=False  # avoids asyncio warning in latest versions
    )
    
    return reddit

def get_user_content(username, limit=50):
    reddit = init_reddit()
    user = reddit.redditor(username)

    posts = []
    comments = []

    try:
        for submission in user.submissions.new(limit=limit):
            posts.append({
                "title": submission.title,
                "selftext": submission.selftext,
                "url": submission.permalink
            })
        for comment in user.comments.new(limit=limit):
            comments.append({
                "body": comment.body,
                "url": comment.permalink
            })
    except Exception as e:
        print(f"❌ Error fetching content for {username}: {e}")

    return posts, comments
