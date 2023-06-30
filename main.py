import os
import praw
import utils
import socketio
from sty import fg
from dotenv import load_dotenv

load_dotenv()
sio = socketio.Client()


@sio.event
def connect():
    print(fg.green + "ws connection established" + fg.rs)


sio.connect("https://ordr-ws.issou.best")


reddit = praw.Reddit(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    username=os.environ["USERNAME"],
    password=os.environ["PASSWORD"],
    user_agent=os.environ["USER_AGENT"],
)

print(fg.green + "Logged in to", fg.blue + str(reddit.user.me()) + fg.rs)

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
    parsed = queueSearch[0]["parsed"]
    try:
        queueSearch[0]["sub"].reply(
            "[{username} | {artist} - {title} \[{difficulty}\]]({link})\n\n----\n\n^(replay provided by [o!rdr](https://ordr.issou.best/))\n\n^(this comment is automated, dm me if I got something wrong)".format(
                link=msg["videoUrl"],
                username=parsed["username"],
                artist=parsed["artist"],
                title=parsed["title"],
                difficulty=parsed["difficulty"],
            )
        )
    except:
        print(fg.red + "error trying to reply to the submission" + fg.rs)
        return
    print(fg.green + "replied to the post" + fg.rs)


@sio.on("render_failed_json")
def failed(msg):
    global queue
    queueSearch = [x for x in queue if x["id"] == msg["renderID"]]
    if queueSearch == []:
        return
    queue = [x for x in queue if x["id"] != msg["renderID"]]
    print(fg.red + "render failed:", fg.yellow, str(queueSearch[0]["id"]) + fg.rs)


for submission in subreddit.stream.submissions(skip_existing=True):
    # only catch submissions with "Gameplay" in flair
    # if submission.link_flair_text != "Gameplay":
    #     continue
    print(fg.green + "found new submission:", fg.blue + submission.title + fg.rs)
    try:
        parsed = utils.parse_submission(submission.title)
        scoreID, access_token = utils.find_score(parsed)
    except Exception as e:
        print(fg.red + "error:", e)
        continue
    print(fg.green + "found the score:", fg.blue + scoreID + fg.rs)

    # download the replay
    try:
        replay = utils.replay_download(access_token, scoreID)
    except:
        print(fg.red + "error:", fg.yellow + "couldn't download the replay" + fg.rs)
        continue
    print(fg.green + "got the replay for score", fg.blue + scoreID + fg.rs)

    # post the replay to o!rdr
    try:
        renderID = utils.ordr_post(replay)
    except:
        print(fg.red + "error:", fg.yellow + "could't post the replay to o!rdr" + fg.rs)
        continue
    print(fg.green + "posted the replay to o!rdr, renderID:", fg.blue + str(renderID) + fg.rs)

    # add to render queue
    queue.append({"id": renderID, "sub": submission, "parsed": parsed})
