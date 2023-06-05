import os
import praw
import time
from dotenv import load_dotenv
load_dotenv()

reddit = praw.Reddit(
    client_id = os.environ.get("CLIENT_ID"),
    client_secret = os.environ.get("CLIENT_SECRET"),
    username = os.environ.get("USERNAME"),
    password = os.environ.get("PASSWORD"),
    user_agent = os.environ.get("USER_AGENT")
)

print("Logged in to", reddit.user.me())

subreddit = reddit.subreddit("allehStestlol")

start_time = time.time()
for submission in subreddit.stream.submissions():
    if submission.created_utc < start_time:
        # skip older posts
        continue
    print(submission.title)