from datetime import datetime
import os
import random
from PIL import Image, ImageFont, ImageDraw
from utils import get_match_cet_time
import pytz
import shutil
import globals as g
import dropbox
import re
from utils import get_videogame_type
from loguru import logger
from secrets import dropbox_token

logger.add("bot_log.log")
d = dropbox.Dropbox(dropbox_token)

# Coordinates: (text, time, date) (from left, from top)
pre_match = {
    'coords': {
        'instagram': [(45, 1332), (45, 376), (45, 305)],
        'twitter': [(1065, 662), (1065, 163), (1065, 93)],
        'facebook': [(40, 992), (40, 163), (40, 93)]
    },
    'font_size': {
        'instagram': [125, 60],
        'twitter': [105, 60],
        'facebook': [95, 60]
    },
}

post_match = {
    'coords': {
        'instagram': (45, 1323),
        'twitter': (40, 625),
        'facebook': (40, 988)
    },
    'font_size': {
        'instagram': 125,
        'twitter': 120,
        'facebook': 95
    },
}

world_map = {
    # Date, Opponent, First time
    'coords': [(40, 95), (40, 597), (1030, 42)],
    'font_size': [60, 85, 67]
}

mvp = {
    # Name
    'coords': (40, 269),
    'font_size': 70
}


def get_font(size): return ImageFont.truetype("Fonts/RiformaLL-Bold.otf", size)

def create_graphics_for_match(sched):
    dl_urls = {}
    for match in sched:
        logger.info(f"Creating graphics for {match['name']}")
        type = get_videogame_type(match)
        if match['opponent'] == 'TBD':
            return

        match_folder = f"temp/{match['opponent']}"
        os.mkdir(match_folder)
        edit_timezone_pic(match, type, match_folder)
        if type == 'lol':
            edit_mvp_pics(match, type, match_folder)
        edit_pre_post_pics(match, type, match_folder)
        dl_url = upload_to_dropbox(f"{type}-{match['opponent']}", match_folder)
        if dl_url != None: dl_urls[match['opponent']] = dl_url

    global used_vic, used_def, used_pre
    used_vic = []
    used_def = []
    used_pre = []

    return dl_urls

def upload_to_dropbox(folder_name, folder_path):
    # Create ZIP
    shutil.make_archive(folder_path, 'zip', folder_path)
    # Upload to dropbox
    d.files_upload(open(f'{folder_path}.zip', 'rb').read(
    ), f'/{folder_name}.zip', mode=dropbox.files.WriteMode("overwrite"))
    url = d.sharing_create_shared_link(f'/{folder_name}.zip').url
    # link which directly downloads by replacing ?dl=0 with ?dl=1
    dl_url = re.sub(r"\?dl\=0", "?dl=1", url)
    # Delete folders
    shutil.rmtree(folder_path)
    os.remove(f'{folder_path}.zip')
    return dl_url

used_vic = []
used_def = []
used_pre = []
def edit_pre_post_pics(match, type, match_folder):
    # Get random post-match and pre-match folder
    post_match_path = f'Graphics/{type}/post_match'
    pre_match_path = f'Graphics/{type}/pre_match'
    # Choose a random img, that is not the same as last time
    rand_vic = random.choice([player for player in os.listdir(post_match_path) if player not in used_vic])
    rand_def = random.choice([player for player in os.listdir(post_match_path) if player not in used_def and player != rand_vic and player != 'promisq' and player != 'bubzkji'])
    rand_pre = random.choice([img for img in os.listdir(pre_match_path) if img not in used_pre])
    global used_vic, used_def, used_pre
    used_vic.append(rand_vic) 
    used_def.append(rand_def)
    used_pre.append(rand_pre)

    get_imgs = lambda path : [f'{path}/{img}' for img in os.listdir(path)]
    victory_imgs = random.choice([f'{post_match_path}/{rand_vic}/{vic}' for vic in os.listdir(f'{post_match_path}/{rand_vic}') if 'victory' in vic])
    victory_imgs = get_imgs(victory_imgs)
    defeat_imgs = random.choice([f'{post_match_path}/{rand_def}/{defeat}' for defeat in os.listdir(f'{post_match_path}/{rand_def}') if 'defeat' in defeat])
    defeat_imgs = get_imgs(defeat_imgs)
    pre_match_imgs = get_imgs(f'{pre_match_path}/{rand_pre}')

    # Edit and save pictures
    for img_path in victory_imgs + defeat_imgs:
        edit_pic(match, img_path, match_folder, 'post_match')
    for img_path in pre_match_imgs:
        edit_pic(match, img_path, match_folder, 'pre_match')

def edit_pic(match, img_path, match_folder, type):
    img_name = img_path.split('/')[-1]
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    social_media = img_name.split('_')[1].split('.')[0]
    opponent = match['opponent'].upper()
    coords = pre_match['coords'][social_media] if type == 'pre_match' else post_match['coords'][social_media]
    font_size = pre_match['font_size'][social_media] if type == 'pre_match' else post_match['font_size'][social_media]
    save_path = f"{match_folder}/{img_name}"

    if type == 'pre_match':
        scheduled_at = get_match_cet_time(match)
        time = scheduled_at.strftime('%H:%M %Z')
        date = scheduled_at.strftime('%B %-d')
        draw.text(coords[0], opponent, (255, 255, 255),font=get_font(font_size[0]))
        draw.text(coords[1], time, (255, 255, 255), font=get_font(font_size[1]))
        draw.text(coords[2], date, (255, 255, 255), font=get_font(font_size[1]))
    elif type == 'post_match':
        draw.text(coords, opponent, (255, 255, 255), font=get_font(font_size))
    
    img.save(save_path)

def edit_timezone_pic(match, type, match_folder):
    path = f"Graphics/{type}/world_map_time.png"
    img = Image.open(path)
    coords = world_map['coords']
    font_size = world_map['font_size']
    timezones = ['America/Los_Angeles', 'America/New_York', 'America/Sao_Paulo', 'Africa/Abidjan', 'Europe/London',
                 'Europe/Copenhagen', 'Europe/Moscow', 'Asia/Kolkata', 'Asia/Bangkok', 'Asia/Shanghai', 'Asia/Tokyo', 'Australia/Sydney']

    opponent = match['opponent'].upper()
    scheduled_at = datetime.strptime(match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ')
    date = scheduled_at.strftime('%B %-d')

    draw = ImageDraw.Draw(img)
    draw.text(coords[0], date, (255, 255, 255), font=get_font(font_size[0]))
    draw.text(coords[1], opponent, (255, 255, 255), font=get_font(font_size[1]))
    start_coords = coords[2]
    for timezone in timezones:
        time = pytz.utc.localize(scheduled_at).astimezone(pytz.timezone(timezone))
        time_str = time.strftime('%H:%M')
        draw.text(start_coords, time_str, (255, 255, 255), font=get_font(font_size[2]))
        start_coords = (start_coords[0], start_coords[1] + 86)

    img.save(f"{match_folder}/world_map_time.png")

def edit_mvp_pics(match, type, match_folder):
    # Create destination dir
    to_folder = f'{match_folder}/mvp'
    os.mkdir(to_folder)
    mvp_pic_path = f'Graphics/{type}/mvp'
    coords = mvp['coords']
    font_size = mvp['font_size']
    opponent = f"VS {match['opponent'].upper()}"
    for mvp_folder in [f'{mvp_pic_path}/{dir}' for dir in os.listdir(mvp_pic_path)]:
        random_pic = random.choice(os.listdir(mvp_folder))
        img_path = f'{mvp_folder}/{random_pic}'
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        draw.text(coords, opponent, (255, 255, 255), font=get_font(font_size))
        img.save(f"{to_folder}/{img_path.split('/')[-1]}")