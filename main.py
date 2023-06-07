import os
import praw
import utils
import socketio
from dotenv import load_dotenv

load_dotenv()
sio = socketio.Client()


@sio.event
def connect():
    print("ws connection established")


sio.connect("https://ordr-ws.issou.best")


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
    if submission.link_flair_text != "Gameplay":
        continue
    print("found new submission:", submission.title)
    access_token = utils.get_access_token()
    print("got access token")
    scoreID = utils.parse_submission(submission.title, access_token)
    if not scoreID:
        print("replay unavailable")
    print("found the score:", scoreID)
    replay = utils.replay_download(access_token, scoreID)
    print("got the replay for score", scoreID)
    renderID = utils.ordr_post(replay)
    print("posted the replay to o!rdr, renderID:", renderID)

    @sio.on("render_done_json")
    def done(msg):
        if msg["renderID"] == renderID:
            print(msg)
