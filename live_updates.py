import globals as g
import discord
import tweepy
import asyncio
from datetime import datetime, timedelta
from messages import get_match_starts_message, get_match_score_update_message, get_match_end_text
from utils import get_match_by_id, get_videogame_type
import os
from loguru import logger
from secrets import consumer_key, consumer_secret

logger.add("bot_log.log")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

'''
    Checks if the match is rescheduled.
    If so wait until new start time, then check again if match is started
    If not return status
'''
async def wait_for_real_start(match):
    updated_match = get_match_by_id(match)
    scheduled_at = datetime.strptime(updated_match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(minutes=5)
    logger.info(f"Match {match['name']} is scheduled at {scheduled_at}")

    # If match has started
    if updated_match['status'] == 'running':
        logger.info(f"{match['name']} has started")
        return updated_match

    # If current time is greater than scheduled, but match has not started.
    # Check again in 1 min if time is past scheduled time
    if datetime.now() > scheduled_at:
        logger.info(f"Waiting another minute for {match['name']}")
        await asyncio.sleep(60)
        return await wait_for_real_start(updated_match)
    # If new scheduled time is in the future, sleep until then
    else:
        logger.info(f"Waiting until {scheduled_at} for {match['name']}")
        await asyncio.sleep((scheduled_at - datetime.now()).total_seconds())
        return await wait_for_real_start(updated_match)

async def update_live_for_match(match):
    type = get_videogame_type(match)
    channel = g.CHANNELS.CSGO_LIVE if type == 'csgo' else g.CHANNELS.LOL_LIVE
    # Sleep until 15 min before match start (in case match starts early)
    scheduled_at = datetime.strptime(match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(minutes=15)
    if datetime.now() < scheduled_at:
        logger.info(f"Waiting until {scheduled_at} for {match['name']} to start")
        await asyncio.sleep((scheduled_at - datetime.now()).total_seconds())
    match = await wait_for_real_start(match)
    status = match['status']

    logger.info(f"{channel}: purge and notify match has started, allow sending messages, edit name")
    # Purge channel then notify that match has started
    await channel.purge(limit=10000, bulk=True)
    await channel.send(get_match_starts_message(match), file=discord.File('Graphics/were_live.png'))
    await channel.set_permissions(g.ROLES.EVERYONE, read_messages=True, send_messages=True)
    channelname = channel.name
    await channel.edit(name = f"{channelname}-vs-{match['opponent']}")

    latest_tweet = get_latest_tweet(type)
    tweets_sent = []
    score = []
    # While match is on
    while status == 'running':
        # Get for new tweets and match updates
        new_tweet = get_latest_tweet(type)
        match = get_match_by_id(match)
        status = match['status']
        new_score = match['results']

        # If the score has changed, but don't include 0-0
        if score != new_score and any(team['score'] != 0 for team in new_score):
            score = new_score
            text, img_path = get_match_score_update_message(match)
            logger.info(f"Sending score update")
            await channel.send(text, file=discord.File(img_path, spoiler=True))
            os.remove(img_path)

        if latest_tweet != new_tweet and new_tweet not in tweets_sent:
            tweets_sent.append(new_tweet)
            latest_tweet = new_tweet
            username = 'AstralisCS' if type == 'csgo' else 'AstralisLOL'
            text = f"Hey everybody, **{username}** just posted a new tweet!\n" + latest_tweet
            logger.info(f"Sending new tweet: {latest_tweet}")
            await channel.send(text)

        # Wait 10 sec before checking for new tweets and match updates again
        await asyncio.sleep((10))

    await channel.send(get_match_end_text(match))
    # Wait an hour
    logger.info(f"Waiting an hour then: disallow sending messages, edit name of {channel}")
    await asyncio.sleep((3600))
    logger.info(f"{channel}: disallow sending messages and edit name")
    await channel.set_permissions(g.ROLES.EVERYONE, read_messages=True, send_messages=False)
    logger.info(f"Variable channelname is {channelname}")
    await channel.edit(name = f"{channelname}")


def get_latest_tweet(type):
    username = 'AstralisCS' if type == 'csgo' else 'AstralisLOL'
    base_url = f'https://twitter.com/{username}/status/'
    tweet = next(tweepy.Cursor(api.user_timeline, id=username, exclude_replies=True, include_rts=False).items(1))
    return base_url + tweet.id_str


if __name__ == "__main__":
    get_latest_tweet()
