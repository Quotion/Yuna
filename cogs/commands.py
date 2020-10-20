from pprint import pprint

import discord
import logging

import steam.steamid

from datetime import datetime, timezone, timedelta

from discord.ext import commands
from discord.ext import tasks
from models import dbhandle, User, Player
import peewee

log = logging.getLogger("commands")


class OnConnectionError(commands.CheckFailure):
    pass


class Commands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @staticmethod
    async def check_user(ctx_user) -> bool:
        try:
            User.insert(discord_id=ctx_user.id) \
                .on_conflict_ignore() \
                .execute()
            return True
        except peewee.PeeweeException as error:
            log.error(error)
            return False

    @commands.command(name="профиль")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def profile(self, ctx, *args):
        async with ctx.typing():
            now = datetime.now(timezone(timedelta(hours=3)))
            profile_data = None
            dbhandle.connect(reuse_if_open=True)

            if len(args) != 0:
                if isinstance(args[0], discord.Member):
                    ctx_user = args[0]
            else:
                ctx_user = ctx.author

            if not await self.check_user(ctx_user):
                raise OnConnectionError("Произашла ошибка в создании профиля.\nДополнительная информация в консоли.")

            try:
                profile_data = User.select().where(User.discord_id == ctx_user.id)[0]
            except IndexError:
                pass
            except peewee.DoesNotExist:
                raise OnConnectionError("Произашла ошибка в получении данных.\nДополнительная информация в консоли.")
            finally:
                dbhandle.close()

            if profile_data.SID == "STEAM_0:0:0000000000":
                data_user = dict(mGIL=profile_data.mgil,
                                 GIL=profile_data.gil,
                                 steamid="Не синхронизирован",
                                 url=None,
                                 nick="Не синхронизирован",
                                 date_enter="Не синхронизирован",
                                 group="Не синхронизирован",
                                 count_violations="Не синхронизирован")
            else:
                player_data = Player.select().where(Player.SID == profile_data.SID)[0]
                cursor_violations = dbhandle.execute_sql(sql="SELECT COUNT(*) FROM ma_violations WHERE SID=%s",
                                                         params=[profile_data.SID])
                count_violations = cursor_violations.fetchone()[0]

                status = eval(player_data.status)

                group = steam.steamid.SteamID(profile_data.SID)

                data_user = dict(mGIL=profile_data.mgil,
                                 GIL=profile_data.gil,
                                 steamid=profile_data.SID,
                                 url=group.community_url,
                                 nick=player_data.nick,
                                 date_enter=datetime.utcfromtimestamp(int(status['date'])).strftime("%d.%m.%Y"),
                                 group=player_data.group,
                                 count_violations=count_violations)

            embed = discord.Embed(colour=discord.Colour.from_rgb(168, 74, 210),
                                  title="Профиль пользователя:",
                                  url=data_user['url'])

            embed.set_author(name=ctx_user.display_name,
                             icon_url=ctx.guild.icon_url)

            embed.add_field(name="Discord:",
                            value=f"`{ctx_user.display_name}#{ctx_user.discriminator}`")

            embed.add_field(name="mGIL:",
                            value=f"`{data_user['mGIL']} mGIL`")

            embed.add_field(name="GIL:",
                            value=f"`{data_user['GIL']} GIL`")

            embed.add_field(name="Имя в Garry's Mod:",
                            value=f"`{data_user['nick']}`")

            embed.add_field(name="Роль в Discord:",
                            value=f"{ctx_user.top_role.mention}",
                            inline=False)

            embed.add_field(name="Роль в Garry's Mod:",
                            value=f"`{data_user['group']}`",
                            inline=False)

            embed.add_field(name="Дата первого входа на сервер:",
                            value=f"`{data_user['date_enter']}`",
                            inline=False)

            if data_user['count_violations'] == "Не синхронизирован":
                embed.add_field(name="Количество нарушений:",
                                value=f"`{data_user['count_violations']}`",
                                inline=False)
            elif data_user['count_violations'] == 1:
                embed.add_field(name="Количество нарушений:",
                                value=f"`{data_user['count_violations']} нарушение.`",
                                inline=False)
            elif data_user['count_violations'] == 2 or data_user['count_violations'] == 3 or data_user[
                'count_violations'] == 4:
                embed.add_field(name="Количество нарушений:",
                                value=f"`{data_user['count_violations']} нарушения.`",
                                inline=False)
            else:
                embed.add_field(name="Количество нарушений:",
                                value=f"`{data_user['count_violations']} нарушений.`",
                                inline=False)

            embed.set_thumbnail(url=ctx_user.avatar_url)

            embed.set_footer(text=f"Дата вызова команды {now.strftime('%d.%m.%Y %H:%M')}")

            await ctx.send(embed=embed)

            dbhandle.close()

    @commands.command(name="синхр")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def synch(self, ctx, *args):
        dbhandle.connect(reuse_if_open=True)
        now = datetime.now(timezone(timedelta(hours=3)))

        if len(args) == 1:
            data = args[0]
        else:
            embed = discord.Embed(colour=discord.Colour.blurple())
            embed.description = "Введите ссылку на свой Steam профиль, чтобы синхронизироваться." \
                                "\nТакже можно воспользоваться SteamID."
            embed.set_footer(text=f"Дата вызова ошибки: {now.strftime('%d.%m.%Y %H:%M')}")
            await ctx.send(embed=embed)
            return

        try:
            user = User.select().where(User.discord_id == ctx.author.id)[0]
        except IndexError:
            embed = discord.Embed(colour=discord.Colour.blurple())
            embed.set_author(name="Создайте профиль для синхронизации!")
            embed.description = f"Для того чтобы синхронизировать свой аккаунт в Garry's mod и Discord " \
                                f"необходимо создать **профиль**. " \
                                f"Для этого введите команду **{self.client.command_prefix[0]} профиль**"
            embed.set_footer(text=f"Дата вызова исключения: {now.strftime('%d.%m.%Y %H:%M')}")

            await ctx.send(embed=embed)

            return

        if data.startswith('https://steamcommunity.com/') or data.startswith('http://steamcommunity.com/'):
            SteamID = steam.steamid.steam64_from_url(data)
            if not SteamID:
                embed = discord.Embed(colour=discord.Colour.blurple())
                embed.set_author(name="SteamID не найден.")
                embed.description = f"После отправки запроса с данными, которые Вы ввели, нам не пришло " \
                                    f"подтверждения, что такой SteamID существует."
                embed.set_footer(text=f"Дата вызова ошибки: {now.strftime('%d.%m.%Y %H:%M')}")
                await ctx.channel.send(embed=embed)
                return
            steamid = steam.steamid.SteamID(SteamID).as_steam2_zero
        else:
            SteamID = steam.steamid.SteamID(data)
            if not SteamID:
                embed = discord.Embed(colour=discord.Colour.blurple())
                embed.set_author(name="SteamID не найден.")
                embed.description = f"После отправки запроса с данными, которые Вы ввели, нам не пришло " \
                                    f"подтверждения, что такой SteamID существует."
                embed.set_footer(text=f"Дата вызова ошибки: {now.strftime('%d.%m.%Y %H:%M')}")
                await ctx.channel.send(embed=embed)
                return
            steamid = SteamID.as_steam2_zero

        try:
            SID = Player.select().where(Player.SID == steamid)[0]
        except IndexError:
            embed = discord.Embed(colour=discord.Colour.blurple())
            embed.set_author(name="SteamID не найден в базе данных.")
            embed.description = f"Этот SteamID не найден в базе данных. " \
                                f"Возможно игрок с этим SteamID ни разу не играл на сервере."
            embed.set_footer(text=f"Дата вызова исключения: {now.strftime('%d.%m.%Y %H:%M')}")
            await ctx.channel.send(embed=embed)
            return

        try:
            query = User.get_or_none(User.SID == steamid)
            if query is not None:
                embed = discord.Embed(colour=discord.Colour.blurple())
                embed.set_author(name="Человек с таким SteamID уже найден.")
                embed.description = f"Игрок SteamID."
                embed.set_footer(text=f"Дата вызова исключения: {now.strftime('%d.%m.%Y %H:%M')}")
                await ctx.channel.send(embed=embed)
                return
        except IndexError:
            pass
        except TypeError:
            pass

        try:
            query = User.update({User.SID: steamid}).where(User.discord_id == ctx.author.id)
            query.execute()
        except Exception as error:
            log.error(error)
            raise commands.CommandError(error)

        # user.execute(f"UPDATE users SET steamid = '{steamid}' WHERE \"discordID\" = '{ctx.author.id}'")
        # conn.commit()
        embed = discord.Embed(colour=discord.Colour.green())
        embed.set_author(name="SteamID успешно синхронизирован!")
        embed.description = f"Спасибо, за синхронизацию вашего аккаунта Steam с Discord!"
        embed.set_footer(text=f"Дата синхронизации: {now.strftime('%d.%m.%Y %H:%M')}")
        await ctx.channel.send(embed=embed)
