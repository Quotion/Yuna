import discord
import logging

from steam import steamid

from datetime import datetime, timezone, timedelta

from discord.ext import commands
from models import dbhandle, User
import peewee


log = logging.getLogger("commands")


class OnConnectionError(commands.CheckFailure):
    pass


class Commands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(name="профиль")
    async def profile(self, ctx, *args):
        now = datetime.now(timezone(timedelta(hours=3)))
        SID = None

        try:
            dbhandle.connect()
        except peewee.OperationalError as error:
            log.error(error)
            raise OnConnectionError("Ошибка подключения базы данных.\nДополнительная информация в консоли.")

        if len(args) != 0:
            if isinstance(args[0], discord.Member):
                ctx_user = args[0]
        else:
            ctx_user = ctx.author

        try:
            SID = User.get(User.discord_id == ctx_user.id)
        except peewee.DoesNotExist:
            pass

        if not SID:
            data_user = dict(steamid="Не синхронизирован",
                             url=None,
                             nick="Не синхронизирован",
                             date_enter="Не синхронизирован",
                             group="Не синхронизирован",
                             count_violations="Не синхронизирован")
        else:
            cursor_user = dbhandle.execute_sql("SELECT * FROM ma_players WHERE SID=%s", [SID])
            user = cursor_user.fetchall()[0]
            cursor_violations = dbhandle.execute_sql('SELECT COUNT(*) FROM ma_violations WHERE SID=%s', [SID])
            count_violations = cursor_violations.fetch_one()

            date_enter = datetime.strptime(str(user[2]['date']), "%Y-%m-%d %H:%M:%S.%f")
            group = steamid.SteamID(SID)

            data_user = dict(steamid=SID,
                             url=group.community_url,
                             nick=user[3],
                             date_enter=date_enter.strftime("%d.%m.%Y"),
                             group=user[1],
                             count_violations=count_violations)

        embed = discord.Embed(colour=discord.Colour.from_rgb(168, 74, 210),
                              title="Профиль пользователя:",
                              url=data_user['url'])

        embed.set_author(name=ctx_user.display_name,
                         icon_url=ctx.guild.icon_url)

        embed.add_field(name="Discord:",
                        value=f"`{ctx_user.display_name}#{ctx_user.discriminator}`")

        embed.add_field(name="Имя в Garry's Mod:",
                        value=f"`{data_user['nick']}`")

        embed.add_field(name="Роль в Discord:",
                        value=f"{ctx_user.top_role.mention}")

        embed.add_field(name="Роль в Garry's Mod:",
                        value=f"`{data_user['group']}`")

        embed.add_field(name="Дата первого входа на сервер:",
                        value=f"`{data_user['date_enter']}`")

        if data_user['count_violations'] == "Не синхронизирован":
            embed.add_field(name="Количество нарушений:",
                            value=f"`{data_user['count_violations']}`")
        elif data_user['count_violations'] == 1:
            embed.add_field(name="Количество нарушений:",
                            value=f"`{data_user['count_violations'] } нарушение.`")
        elif data_user['count_violations']  == 2 or data_user['count_violations']  == 3 or data_user['count_violations']  == 4:
            embed.add_field(name="Количество нарушений:",
                            value=f"`{data_user['count_violations'] } нарушения.`")
        else:
            embed.add_field(name="Количество нарушений:",
                            value=f"`{data_user['count_violations'] } нарушений.`")

        embed.set_thumbnail(url=ctx_user.avatar_url)

        embed.set_footer(text=f"Дата вызова команды {now.strftime('%d.%m.%Y %H:%M')}")

        await ctx.send(embed=embed)
