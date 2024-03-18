from time import time
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
    try:
        requests.post(
            url=os.environ["WEBHOOK_LINK"],
            json={"content": " ".join(args), "username": "allehS"},
        )
    except Exception:
        pass


def parse_submission(submission_title):
    username = re.search(re_username, submission_title)
    if not username:
        raise Exception("couldn't parse username")
    artist = re.search(re_artist, submission_title)
    if not artist:
        raise Exception("couldn't parse artist")
    title = re.search(re_title, submission_title)
    if not title:
        raise Exception("couldn't parse title")
    difficulty = re.search(
        re_difficulty, submission_title.replace(username.group(), "")
    )
    if not difficulty:
        raise Exception("couldn't parse difficulty")
    accuracy = re.search(re_accuracy, submission_title.replace(",", "."))
    if not accuracy and not re.search(re_ss, submission_title):
        raise Exception("couldn't parse accuracy")

    parsed = {
        "username": username.group().split("(")[0].strip(),
        "artist": artist.group().strip(),
        "title": title.group().strip(),
        "difficulty": difficulty.group().strip(),
        "accuracy": "100.00" if not accuracy else accuracy.group().replace("%", ""),
    }
    return parsed


def find_score(parsed, access_token):
    try:
        userID = requests.get(
            url=f"https://osu.ppy.sh/api/v2/users/{parsed['username']}/osu?key=username",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()["id"]
    except Exception:
        raise Exception("couldn't find the player with that username")

    scores = requests.get(
        url=f"https://osu.ppy.sh/api/v2/users/{userID}/scores/recent?limit=100",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    filtered = [
        score
        for score in scores
        if score["replay"]
        and score["beatmapset"]["title"] == parsed["title"]
        and score["beatmapset"]["artist"] == parsed["artist"]
        and score["beatmap"]["version"] == parsed["difficulty"]
        and round(score["accuracy"] * 100, 2) == float(parsed["accuracy"])
    ]
    if len(filtered) != 1:
        raise Exception("couldn't find the exact score")
    return filtered[0]


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
    res = requests.get(
        url=f"https://osu.ppy.sh/api/v2/scores/osu/{score['id']}/download",
        headers={
            "Accept": "application/octet-stream",
            "Content-Type": "application/octet-stream",
            "Authorization": f"Bearer {access_token}",
        },
    )
    if res.status_code != 200:
        raise Exception(f"Couldn't download replay {score['id']}")
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
        config.update(
            {
                "customSkin": "true",
                "skin": "11704",
                "useBeatmapColors": "false",
                "useSkinColors": "true",
            }
        )
        log("Using EZ skin")
    elif (score_info["beatmap"]["ar"] >= 9.0) and (
        "DT" in score_info["mods"] or "NC" in score_info["mods"]
    ):
        config.update(
            {
                "customSkin": "true",
                "skin": "11683",
                "useBeatmapColors": "false",
                "useSkinColors": "true",
            }
        )
        log("Using DT skin")
    else:
        config.update({"skin": "FreedomDiveBTMC"})
        log("Using NM skin")

    try:
        res = requests.post(
            url="https://apis.issou.best/ordr/renders",
            data=config,
            files={"replayFile": ("replay.osr", replay)},
        ).json()
        return res["renderID"]
    except Exception:
        raise Exception("Couldn't post replay to o!rdr")


def reply(scorepost, score):
    try:
        scorepost.reply(
            f"[**replay**]({score['render_url']})\n\n---\n  ^(rendered by [o!rdr](https://ordr.issou.best/) | [Report issues](https://www.reddit.com/message/compose?to=u/allehS&subject={scorepost.id}:{score['score_id']}:{score['render_url']}))"
        )
    except Exception:
        raise Exception(f"Couldn't reply to {scorepost.id}")
    return True
