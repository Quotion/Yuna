from configparser import ConfigParser

import cogs

from discord.ext import commands
import logging


config = ConfigParser()
config.read("config.ini")


logging.basicConfig(format="%(levelname)s: %(funcName)s (%(lineno)d): %(name)s: %(message)s",
                    level=logging.INFO)
log = logging.getLogger("main")
log.setLevel(logging.INFO)


client = commands.Bot(command_prefix="-")

client.add_cog(cogs.Events(client))
client.run(config.get("DISCORD", "token"))