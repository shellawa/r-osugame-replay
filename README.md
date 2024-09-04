# Archived in favor of [u/osu-bot](https://github.com/christopher-dG/osu-bot)

# **r-osugame-replay**

## Description

This is a reddit bot for subreddit [r/osugame](https://reddit.com/r/osugame) on reddit. It will reply to scoreposts with a replay video rendered on [o!rdr](https://ordr.issou.best/). (Only if the replay is available on bancho).\
The bot uses lazer login credentials to communicate with osu!apiV2.\
It might break sometimes but idk

## Requirement

Python

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
USER_AGENT=<User agent used with praw>
SUBREDDIT=<The subreddit which the bot is listening to>

LAZER_USERNAME=<Your osu!lazer username>
LAZER_PASSWORD=<Your osu!lazer password>

RENDER_USERNAME=<o!rdr display name>
RENDER_API_KEY=<o!rdr api key>
```
