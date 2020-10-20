from configparser import ConfigParser

import cogs

from discord.ext import commands
import logging


config = ConfigParser()
config.read("config.ini", encoding="utf8")


logging.basicConfig(format="%(levelname)s: %(funcName)s (%(lineno)d): %(name)s: %(message)s",
                    level=logging.INFO)
log = logging.getLogger("main")


client = commands.Bot(command_prefix="-")

client.add_cog(cogs.Events(client))
client.add_cog(cogs.Orders(client))
client.add_cog(cogs.Vote(client))
client.add_cog(cogs.Commands(client))

client.run(config.get("DISCORD", "token"))
