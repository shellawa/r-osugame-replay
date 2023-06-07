# **r-osugame-replay**
## Description
This is a reddit bot for subreddit [r/osugame](https://reddit.com/r/osugame) on reddit. It will reply to scoreposts with a replay video rendered on [o!rdr](https://ordr.issou.best/). (Only if the replay is available on bancho).\
The bot uses lazer login credentials to communicate with osu!apiV2.\
It might break sometimes but idk
## Usage
```
python main.py
```
## .envexample
```
CLIENT_ID=<Your Reddit OAuth client id>
CLIENT_SECRET=<Your reddit OAuth client secret>
USERNAME=<Your Reddit username>
PASSWORD=<Your Reddit password>

LAZER_USERNAME=<Your osu!lazer username>
LAZER_PASSWORD=<Your osu!lazer password>
```