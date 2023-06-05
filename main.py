import os
import praw
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    username=os.environ["USERNAME"],
    password=os.environ["PASSWORD"],
    user_agent=os.environ["USER_AGENT"],
)

print("Logged in to", reddit.user.me())

subreddit = reddit.subreddit("allehStestlol")

for submission in subreddit.stream.submissions(skip_existing=True):
    print(submission.title)
