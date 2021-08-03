from discord.ext import commands
from datetime import datetime, time, timedelta
import asyncio
import schedule
import live_updates
import match_graphics
import messages
import utils
import globals as g
from loguru import logger
from secrets import discord_token

logger.add("bot_log.log")
client = commands.Bot(command_prefix='!')
IS_TESTING = True
FIRST = True

@client.event
async def on_ready():
    global FIRST
    if FIRST:
        FIRST = False
        logger.info('Bot is ready')
        await client.wait_until_ready()

        if IS_TESTING:
            guild = next(guild for guild in client.guilds if guild.name == 'Annes server')
        else:
            guild = next(guild for guild in client.guilds if guild.name == 'Astralis')
        logger.info(f'Guild: {guild}')
        g.initialise_globals(guild)
        schedule.update_schedules()

        client.loop.create_task(background_task_hourly())
        client.loop.create_task(background_task_daily())

@client.command()
async def update(ctx):
    is_monday = datetime.today().weekday() == 0
    changed_matches = await schedule.check_schedule_daily(g.CHANNELS.SCHEDULE, is_monday)
    if len(changed_matches) > 0:
        await generate_for_new(is_monday, changed_matches)
    else:
        await ctx.send("No updates found to the schedule")

@client.command()
async def give_me_graphics(ctx):
    matches = schedule.CSGO_SCHEDULE + schedule.LOL_SCHEDULE
    if len(matches) > 0:
        await generate_for_new(False, matches)
    else:
        await ctx.send("No matches this week")

async def background_task_hourly():
    # Sleep until next whole hour
    await asyncio.sleep(next_hour())
    while True:
        # Checks if schedule has changed. If monday post new schedule for week
        is_monday = datetime.today().weekday() == 0
        changed_matches = await schedule.check_schedule_daily(g.CHANNELS.SCHEDULE, is_monday)

        # If monday or the schedule has changed post match graphics to com coords channel
        if changed_matches:
            changed_matches = list(filter(lambda match: ('Astralis Talent' not in match['name']), changed_matches))
            if changed_matches:
                await generate_for_new(is_monday, changed_matches)

        await asyncio.sleep(next_hour())

def next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
    wait_seconds = (next_hour - now).seconds
    return wait_seconds

async def generate_for_new(is_monday, changed_matches):
    csgo_matches = list(filter(lambda match: (utils.get_videogame_type(match) == 'csgo'), changed_matches))
    csgo_matches = match_graphics.create_graphics_for_match(csgo_matches) if csgo_matches else []
    
    lol_matches = list(filter(lambda match: (utils.get_videogame_type(match) == 'lol'), changed_matches))
    lol_matches = match_graphics.create_graphics_for_match(lol_matches) if lol_matches else []
    
    text = messages.get_match_graphics_text(csgo_matches, lol_matches, is_monday)
    await g.CHANNELS.COMCOORDS.send(text)


async def background_task_daily():
    now = datetime.now()
    EIGHT_CEST = time(6, 0, 0)  # 6:00 GMT 8:00 CEST
    if now.time() > EIGHT_CEST:
        # Sleep until tomorrow and then the loop will start
        await asyncio.sleep((datetime.combine(now.date() + timedelta(days=1), time(0)) - now).total_seconds())
    while True:
        now = datetime.now()
        # Sleep until we hit the target time
        await asyncio.sleep((datetime.combine(now.date(), EIGHT_CEST) - now).total_seconds())
        # If any matches today, being live updates.
        matches_today = [match for match in schedule.CSGO_SCHEDULE + schedule.LOL_SCHEDULE if datetime.strptime(
            match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ').date() == now.date()]
        if matches_today:
            for match in matches_today:
                logger.info(f"Match today at {match['scheduled_at']} vs {match['opponent']}")
                asyncio.get_event_loop().create_task(live_updates.update_live_for_match(match))
        # Sleep until tomorrow and then the loop will start a new iteration
        await asyncio.sleep((datetime.combine(now.date() + timedelta(days=1), time(0)) - now).total_seconds())

if __name__ == "__main__":
    client.run(discord_token)
