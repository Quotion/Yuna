import numpy
import os

import discord
from datetime import timedelta, timezone
from discord.ext import commands
from models import *
import logging


config = ConfigParser()
config.read("config.ini", encoding="utf8")


log = logging.getLogger("main")


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.check()

        try:
            dbhandle.connect()
            if not dbhandle.table_exists("user"):
                dbhandle.create_tables([User])
            if not dbhandle.table_exists("usergame"):
                dbhandle.create_tables([UserGame])
            if not dbhandle.table_exists("role"):
                dbhandle.create_tables([Role])
            if not dbhandle.table_exists("roleanduser"):
                dbhandle.create_tables([RoleAndUser])
        except Exception as error:
            log.error(error)
        finally:
            dbhandle.close()

    def user_bot(self, user_id):
        return self.client.user.id == user_id

    @commands.Cog.listener()
    async def on_connect(self):
        log.info("Bot Yuna connect to Discord API")

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Bot Yuna ready on 100%")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        now = datetime.now(timezone(timedelta(hours=3)))

        try:
            dbhandle.connect()

            User.insert(discord_id=member.id,
                        name=member.name,
                        role=member.roles[0].id) \
                .on_conflict_ignore() \
                .execute()

            role = discord.utils.get(member.guild.roles, name="Помощник машинста")
            if not role:
                raise commands.MissingRole("Помошник машиниста")

            await member.add_roles(role)
        except discord.HTTPException as error:
            raise commands.CommandError(error)
        except Exception as error:
            raise commands.CommandError(error)
        finally:
            dbhandle.close()

        embed = discord.Embed(colour=discord.Colour.dark_green(),
                              title="Новый пользователь",
                              description=f"На сервер зашел {member.name}#{member.discriminator}")
        embed.set_image(url=member.avatar_url)
        embed.set_footer(text=f"Дата входа: {now.strftime('%d.%m.%Y %H:%M')}")

        channel = discord.utils.get(self.client.get_all_channels(), name=config.get("CHANNELS", "logging"))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = discord.utils.get(self.client.get_all_channels(), name=config.get("CHANNELS", "logging"))

        if not channel:
            return

        now = datetime.now(timezone(timedelta(hours=3)))

        embed = discord.Embed(colour=discord.Colour.red(),
                              title="Пользователь покинул сервер.",
                              description=f"С сервера ушел {member.name}#{member.discriminator}")
        embed.set_image(url=member.avatar_url)
        embed.set_footer(text=f"Дата выхода: {now.strftime('%d.%m.%Y %H:%M')}")

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, member_before, member_after):
        channel = discord.utils.get(self.client.get_all_channels(), name=config.get("CHANNELS", "logging"))

        if not channel:
            return

        now = datetime.now(timezone(timedelta(hours=3)))

        if not numpy.array_equal(member_before.roles, member_after.roles):
            embed = discord.Embed(colour=discord.Colour.dark_gold(),
                                  title=f"Роли, пользователя {member_after.name}, были изменены.")

            embed.description = f"`Роли до`: {' '.join([role.mention for role in member_before.roles])}\n" \
                                f"`Роли после`: {' '.join([role.mention for role in member_after.roles])}"

            embed.set_thumbnail(url=member_after.avatar_url)

            embed.set_footer(text=f"Дата изменения: {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, msg_before, msg_after):
        if self.user_bot(msg_after.author.id):
            return

        channel = discord.utils.get(self.client.get_all_channels(), name=config.get("CHANNELS", "logging"))

        if not channel:
            return

        now = datetime.now(timezone(timedelta(hours=3)))

        embed = discord.Embed(colour=discord.Colour.dark_gold(),
                              title="Сообщение было изменено.",
                              description=f"Пользователь {msg_before.author.mention} изменил своё сообщение.")

        if len(msg_after.content.split()) > 5:
            embed.add_field(name="Сообщение:",
                            value=f"`До`: {' '.join(word for word in msg_before.content.split()[:5])}..." \
                                  f"\n`После`: {' '.join(word for word in msg_after.content.split()[:5])}...")

            file = open("changed_message.txt", "w", encoding="utf8")
            file.write(f"Сообщение до:\n{msg_before.content}"
                       f"\n\n\n"
                       f"Сообщение после:\n{msg_after.content}")

            file.close()

            file = open("changed_message.txt", "rb")
            file_send = discord.File(file, filename="changed_message.txt")

            embed.set_footer(text=f"Дата изменения сообщения: {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed, file=file_send)

            file.close()
            file_send.close()
            os.remove("changed_message.txt")

        else:
            embed.add_field(name="Сообщение:",
                            value=f"`До`: {msg_before.content}" \
                                  f"\n`После`: {msg_after.content}")

            embed.set_footer(text=f"Дата изменения сообщения: {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.user_bot(message.author.id):
            return

        channel = discord.utils.get(self.client.get_all_channels(), name=config.get("CHANNELS", "logging"))

        if not channel:
            return

        now = datetime.now(timezone(timedelta(hours=3)))

        embed = discord.Embed(colour=discord.Colour.dark_magenta(),
                              title="Сообщение было удалено.",
                              description=f"Пользователь {message.author.mention}, удалил сообщение")

        if len(message.content.split()) > 10:
            embed.add_field(name="Сообщение:",
                            value=" ".join(word for word in message.content.split()[:10]))

            file = open("message_deleted.txt", "w", encoding="utf8")
            file.write(f"Сообщение:\n{message.content}")

            file.close()

            file = open("message_deleted.txt", "rb")
            file_send = discord.File(file, filename="message_deleted.txt")

            embed.set_footer(text=f"Дата удаления сообщения: {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed, file=file_send)

            file.close()
            file_send.close()
            os.remove("changed_message.txt")
        else:
            embed.add_field(name="Сообщение:",
                            value=message.content)

            embed.set_footer(text=f"Дата удаления сообщения: {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed)

    def check(self):
        @self.client.event
        async def on_message(message):
            if self.user_bot(message.author.id):
                return
            else:
                await self.client.process_commands(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        now = datetime.now(timezone(timedelta(hours=3)))

        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(colour=discord.Colour.red())
            embed.description = "```css\n[Команда] не найдена. Вы ввели [команду], которую невозможно обработать." \
                                f"\n[Команда]: {ctx.message.content.split()[0][1::]}```"
            embed.set_footer(text=f"Дата вызова ошибки {now.strftime('%d.%m.%Y %H:%M')}")
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRole):
            embed = discord.Embed(colour=discord.Colour.red())
            embed.description = "```css\n[Роль] не найдена." \
                                f"\n[Роль]: {error}```"
            embed.set_footer(text=f"Дата вызова ошибки {now.strftime('%d.%m.%Y %H:%M')}")
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(colour=discord.Colour.light_gray())
            embed.description = "```css\n[Аргументов] к данной команде недостаточно." \
                                f"\n[Аргумент]: {error.param}```"
            embed.set_footer(text=f"Дата вызова ошибки {now.strftime('%d.%m.%Y %H:%M')}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=discord.Colour.light_gray())
            embed.description = "```css\nВызвана [ошибка], которую невозможно обработать." \
                                f"\n[Ошибка]: {error}```"
            embed.set_footer(text=f"Дата вызова ошибки {now.strftime('%d.%m.%Y %H:%M')}")
            await ctx.send(embed=embed)
