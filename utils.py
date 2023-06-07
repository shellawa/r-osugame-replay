from time import time
import os
import requests
import re

re_username = re.compile("^[^ | ]+")
re_artist = re.compile("(?<= \| )(.*?)(?= \- )")
re_title = re.compile("(?<= \- )(.*?)(?=\[)")
re_difficulty = re.compile("(?<=\[)(.*?)(?=\])")
re_creator = re.compile("(?<=] \()(.*?)(?=,|\|)")
re_accuracy = re.compile("(?<=\s)\S+(?=\%)")
re_ss = re.compile(" ss ", re.IGNORECASE)


def parse_submission(subTitle, access_token):
    username = re.search(re_username, subTitle)
    if not username:
        return
    artist = re.search(re_artist, subTitle)
    if not artist:
        return
    title = re.search(re_title, subTitle)
    if not title:
        return
    difficulty = re.search(re_difficulty, subTitle)
    if not difficulty:
        return
    accuracy = re.search(re_accuracy, subTitle)
    if not accuracy and not re.search(re_ss, subTitle):
        return

    parsed = {
        "username": username.group().strip(),
        "artist": artist.group().strip(),
        "title": title.group().strip(),
        "difficulty": difficulty.group().strip(),
        "accuracy": "100.00" if not accuracy else accuracy.group(),
    }

    userID = requests.get(
        "https://osu.ppy.sh/api/v2/users/" + parsed["username"] + "/osu?key=username",
        headers={"Authorization": "Bearer " + access_token},
    ).json()["id"]

    scores = requests.get(
        "https://osu.ppy.sh/api/v2/users/" + str(userID) + "/scores/recent?limit=100",
        headers={"Authorization": "Bearer " + access_token},
    ).json()

    filtered = [
        score["best_id"]
        for score in scores
        if score["replay"] == True
        and score["beatmapset"]["title"] == parsed["title"]
        and score["beatmapset"]["artist"] == parsed["artist"]
        and score["beatmap"]["version"] == parsed["difficulty"]
        and round(score["accuracy"] * 100, 2) == float(parsed["accuracy"])
    ]
    if len(filtered) > 1 or len(filtered) == 0:
        return
    return str(filtered[0])


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


def replay_download(access_token, scoreID):
    res = requests.get(
        "https://osu.ppy.sh/api/v2/scores/osu/" + scoreID + "/download",
        headers={
            "Accept": "application/octet-stream",
            "Content-Type": "application/octet-stream",
            "Authorization": "Bearer " + access_token,
        },
    )
    return res.content


def ordr_post(replay):
    res = requests.post(
        "https://apis.issou.best/ordr/renders",
        data={
            "username": "shellawa",
            "resolution": "1280x720",
            "skin": "whitecatCK1.0",
            "verificationKey": "devmode_success",
        },
        files={"replayFile": ("replay.osr", replay)},
    ).json()
    return res["renderID"]
