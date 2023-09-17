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
    print(fg.green + "WebSocket connection established" + fg.rs)


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
    print(fg.red + "Render failed:" + fg.yellow, score["renderID"], fg.rs)


while True:
    for submission in subreddit.stream.submissions(skip_existing=True):
        if not all([cue in submission.title for cue in scorepost_cues]):
            continue
        print(fg.green + "New scorepost:", fg.blue + submission.title + fg.rs)

        score = {}

        try:
            score["parsed"] = utils.parse_submission(submission.title)
            score["scoreInfo"], access_token = utils.find_score(score["parsed"])
        except Exception as e:
            print(fg.red + "Error:", e)
            continue
        print(fg.green + "Found the score:", fg.blue + str(score["scoreInfo"]["best_id"]) + fg.rs)

        is_duplicated = False
        for idx, duplicated in enumerate(score_list):
            if duplicated["scoreInfo"]["best_id"] == str(score["scoreInfo"]["best_id"]):
                if duplicated.get("videoUrl") == None:
                    print(fg.yellow + "Duplicated with a rendering score" + fg.rs)
                    score_list[idx]["submissions"].append(submission)
                else:
                    print(fg.yellow + "Duplicated with a rendered score" + fg.rs)
                    duplicated["submissions"].append(submission)
                    utils.reply(duplicated)
                is_duplicated = True
                break
        if is_duplicated:
            continue

        try:
            replay = utils.replay_download(access_token, str(score["scoreInfo"]["best_id"]))
        except:
            print(fg.red + "Error:", fg.yellow + "couldn't download the replay" + fg.rs)
            continue
        print(fg.green + "Got the replay for score", fg.blue + str(score["scoreInfo"]["best_id"]) + fg.rs)

        try:
            score["renderID"] = utils.ordr_post(replay, score["scoreInfo"])
        except:
            print(fg.red + "Error:", fg.yellow + "couldn't post the replay to o!rdr" + fg.rs)
            continue
        print(fg.green + "Posted the replay to o!rdr, renderID:", fg.blue + str(score["renderID"]) + fg.rs)

        score["submissions"] = [submission]
        score_list.append(score)
