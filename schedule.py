from datetime import datetime
from PIL import Image, ImageFont, ImageDraw
import discord
from messages import get_schedule_header_footer, get_schedule_message_for_type
from utils import get_videogame_type, teamnames, get_matches_by_type, get_match_cet_time
from loguru import logger
from itertools import groupby


logger.add("bot_log.log")
CSGO_SCHEDULE = []
CSGO_TALENT_SCHEDULE = []
LOL_SCHEDULE = []

sched_coords = {
    'text': {
        'csgo': (250, 425),
        'talent': (250, 825),
        'lol': (1110, 425)
    },
    'date': {
        'csgo': (770, 425),
        'talent': (770, 825),
        'lol': (1610, 425)
    },
}


async def check_schedule_daily(channel, is_monday):
    logger.info('Checking if schedules have changed')
    # Checks for changes and updates schedule
    changed_matches = schedules_have_changed()
    logger.info(f'Is monday: {is_monday}')
    logger.info(f'Num changed: {len(changed_matches)}')
    if not changed_matches:
        logger.info("Does not send new schedule")
        return []

    get_schedule_picture()
    schedule_text = get_schedule_message()
    logger.info(f'Purging channel: {channel}')
    await channel.purge()
    # Send text and image
    logger.info(f'Sending schedule to channel: {channel}')
    await channel.send(schedule_text, file=discord.File('Graphics/schedule.png'))
    if not is_monday:
        update_text = "**The schedule has been updated** \n"
        for reason, matches in groupby(changed_matches, lambda x: x['update_reason']):
            update_text += f'\n*Update ({reason}):*\n'
            update_text += "".join([f"Astralis vs {match['opponent']}\n" for match in list(matches)])
        await channel.send(update_text)
    return changed_matches


def get_schedule_picture():
    img = Image.open("Graphics/background.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("Fonts/RiformaLL-Medium.otf", 35)

    def match_text(match): return f"VS {match['opponent']}"
    def match_date(match): return f"{get_match_cet_time(match).strftime('%b %-d - %H:%M')} "
    def text_format(schedule): return '\n\n'.join([match_text(match) for match in schedule]) if schedule else 'No games this week'
    def date_format(schedule): return '\n\n'.join([match_date(match)for match in schedule]) if schedule else ''

    for type, schedule in [('csgo', CSGO_SCHEDULE), ('talent', CSGO_TALENT_SCHEDULE), ('lol', LOL_SCHEDULE)]:
        text = text_format(schedule)
        dates = date_format(schedule)
        draw.text(sched_coords['text'][type], text, (255, 255, 255), font=font)
        draw.text(sched_coords['date'][type], dates, (255, 255, 255), font=font)

    img.save('Graphics/schedule.png')


def get_schedule_message():
    sched_header, sched_footer = get_schedule_header_footer()
    schedule_message = sched_header
    schedule_message += get_schedule_message_for_type(CSGO_SCHEDULE, 'csgo') + '\n'
    schedule_message += get_schedule_message_for_type(CSGO_TALENT_SCHEDULE, 'talent') + '\n'
    schedule_message += get_schedule_message_for_type(LOL_SCHEDULE, 'lol') + '\n'
    schedule_message += sched_footer
    return schedule_message


def schedules_have_changed():
    current_csgo = CSGO_SCHEDULE
    current_csgo_talent = CSGO_TALENT_SCHEDULE
    current_lol = LOL_SCHEDULE
    update_schedules()

    new_sched = CSGO_SCHEDULE + CSGO_TALENT_SCHEDULE + LOL_SCHEDULE
    old_sched = current_csgo + current_csgo_talent + current_lol
    changed_matches = [m for m in new_sched if not any(m['slug'] == y['slug'] for y in old_sched)]
    for match in changed_matches:
        match['update_reason'] = 'New match'
    
    # If any scheduled time has changed or new opponent
    for cur in old_sched:
        new = next((m for m in new_sched if m['slug'] == cur['slug']), None)
        if new == None:
            continue 
        # If scheduled time has changed, but disregard matches already played
        if cur['opponent'] != new['opponent']:
            logger.info(f'Found new opponent for match: {new["name"]}')
            new['update_reason'] = 'New opponent'
            changed_matches.append(new)
        elif cur['scheduled_at'] != new['scheduled_at'] and datetime.strptime(new['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ') >= datetime.today():
            logger.info(f'Found new scheduled match time for match: {new["name"]}')
            new['update_reason'] = 'New time'
            changed_matches.append(new)
    
    return changed_matches


def update_schedules(types=['csgo', 'lol']):
    global CSGO_SCHEDULE, CSGO_TALENT_SCHEDULE, LOL_SCHEDULE
    for type in types:
        upcoming = get_matches_by_type(type)
        if type == 'csgo':
            # Divide into talent and not talent
            CSGO_TALENT_SCHEDULE = [match for match in upcoming if teamnames['talent'] in match['name']]
            CSGO_SCHEDULE = [match for match in upcoming if teamnames['talent'] not in match['name']]
            logger.info(f'Found {len(CSGO_SCHEDULE)} CSGO matches')
            logger.info(f'Found {len(CSGO_TALENT_SCHEDULE)} CSGO Talent matches')
        elif type == 'lol':
            LOL_SCHEDULE = upcoming
            logger.info(f'Found {len(LOL_SCHEDULE)} LOL matches')