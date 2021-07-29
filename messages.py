from datetime import datetime
import globals as g
from utils import get_videogame_type, get_week_info, get_match_cet_time
from PIL import Image, ImageFont, ImageDraw
import random
import os
import uuid
from dadjokes import Dadjoke
import json
dadjoke = Dadjoke()

def get_schedule_header_footer():
    week_number, week_start, week_end = get_week_info()
    sched_header = f"**{g.EMOJIS.ASTRALIS}  Schedule week {week_number} for Astralis Esport {week_start.strftime('%B %-d')} - {week_end.strftime('%B %-d')}  {g.EMOJIS.ASTRALIS}** \n\n"
    sched_footer = f"See the full schedule here :point_down_tone2: \n<https://astralis.gg/schedule>"
    return sched_header, sched_footer


def get_schedule_message_for_type(sched, type):
    message = ''
    type_emoji = g.EMOJIS.CSGO if type == 'csgo' or type == 'talent' else g.EMOJIS.LOL
    type_header = 'Counter Strike: Global Offensive' if type == 'csgo' else 'League of Legends' if type == 'lol' else 'CS:GO - Astralis Talent'
    type_channel = f'- <#{g.CHANNELS.CSGO.id}>' if type == 'csgo' else f'- <#{g.CHANNELS.LOL.id}>' if type == 'lol' else ''
    message += f"{type_emoji} **__{type_header}__** {type_channel}\n\n"
    if not sched:
        message += f"{type_emoji} No games this week. \n"
    else:
        event = sched[0]['league']['name'] + ' ' + sched[0]['serie']['full_name']
        message += f"**{event}** \n"
        for match in sched:
            scheduled = get_match_cet_time(match).strftime('%b %-d - %H:%M')
            match_text = f"{type_emoji} VS {match['opponent']} on {scheduled}"
            if datetime.strptime(match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ').date() < datetime.now().date():
                match_text = f"~~{match_text}~~"
            message += f"{match_text}\n"
    return message

def get_match_starts_message(match):
    type = get_videogame_type(match)
    type_channel = g.CHANNELS.CSGO_LIVE.id if type == 'csgo' else g.CHANNELS.LOL_LIVE.id
    type_role_id = g.ROLES.CSGO.id if type == 'csgo' else g.ROLES.LOL.id
    return f"""<@&{type_role_id}>
    
{g.EMOJIS.ASTRALIS}We're going live against {match['opponent']}. The live discussion is now open at <#{type_channel}>. Come cheer with the other fans.{g.EMOJIS.ASTRALIS}
    
:point_down: 

:tv: <{match['official_stream_url']}>"""

def get_match_score_update_message(match):
    type = get_videogame_type(match)
    if match['status'] == 'finished':
        text = 'The match has ended! Click the spoiler to show the result'
    else:
        text = 'The score has been updated! Click the spoiler to show the result'
    team_id = g.type2pandaid[type]
    ast_score = next(result['score'] for result in match['results'] if result['team_id'] == team_id)
    other_score = next(result['score'] for result in match['results'] if result['team_id'] != team_id)
    line = f'{str(ast_score)} - {str(other_score)}'
    opponent = f"{match['opponent']}".upper()
    path = f"Graphics/{type}/score"
    img_path = f'{path}/ahead' if ast_score > other_score else f'{path}/behind' if ast_score < other_score else f'{path}/equal'
    to_path = f"temp/{str(uuid.uuid4())}.png"
    pic = random.choice(os.listdir(img_path))
    img = Image.open(f"{img_path}/{pic}")
    
    draw = ImageDraw.Draw(img)
    font_little = ImageFont.truetype("Fonts/RiformaLL-Bold.otf", 126)
    font_big = ImageFont.truetype("Fonts/RiformaLL-Bold.otf", 200)

    draw.text((40, 110), line, (255, 255, 255), font=font_big)
    draw.text((40, 625), opponent, (255, 255, 255), font=font_little)

    img.save(to_path)
    
    return text, to_path

def get_match_end_text(match):
    is_ast_win = match['winner_id'] == g.type2pandaid[get_videogame_type(match)]
    end_text = f"The match has ended. This channel will remain open for an hour. "
    if is_ast_win:
        end_text += "Celebrate the victory with the other fans. "
    else:
        end_text += "Spend the time discussing the game with the other fans. "
    end_text += "See you at the next match. "
    return end_text

def get_match_graphics_text(csgo_urls, lol_urls, is_monday):
    joke = dadjoke.joke
    csgo_urls = "".join([f"{g.EMOJIS.CSGO} VS {opponent} {url} \n" for opponent, url in csgo_urls.items()]) if csgo_urls else ""
    lol_urls = "".join([f"{g.EMOJIS.LOL} VS {opponent} {url} \n" for opponent, url in lol_urls.items()]) if lol_urls else ""
    text = f"On a serious note, <@&{g.ROLES.COMCOORDS.id}> & <@&{g.ROLES.SOME.id}>; "
    if is_monday:
        text += f"Match Graphics for this weeks games are now up! Download them here:"
    else:
        text += f"There's an update to the match graphics for this week! Download it here:"
    return f"{joke}\n\n{text}\n\n{csgo_urls}{lol_urls}\nIf you find any issues with the match graphics, please let Nicolaj know. "