def get_by_name(list, name): return next(
    (elem for elem in list if elem.name == name), None)


class _Channels(object):
    def __init__(self, channels) -> None:
        self.CSGO_LIVE = get_by_name(channels, '☆│cs-live')
        self.CSGO = get_by_name(channels, '☆│counter-strike')
        self.LOL_LIVE = get_by_name(channels, '☆│lol-live')
        self.LOL = get_by_name(channels, '☆│league-of-legends')
        self.SCHEDULE = get_by_name(channels, '📆│weekly-schedule')
        self.COMCOORDS = get_by_name(channels, '🔴│community-coordinators')


class _Roles(object):
    def __init__(self, roles) -> None:
        self.CSGO = get_by_name(roles, 'Astralis CS')
        self.LOL = get_by_name(roles, 'Astralis LOL')
        self.COMCOORDS = get_by_name(roles, 'Community Coordinators')
        self.SOME = get_by_name(roles, 'Social Media Team')
        self.EVERYONE = get_by_name(roles, '@everyone')


class _Emojis(object):
    def __init__(self, emojis) -> None:
        self.CSGO: str = f"<:csgo:{get_by_name(emojis, 'csgo').id}>"
        self.LOL: str = f'<:lol:{get_by_name(emojis, "lol").id}>'
        self.ASTRALIS: str = f"<:astralis:{get_by_name(emojis, 'astralis').id}>"
        self.TWITTER: str = f"<:twitter:{get_by_name(emojis, 'twitter').id}>"


CHANNELS: _Channels = None
ROLES: _Roles = None
EMOJIS: _Emojis = None


def initialise_globals(guild):
    global CHANNELS, ROLES, EMOJIS
    CHANNELS = _Channels(guild.channels)
    ROLES = _Roles(guild.roles)
    EMOJIS = _Emojis(guild.emojis)


teamnames = {
    'long': 'Astralis',
    'short': 'AST',
    'talent': 'Astralis Talent'
}

type2pandaid = {
    'csgo': 3209,
    'lol': 128044
}

presentable_names = {
    'Team Vitality': 'Vitality',
    'Excel Esports': 'Excel',
    'FC Schalke 04 Esports': 'Schalke 04',
    'Misfits Gaming': 'Misfits',
    'Natus Vincere': 'NAVI'
}
