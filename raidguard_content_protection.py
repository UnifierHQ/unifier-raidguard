"""
<one line to give the program's name and a brief idea of what it does.>
Copyright (C) <year>  <name of author>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import revolt
import guilded
import time
import math
import re
from tld import get_tld
from utils import rapidphish

# 0: ignore
# 1: watch
# 2: temp

config = {
    'constant': 9600,
    'allow_nsfw': False,
    'invites': 2,
    'rapidphish': 2,
    'raid': 1,
    'rapidphish_whitelist': [

    ]
}

def findurl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]


def bypass_killer(string):
    if not [*string][len(string) - 1].isalnum():
        return string[:-1]
    else:
        raise RuntimeError()

class RaidBan:
    def __init__(self, identifier, bantype=0, debug=True, frequency=1, constant=9600):
        self.identifier = str(identifier) # Either an ID or message content
        self.bantype = bantype # 0: Watchban, 1: Tempban. Watchban lets the content through initially
        self.frequency = frequency # Frequency of content
        self.constant = constant # Constant used for raid detection. Lower is more sensitive
        self.time = round(time.time()) # Time when ban occurred
        self.duration = 600 # Duration of ban in seconds. Base is 600
        self.expire = round(time.time()) + self.duration # Expire time
        self.debug = debug # Debug raidban
        self.involved = {} # List of involved users (format: {userid: [message_ids]})
        self.banned = False # If action has been taken or not

    def is_banned(self):
        if self.expire < time.time():
            return False or self.banned
        return True

    def increment(self,count=1):
        if self.banned:
            raise RuntimeError()
        self.frequency += count
        t = math.ceil((round(time.time())-self.time)/60)
        i = self.frequency
        threshold = round(self.constant*t/i)
        prevd = self.duration
        self.duration = self.duration * 2
        diff = self.duration - prevd
        self.expire += diff
        self.banned = self.duration > threshold
        return self.duration > threshold, threshold


async def find_raidban(identifier,raidbans):
    offset = 0
    for index in range(len(raidbans)):
        raidban = raidbans[index-offset]
        if time.time() >= raidban.expire:
            raidbans.pop(index-offset)
            offset += 1
        if raidban.identifier==identifier:
            return raidban
    return None

async def push_raidban(raidban,raidbans):
    for index in range(len(raidbans)):
        raidban_existing = raidbans[index]
        if raidban_existing.identifier == raidban.identifier:
            raidbans[index] = raidban
            return index
    return None

async def scan(message: discord.Message or revolt.Message or guilded.Message, data):
    """Message scan logic"""

    # Example ban entry in target:
    # {'1187093090415149056': 0} (this is a permanent ban)
    # {'1187093090415149056': 20} (this is a 20 second ban)
    response = {
        'unsafe': False,
        'description': 'No suspicious content found',
        'target': {},
        'delete': [],
        'restrict': {},
        'data': {}
    }

    try:
        raidbans = data['raidbans']
    except:
        raidbans = []

    if (not message.guild.explicit_content_filter == discord.ContentFilter.all_members or
            message.channel.nsfw) and not config['allow_nsfw']:
        response['unsafe'] = True
        response['description'] = (
            'Channel is NSFW or server does not have explicit content scanning set to all members.\n'+
            'Please contact your server administrators for assistance.'
        )
        return response

    invite = False
    phishing = False

    # Prevent message tampering
    urls = findurl(message.content)
    filtered = message.content.replace('\\', '')
    for url in urls:
        filtered = filtered.replace(url, '', 1)
    for word in filtered.split():
        # kill hyperlinks :woke:
        if '](' in word:
            # likely hyperlink, lets kill it
            if word.startswith('['):
                word = word[1:]
            if word.endswith(')'):
                word = word[:-1]
            word = word.replace(')[', ' ')
            words = word.split()
            found = False
            for word2 in words:
                words2 = word2.replace('](', ' ').split()
                for word3 in words2:
                    if '.' in word3:
                        if not word3.startswith('http://') or not word3.startswith('https://'):
                            word3 = 'http://' + word3
                        while True:
                            try:
                                word3 = bypass_killer(word3)
                            except:
                                break
                        if len(word3.split('.')) == 1:
                            continue
                        else:
                            if word3.split('.')[1] == '':
                                continue
                        try:
                            get_tld(word3.lower(), fix_protocol=True)
                            if '](' in word3.lower():
                                word3 = word3.replace('](', ' ', 1).split()[0]
                            urls.append(word3.lower())
                            found = True
                        except:
                            pass

            if found:
                # successful link detection from hyperlink yippee
                continue
        if '.' in word:
            while True:
                try:
                    word = bypass_killer(word)
                except:
                    break
            if len(word.split('.')) == 1:
                continue
            else:
                if word.split('.')[1] == '':
                    continue
            try:
                get_tld(word.lower(), fix_protocol=True)
                if '](' in word.lower():
                    word = word.replace('](', ' ', 1).split()[0]
                urls.append(word.lower())
            except:
                pass

    key = 0
    for url in urls:
        url = url.lower()
        urls[key] = url
        if not url.startswith('http://') and not url.startswith('https://'):
            urls[key] = f'https://{url}'
        if '](' in url:
            urls[key] = url.replace('](', ' ', 1).split()[0]
        if ('discord.gg/' in url or 'discord.com/invite/' in url or 'discordapp.com/invite/' in url or
                'discord.gg/' in message.content or 'discord.com/invite/' in message.content or
                'discordapp.com/invite/' in message.content):
            invite = True
        key = key + 1

    if len(urls) > 0:
        rpresults = rapidphish.compare_urls(urls, 0.85)
        phishing = rpresults.final_verdict == 'safe'

    chars = ''.join(message.content.split())  # remove all whitespace
    upper_percent = sum(i.isupper() for i in chars) / len(chars)

    multi = 1

    for line in message.content.split('\n'):
        if line.startswith('# '):
            multi *= 4
        elif line.startswith('## '):
            multi *= 2

    raid = (upper_percent > 0.5 and len(message.content) > 4 or len(urls) > 0 or
            round(len(message.content) * multi) > 200)

    punishment = 0
    if invite:
        punishment = config['invites']
    elif phishing:
        punishment = config['rapidphish']
    elif raid:
        punishment = config['raid']

    if punishment==0:
        pass
    else:
        raidban = await find_raidban(f'{message.author.id}' if punishment==2 else message.content,raidbans)
        new = False
        toban = False
        threshold = config['constant']
        if not raidban:
            new = True
            raidban = RaidBan(
                identifier=f'{message.author.id}' if punishment==2 else message.content,
                bantype=punishment-1,
                constant=config['constant']
            )
            raidbans.append(raidban)
        if not f'{message.author.id}' in list(raidban.involved.keys()):
            raidban.involved.update({f'{message.author.id}': []})
        raidban.involved[f'{message.author.id}'].append(message.id)
        if not new:
            toban, threshold = raidban.increment()
        if punishment==2:
            response['unsafe'] = True
            response['description'] = f'RaidGuard configured to temporary ban'
            response['target'] = {
                f'{message.author.id}': raidban.duration,
            }
            response['delete'] = [message.id]
        if toban:
            toban = {}
            todelete = []
            for user in raidban.involved:
                toban.update({user:0})
                todelete.append(raidban.involved[user])

            response['unsafe'] = True
            response['description'] = f'RaidGuard dynamic threshold passed ({raidban.duration}/{round(threshold,2)})'
            response['target'] = toban
            response['delete'] = todelete

            if len(raidban.involved.keys()) >= 3:
                response['restrict'].update({f'{message.server.id}':3600})

        await push_raidban(raidban,raidbans)

    response['data'] = {'raidbans': raidbans}

    return response
