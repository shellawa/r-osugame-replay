from time import time
import os
import requests


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
        "https://osu.ppy.sh/api/v2/scores/osu/" + str(scoreID) + "/download",
        headers={
            "Accept": "application/octet-stream",
            "Content-Type": "application/octet-stream",
            "Authorization": "Bearer " + access_token,
        },
    )
    return res.content
