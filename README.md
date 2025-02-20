# Unifier RaidGuard
Raid detection plugin for Unifier

> [!CAUTION]
> RaidGuard has been discontinued in favor of [Filters](https://wiki.unifierhq.org/guides/bridge/filters).

> [!NOTE]
> This is a Unifier **plugin**! To access Unifier, go [here](https://github.com/greeeen-dev/unifier).

## What is this?
This is a plugin for Unifier which gives it the raid protection it really needs for larger communities. Don't let 
those pesky raiders destroy your communities.

Detects invites, phishing links, and common raid messages.

## Requirements
Unifier v1.2.3 or newer is required.

## Setup
To install Unifier RaidGuard, you can run `u!install https://github.com/UnifierHQ/unifier-raidguard` on the bot.
This will install the plugin through System Manager.

## Troubleshooting
### Conflicting file: `rapidphish.py`
In v1.2.2 and older, some features of RaidGuard were integrated into Unifier Bridge, however we have removed this
from v1.2.3 in favor of RaidGuard Plugin. Please delete `utils/rapidphish.py` and try again.

## License
Unifier Revolt Support is licensed under the AGPLv3. If you wish to use its source code, please read the license 
carefully before doing so.

## Note
All processing of data is done locally on your machine. Nothing is sent to any external server, so don't worry.
