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

subreddit = reddit.subreddit(os.environ["SUBREDDIT"])

queue = []


# listening to ws events
@sio.on("render_done_json")
def done(msg):
    global queue
    queueSearch = [x for x in queue if x["id"] == msg["renderID"]]
    if queueSearch == []:
        return
    queue = [x for x in queue if x["id"] != msg["renderID"]]
    try:
        queueSearch[0]["sub"].reply(
            "[replay provided by o!rdr]({link})\n\n----\n\n^(this comment is automated, dm me if I got something wrong)".format(
                link=msg["videoUrl"]
            )
        )
    except:
        print("error trying to reply to the submission")
        return
    print("replied to the post")


@sio.on("render_failed_json")
def failed(msg):
    global queue
    queueSearch = [x for x in queue if x["id"] == msg["renderID"]]
    if queueSearch == []:
        return
    queue = [x for x in queue if x["id"] != msg["renderID"]]
    print("render failed:", queueSearch[0])


for submission in subreddit.stream.submissions(skip_existing=True):
    # only catch submissions with "Gameplay" in flair
    if submission.link_flair_text != "Gameplay":
        continue
    print("found new submission:", submission.title)

    # getting access token
    try:
        access_token = utils.get_access_token()
    except:
        print("error getting access token")
        continue
    print("got access token")

    # parse the title of the submission and find the score
    try:
        scoreID = utils.parse_submission(submission.title, access_token)
        if not scoreID:
            print("replay unavailable")
            continue
    except:
        print("error finding the score")
        continue
    print("found the score:", scoreID)

    # download the replay
    try:
        replay = utils.replay_download(access_token, scoreID)
    except:
        print("error downloading the replay")
        continue
    print("got the replay for score", scoreID)

    # post the replay to o!rdr
    try:
        renderID = utils.ordr_post(replay)
    except:
        print("could't post the replay to o!rdr")
        continue
    print("posted the replay to o!rdr, renderID:", renderID)

    # add to render queue
    queue.append({"id": renderID, "sub": submission})
