from time import time
from sty import fg
import os
import requests
import re

re_username = re.compile(r"^[^|]*")
re_artist = re.compile(r"(?<= \| )(.*?)(?= \- )")
re_title = re.compile(r"(?<= \- )(.*?)(?=\[)")
re_difficulty = re.compile(r"(?<=\[)(.*?)(?=\])")
re_creator = re.compile(r"(?<=] \()(.*?)(?=,|\|)")
re_accuracy = re.compile(r"\d+(?:\.\d+)?%")
re_ss = re.compile(r" ss ", re.IGNORECASE)


def log(*args, **kwargs):
    print(*args, **kwargs)
    if "WEBHOOK_LINK" in os.environ:
        normalized = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", " ".join(str(x) for x in args)).strip()
        try:
            requests.post(
                os.environ["WEBHOOK_LINK"],
                json={"content": normalized, "username": "allehS"},
            )
        except Exception:
            pass


def parse_submission(subTitle):
    username = re.search(re_username, subTitle)
    if not username:
        raise Exception(fg.yellow + "couldn't parse username" + fg.rs)
    artist = re.search(re_artist, subTitle)
    if not artist:
        raise Exception(fg.yellow + "couldn't parse artist" + fg.rs)
    title = re.search(re_title, subTitle)
    if not title:
        raise Exception(fg.yellow + "couldn't parse title" + fg.rs)
    difficulty = re.search(re_difficulty, subTitle)
    if not difficulty:
        raise Exception(fg.yellow + "couldn't parse difficulty" + fg.rs)
    accuracy = re.search(re_accuracy, subTitle.replace(",", "."))
    if not accuracy and not re.search(re_ss, subTitle):
        raise Exception(fg.yellow + "couldn't parse accuracy" + fg.rs)

    parsed = {
        "username": username.group().split("(")[0].strip(),
        "artist": artist.group().strip(),
        "title": title.group().strip(),
        "difficulty": difficulty.group().strip(),
        "accuracy": "100.00" if not accuracy else accuracy.group().replace("%", ""),
    }
    return parsed


def find_score(parsed):
    access_token = get_access_token()
    if not access_token:
        raise Exception(fg.yellow + "couldn't get access token" + fg.rs)
    log(fg.green + "Got access token" + fg.rs)
    try:
        userID = requests.get(
            "https://osu.ppy.sh/api/v2/users/" + parsed["username"] + "/osu?key=username",
            headers={"Authorization": "Bearer " + access_token},
        ).json()["id"]
    except:
        raise Exception(fg.yellow + "couldn't find the player with that username" + fg.rs)

    scores = requests.get(
        "https://osu.ppy.sh/api/v2/users/" + str(userID) + "/scores/recent?limit=100",
        headers={"Authorization": "Bearer " + access_token},
    ).json()

    filtered = [
        score
        for score in scores
        if score["id"] == score["best_id"]
        and score["beatmapset"]["title"] == parsed["title"]
        and score["beatmapset"]["artist"] == parsed["artist"]
        and score["beatmap"]["version"] == parsed["difficulty"]
        and round(score["accuracy"] * 100, 2) == float(parsed["accuracy"])
    ]
    if len(filtered) > 1 or len(filtered) == 0:
        raise Exception(fg.yellow + "couldn't find the exact score" + fg.rs)
    return filtered[0], access_token


def get_access_token():  # using lazer access token as it doesn't require user input
    if not os.environ.get("EXPIRE_AT") or time() > float(os.environ["EXPIRE_AT"]):
        res = requests.post(
            "https://osu.ppy.sh/oauth/token",
            data={
                "client_id": "5",
                "client_secret": "FGc9GAtyHzeQDshWP5Ah7dega8hJACAJpQtw6OXk",
                "username": os.environ["LAZER_USERNAME"],
                "password": os.environ["LAZER_PASSWORD"],
                "grant_type": "password",
                "scope": "*",
            },
        ).json()
        os.environ["BANCHO_ACCESS_TOKEN"] = res["access_token"]
        os.environ["EXPIRE_AT"] = str(time() + 86000)
        return res["access_token"]
    return os.environ["BANCHO_ACCESS_TOKEN"]


def replay_download(access_token, score):
    # if score["replay"] == False:
    #     raise Exception(fg.yellow + "The replay isn't available for score" + fg.blue, score["id"], fg.rs)
    base_url = "https://osu.ppy.sh/api/v2/scores/"
    if score["type"] == "score_best_osu":
        base_url += "osu/"
    res = requests.get(
        base_url + str(score["id"]) + "/download",
        headers={
            "Accept": "application/octet-stream",
            "Content-Type": "application/octet-stream",
            "Authorization": "Bearer " + access_token,
        },
    )
    if res.status_code == 404:
        raise Exception(fg.yellow + "The replay isn't available for score" + fg.blue, score["id"], fg.rs)
    return res.content


def ordr_post(replay, score_info):
    config = {
        "username": os.environ["RENDER_USERNAME"],
        "resolution": "1280x720",
        "inGameBGDim": "90",
        "showHitCounter": "true",
        "showAimErrorMeter": "true",
        "showScoreboard": "true",
        "showStrainGraph": "true",
        "showSliderBreaks": "true",
        "verificationKey": os.environ["RENDER_API_KEY"],
    }

    if "EZ" in score_info["mods"]:
        config.update({"customSkin": "true", "skin": "11704", "useBeatmapColors": "false", "useSkinColors": "true"})
        log(fg.blue + "Using EZ skin" + fg.rs)
    elif ("DT" in score_info["mods"] or "NC" in score_info["mods"]) and score_info["beatmap"]["ar"] >= 9.0:
        config.update({"customSkin": "true", "skin": "11683", "useBeatmapColors": "false", "useSkinColors": "true"})
        log(fg.blue + "Using DT skin" + fg.rs)
    else:
        config.update({"skin": "FreedomDiveBTMC"})
        log(fg.blue + "Using NM skin" + fg.rs)

    res = requests.post(
        "https://apis.issou.best/ordr/renders",
        data=config,
        files={"replayFile": ("replay.osr", replay)},
    ).json()
    return res["renderID"]


def reply(score):
    for submission in score["submissions"]:
        try:
            submission.reply(
                "[**replay**]({videoUrl})\n\n---\n  ^(rendered by [o!rdr](https://ordr.issou.best/) | [Report issues](https://www.reddit.com/message/compose?to=u/allehS&subject={submission_id}:{score_id}:{render_id}) | [Source](https://github.com/shellawa/r-osugame-replay))".format(
                    videoUrl=score["videoUrl"],
                    submission_id=submission.id,
                    score_id=score["score_info"]["id"],
                    render_id=score["videoUrl"].split("/")[-1],
                )
            )
        except:
            log(fg.red + "Error: " + fg.yellow + "could't reply to the post" + fg.rs)
            return
        log(fg.green + "Replied to " + submission.id + fg.rs)
