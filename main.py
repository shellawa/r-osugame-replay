import os
import praw
import utils
import socketio
from utils import log
from sty import fg
from dotenv import load_dotenv

load_dotenv()
sio = socketio.Client()


@sio.event
def connect():
    log(fg.green + "WebSocket connection established" + fg.rs)


@sio.event
def disconnect():
    log(fg.yellow + "Disconnected from WebSocket" + fg.rs)


@sio.event
def connect_error():
    log(fg.red + "The connection failed!" + fg.rs)


sio.connect("https://ordr-ws.issou.best")


reddit = praw.Reddit(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    username=os.environ["USERNAME"],
    password=os.environ["PASSWORD"],
    user_agent=os.environ["USER_AGENT"],
)

log(fg.green + "Logged in to", fg.blue + str(reddit.user.me()) + fg.rs)

subreddit = reddit.subreddit(os.environ["SUBREDDIT"])

scorepost_cues = ["|", "-", "[", "]"]

score_list = []


@sio.on("render_done_json")
def done(msg):
    global score_list
    score_search = [score for score in score_list if score["renderID"] == msg["renderID"]]
    if score_search == []:
        return
    score_list = [score for score in score_list if score["renderID"] != msg["renderID"]]
    score = score_search[0]
    score["videoUrl"] = msg["videoUrl"]
    utils.reply(score)
    score["submissions"] = []
    score_list.append(score)


@sio.on("render_failed_json")
def failed(msg):
    global score_list
    score_search = [score for score in score_list if score["renderID"] == msg["renderID"]]
    if score_search == []:
        return
    score_list = [score for score in score_list if score["renderID"] != msg["renderID"]]
    log(fg.red + "Render failed:" + fg.yellow, score["renderID"], fg.rs)


while True:
    for submission in subreddit.stream.submissions(skip_existing=True):
        if not all([cue in submission.title for cue in scorepost_cues]):
            continue
        log(fg.green + "New scorepost (" + submission.id + "): " + fg.blue + submission.title + fg.rs)

        score = {}

        try:
            score["parsed"] = utils.parse_submission(submission.title)
            score["score_info"], access_token = utils.find_score(score["parsed"])
        except Exception as e:
            log(fg.red + "Error:", e)
            continue
        log(fg.green + "Found the score:", fg.blue + str(score["score_info"]["best_id"]) + fg.rs)

        is_duplicated = False
        for idx, duplicated in enumerate(score_list):
            if duplicated["score_info"]["best_id"] == score["score_info"]["best_id"]:
                if duplicated.get("videoUrl") == None:
                    log(fg.yellow + "Duplicated with a rendering score" + fg.rs)
                    score_list[idx]["submissions"].append(submission)
                else:
                    log(fg.yellow + "Duplicated with a rendered score" + fg.rs)
                    duplicated["submissions"].append(submission)
                    utils.reply(duplicated)
                is_duplicated = True
                break
        if is_duplicated:
            continue

        try:
            replay = utils.replay_download(access_token, score["score_info"]["best_id"])
        except:
            log(fg.red + "Error:", fg.yellow + "couldn't download the replay" + fg.rs)
            continue
        log(fg.green + "Got the replay for score", fg.blue + str(score["score_info"]["best_id"]) + fg.rs)

        try:
            score["renderID"] = utils.ordr_post(replay, score["score_info"])
        except:
            log(fg.red + "Error:", fg.yellow + "couldn't post the replay to o!rdr" + fg.rs)
            continue
        log(fg.green + "Posted the replay to o!rdr, renderID:", fg.blue + str(score["renderID"]) + fg.rs)

        score["submissions"] = [submission]
        score_list.append(score)
