import os
import praw
import socketio
from supabase import create_client, ClientOptions
from dotenv import load_dotenv
from utils import (
    log,
    parse_submission,
    get_access_token,
    find_score,
    replay_download,
    ordr_post,
    reply,
)

load_dotenv()

supabase = create_client(
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_API_KEY"],
    options=ClientOptions(
        postgrest_client_timeout=20,
    ),
)

sio = socketio.Client()


@sio.event
def connect():
    log("WebSocket connection established")


@sio.event
def disconnect():
    log("Disconnected from WebSocket")


@sio.event
def connect_error():
    log("The connection failed!")


@sio.on("render_done_json")
def done(msg):
    score = (
        supabase.table("scores")
        .select("*")
        .eq("render_id", str(msg["renderID"]))
        .execute()
        .data
    )
    if score == []:
        return
    score = (
        supabase.table("scores")
        .update({"render_url": msg["videoUrl"]})
        .eq("score_id", score[0]["score_id"])
        .execute()
        .data
    )
    scoreposts = (
        supabase.table("scoreposts")
        .select("*", "scores(*)")
        .eq("score_id", score[0]["score_id"])
        .execute()
        .data
    )
    for scorepost in scoreposts:
        try:
            reply(reddit.submission(scorepost["scorepost_id"]), score[0])
            supabase.table("scoreposts").update({"is_replied": True}).eq(
                "scorepost_id", scorepost["scorepost_id"]
            ).execute()
        except Exception as e:
            print("Error", e)


sio.connect("https://apis.issou.best/", socketio_path="/ordr/ws")

reddit = praw.Reddit(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    username=os.environ["USERNAME"],
    password=os.environ["PASSWORD"],
    user_agent=os.environ["USER_AGENT"],
)
log(f"Logged in to {reddit.user.me()}")

subreddit = reddit.subreddit(os.environ["SUBREDDIT"])

scorepost_cues = ["|", "-", "[", "]"]

while True:
    for scorepost in subreddit.stream.submissions(skip_existing=True):
        if not all([cue in scorepost.title for cue in scorepost_cues]):
            continue
        log(f"New scorepost: ({scorepost.id}): {scorepost.title}")

        try:
            parsed = parse_submission(scorepost.title)
            access_token = get_access_token()
            score_info = find_score(parsed, access_token)
            log(f"Found the score: {score_info['id']}")
            stored_score = (
                supabase.table("scores")
                .select("*")
                .eq("score_id", score_info["id"])
                .execute()
                .data
            )
            if stored_score != []:
                supabase.table("scoreposts").insert(
                    {"scorepost_id": scorepost.id, "score_id": score_info["id"]}
                ).execute()
                if stored_score[0]["render_url"]:
                    log("Duplicated with a rendered score")
                    reply(scorepost, stored_score[0])
                    supabase.table("scoreposts").update({"is_replied": True}).eq(
                        "scorepost_id", scorepost.id
                    ).execute()
                else:
                    log("Duplicated with a rendering score")
                continue
            replay = replay_download(access_token, score_info)
            render_id = ordr_post(replay, score_info)
            log(f"Posted replay of {score_info["id"]} to o!rdr")

            supabase.table("scores").insert(
                {"score_id": score_info["id"], "render_id": render_id}
            ).execute()
            supabase.table("scoreposts").insert(
                {"scorepost_id": scorepost.id, "score_id": score_info["id"]}
            ).execute()

        except Exception as e:
            log("Error:", e)
            continue
