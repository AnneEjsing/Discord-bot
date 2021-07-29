import requests
from datetime import datetime, timedelta
from globals import presentable_names
import pytz
from secrets import API_TOKEN

headers = {"Authorization": f"Bearer {API_TOKEN}"}

teamnames = {
    'long': 'Astralis',
    'short': 'AST',
    'talent': 'Astralis Talent'
}

def get_match_cet_time(match):
    utc = pytz.utc
    gmt = datetime.strptime(match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ')
    cet_time = utc.localize(gmt).astimezone(pytz.timezone("Europe/Copenhagen"))
    return cet_time


def get_week_info():
    week_number = datetime.today().isocalendar()[1]
    week_start = datetime.fromisocalendar(2021, week_number, 1)
    week_end = datetime.fromisocalendar(2021, week_number, 7)
    return week_number, week_start, week_end

def get_matches_by_type(type):
    name = teamnames['short'] if type == 'lol' else teamnames['long']
    _, week_start, week_end = get_week_info()
    week_end = week_end + timedelta(days=1)
    query = f'https://api.pandascore.co/{type}/matches?search[name]={name}&range[scheduled_at]={week_start.strftime("%Y-%m-%d")}T00:00:00Z,{week_end.strftime("%Y-%m-%d")}T00:00:00Z&page[size]=100'
    matches = requests.get(query, headers=headers).json()
    # Create 'opponent' entry for each match
    matches = update_matches_with_opponent(matches)

    # Sort matches based on time
    matches = sorted(matches, key=lambda match: datetime.strptime(match['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ'))
    return matches

def get_match_by_id(match):
    type = get_videogame_type(match)
    id = match['id']
    match = requests.get(f'https://api.pandascore.co/{type}/matches?filter[id]={id}', headers=headers).json()
    # Create 'opponent' entry for each match
    match = update_matches_with_opponent(match)
    return match[0]


def update_matches_with_opponent(matches):
    for match in matches:
        opponent = next((opp['opponent']['name'] for opp in match['opponents'] if teamnames['long'] not in opp['opponent']['name']), 'TBD')
        match['opponent'] = opponent
        match['update_reason'] = None
        if opponent in presentable_names:
            match['opponent'] = presentable_names[opponent]
    return matches

def get_videogame_type(match):
    type = match['videogame']['name']
    return 'csgo' if type == 'CS:GO' else 'lol'