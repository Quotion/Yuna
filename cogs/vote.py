import os
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands

import json
import asyncio


class Vote(commands.Cog, name="Голосование"):

    def __init__(self, client):
        self.client = client
        self.poll_time = False

    @commands.command(name="выбор",
                      help="Дополнительные аргументы в этой команде используются следующим образом:"
                           "\n1. Вы указываете вопрос сразу после команды ВЫБОР "
                           "(пример <префикс>выбор Стоит лм убрать меня с админки?)"
                           "\n2. Далее необходимо указать ответы, которые будут идти по порядку, через знак \"+\""
                           "(пример: <префикс>выбор <вопрос> +да +нет +что?",
                      brief="<префикс>выбор Стоит лм убрать меня с админки? +да +нет +что?",
                      description="Команда создает голосвание, которое можно использовать как угодно.")
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def polls(self, ctx, *, data: str):
        message = data.split()
        answers = data.split("+")
        quest = ""
        for i in range(0, len(message)):
            if message[i].find("+") == -1:
                quest += message[i] + " "
            else:
                break

        if quest == "":
            desc = discord.Embed(colour=discord.Colour.dark_green())

            desc.set_author(name="Вы не поставили вопрос.")
            desc.description = f"Голосование не может быть создано, пока не будет поставлен вопрос голосования."
            await ctx.channel.send(embed=desc)
            return

        answers = answers[1:len(answers)]
        if len(answers) > 9 or len(answers) < 1:
            desc = discord.Embed(colour=discord.Colour.dark_green())

            desc.set_author(name=f"Ответов очень {'мало' if len(answers) < 1 else 'много'}.")
            desc.description = f"Голосование не может быть создано, потому что количетсво " \
                                f"ответов {'меньше 1' if len(answers) < 1 else 'больше 9'}."

            await ctx.channel.send(embed=desc)
            return

        now = datetime.now(timezone(timedelta(hours=3)))

        simbols = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":ten:"]
        things = list()

        for answer, i in zip(answers, range(0, 9)):
            things.append(f"{simbols[i]} {answer}")

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 63))
        embed.set_author(name=quest)
        embed.description = '\n'.join([thing for thing in things])
        embed.set_footer(text=f"Время создания: {now.strftime('%H:%M %d.%m.%Y')} | Сделал: {ctx.author.nick}")

        msg = await ctx.send(embed=embed)

        for i in range(1, len(answers) + 1):
            await msg.add_reaction(f"{i}\N{combining enclosing keycap}")

    @commands.command(name="голосование",
                      help="Дополнительные аргументы в этой команде используются следующим образом:"
                           "\n1. Для начала нужно указать время, которое будет идти голосование, но не больше 60 минут"
                           " (пример: <префикс>голосование 60)."
                           "\n2. Вы указываете вопрос сразу после команды ГОЛОСОВАНИЕ"
                           " (пример: <префикс>голосование 60 Стоит лм убрать меня с админки?)"
                           "\n3. Далее необходимо указать ответы, которые будут идти по порядку, через знак \"+\""
                           " (пример: <префикс>голосование <время> <вопрос> +да +нет +что?",
                      brief="<префикс>голосование Стоит лм убрать меня с админки? +да +нет +что?",
                      description="Команда создает голосвание, но уже на определенное количетсво времени, "
                                  "которое можно использовать как угодно.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def polls_time(self, ctx, time: int, *, data: str):
        if self.poll_time:
            warning = discord.Embed(colour=discord.Colour.red())
            warning.set_author(name="У Вас не завершенно предыдущее голосвание")
            warning.description = "Чтобы начать новогое голосование закончите предыдущее."

            await ctx.send(embed=warning)
            return

        message = data.split()
        answers = data.split("+")
        quest = ""
        for i in range(0, len(message)):
            if message[i].find("+") == -1:
                quest += message[i] + " "
            else:
                break

        desc = discord.Embed(colour=discord.Colour.light_grey())

        if time > 120:

            desc.set_author(name="Нельзя ставить время на голосование больше 2 часов.")
            desc.description = f"Нельзя ставить время на голосование больше 2 часов из-за того что это может " \
                               f"превисти к неожиданным последствиям."
            await ctx.channel.send(embed=desc)
            return

        if quest == "":
            desc.set_author(name="Вы не поставили вопрос.")
            desc.description = f"Голосование не может быть создано, пока не будет поставлен вопрос голосования."
            await ctx.channel.send(embed=desc)
            return

        answers = answers[1:len(answers)]

        if len(answers) > 9 or len(answers) < 1:
            embed = discord.Embed(colour=discord.Colour.dark_green())

            embed.set_author(name=f"Ответов очень {'мало' if len(answers) < 1 else 'много'}.")
            embed.description = f"Голосование не может быть создано, потому что количетсво " \
                                f"ответов {'меньше 1' if len(answers) < 1 else 'больше 9'}."
            await ctx.channel.send(embed=embed)
            return

        emoji = self.client.get_emoji(762433366049816587)

        now = datetime.now(timezone(timedelta(hours=3)))
        time_end = datetime.now(timezone(timedelta(minutes=time + 180)))

        simbols = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":ten:"]
        things = list()

        for answer, i in zip(answers, range(0, 9)):
            things.append(f"{simbols[i]} - {answer[0].title() + answer[1::]}")

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 63))
        embed.set_author(name=quest)
        for answer in answers:
            embed.add_field(name=answer[0].title() + answer[1::],
                            value=emoji,
                            inline=False)
        embed.description = '\n'.join([thing for thing in things])
        embed.set_footer(text=f"Время создания: {now.strftime('%H:%M %d.%m.%Y')} | "
                              f"Сделал: {ctx.author.name} | "
                              f"Время до окончания {time_end.strftime('%H:%M %d.%m.%Y')}")

        msg = await ctx.send(embed=embed)

        for i in range(1, len(answers) + 1):
            await msg.add_reaction(f"{i}\N{combining enclosing keycap}")

        self.poll_time = True
        message_id = msg.id
        del msg

        poll_time = {"emoji": 762433366049816587, "message": message_id, "voices": {}}

        with open("poll_time.json", "w", encoding='utf8') as file:
            json.dump(poll_time, file, indent=3)

        await asyncio.sleep(time * 60)

        try:
            msg = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            desc.set_author(name="Сообщение с голосвание не было найдено.")
            desc.description = f"Произошла ошибка и сообщение с голосвание не было найдено." \
                               f"превисти к неожиданным последствиям."
            await ctx.send(embed=embed)

        self.poll_time = False

        embed = msg.embeds[0].to_dict()

        now = datetime.now(timezone(timedelta(hours=3)))

        del embed['description']
        embed['author']['name'] = f"Результаты.\n{embed['author']['name'][0].title()}{embed['author']['name'][1::]}"
        embed['footer']['text'] = f"Голосвание завершено в {now.strftime('%H:%M %d.%m.%Y')} | Создал {ctx.author.name}"

        await msg.edit(embed=discord.Embed.from_dict(embed))
        await msg.clear_reactions()

        try:
            os.remove("poll_time.json")
        except Exception as error:
            self.logger.error(error)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not self.poll_time or user.id == self.client.user.id:
            return

        with open("poll_time.json", "r", encoding='utf8') as file:
            previously = json.load(file)

        message = reaction.message

        if message.id != previously['message']:
            return

        emoji = self.client.get_emoji(previously['emoji'])

        if str(user.id) not in previously['voices'].keys():
            embed = message.embeds[0].to_dict()
            embed["fields"][int(reaction.emoji[0]) - 1]['value'] += f" <:{emoji.name}:{emoji.id}>"
            await message.edit(embed=discord.Embed.from_dict(embed))
            await reaction.remove(user)
            previously['voices'][user.id] = int(reaction.emoji[0])
        else:
            await reaction.remove(user)

        with open("poll_time.json", "w", encoding='utf8') as file:
            json.dump(previously, file, indent=3)