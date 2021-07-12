class Variables(object):
    """
    Class that contains some bot variables.
    """
    musicname = ""

    daysarray = {"Monday": "Poniedziałek", "Tuesday": "Wtorek", "Wednesday": "Środa", "Thursday": "Czwartek",
                 "Friday": "Piątek", "Saturday": "Sobota", "Sunday": "Niedziela"}

    emojiarray = ["😀", "😈", "🎃", "🥶", "😡", "🔥", "👽"]

    noneEmoji = "❌"

    sessionLimit = 7
    sessionMembers = 10

    goodSound = "wow"

    badSound = "mexican"

    inactiveRole = "RPGamer: Inactive"

    djRole = "RPGamer: DJ"

    FFMPEG_OPTIONS = {'before_options': "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                      'options': "-vn"}



    YTDL_OPTS = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'simulate': True,
        'no_warnings': True,
        'quiet': True,
        'logtostderr': False,
        'ignorerrrors': True
    }

    queueLimit = 10
    queueCacheLimit = 5

    teamLimit = 10




