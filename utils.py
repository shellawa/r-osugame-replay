from time import time
import os
import requests


def get_access_token():
    if not os.environ.get("EXPIRE_AT") or time() > float(os.environ["EXPIRE_AT"]):
        res = requests.post(
            "https://osu.ppy.sh/oauth/token",
            data={
                "client_id": os.environ["BANCHO_CLIENT_ID"],
                "client_secret": os.environ["BANCHO_CLIENT_SECRET"],
                "grant_type": "client_credentials",
                "scope": "public",
            },
        ).json()
        os.environ["BANCHO_ACCESS_TOKEN"] = res["access_token"]
        os.environ["EXPIRE_AT"] = str(time() + 86000)
        return res["access_token"]
    return os.environ["BANCHO_ACCESS_TOKEN"]
