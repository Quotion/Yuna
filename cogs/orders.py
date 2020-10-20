import asyncio
import os
import discord
import datetime
import logging
from discord.ext import commands
from configparser import ConfigParser
from models import Role, dbhandle

config = ConfigParser()
config.read("config.ini", encoding="utf8")


class Orders(commands.Cog, name="Приказы рангового сервера"):
    def __init__(self, client):
        self.client = client
        self.check = True

        logger = logging.getLogger("orders")
        logger.setLevel(logging.INFO)

        self.logger = logger

    def get_name_of_role(self, ctx) -> str:
        try:
            dbhandle.connect(reuse_if_open=True)
            role = Role.select().where(Role.role_id == ctx.author.top_role.id)[0]
        except IndexError:
            raise commands.CommandError("Профиль пользователя не был создан в БД")
        except Exception as error:
            raise commands.CommandError(error)

        if role:
            return role.name

    async def __delete_message(self, ctx, message):
        await ctx.message.delete()
        with open("deleted_order.txt", "w", encoding="utf8") as file:
            file.write(ctx.message.content)

        file = open("deleted_order.txt", "rb")
        temp = discord.File(file, filename="deleted_order.txt")

        await ctx.send(file=temp)
        file.close()
        os.remove("deleted_order.txt")
        temp.close()

        await message.delete()

        self.check = True

    async def __send_message(self, reaction, ctx, message, embed):
        if reaction.emoji == "✅":
            await ctx.message.delete()
            await message.delete()
            embed.set_footer(text="Приказ является ПОДТВЕРЖДЕННЫМ.\nПодтверждено: {}".format(ctx.author.name))
            await ctx.send(embed=embed)
            self.check = True
        elif reaction.emoji == "❌":
            await self.__delete_message(ctx, message)

    @commands.command(name="заступить", help="<префикс>заступить <№ приказа>")
    async def enter(self, ctx, *, number_of_order: int):
        if not self.check:
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.description = f"{ctx.author.mention}, предыдущий приказ является НЕ ПОДТВЕЖДЕННЫМ.\n" \
                                f"Подтвердите его, прежде чем перейти к следующему."
            embed.set_footer(text="Предупреждение.")
            await ctx.send(embed=embed)
            return

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

        embed = discord.Embed(colour=discord.Colour.greyple())
        embed.set_author(name=f"Приказ №{number_of_order}")
        embed.description = f"\nДата: {now.strftime('%d.%m.%Y')}\nВремя: {now.strftime('%H:%M:%S')}\n\nПоездной диспетчер {ctx.author.mention} заступил на дежурство."
        embed.set_footer(text="Приказ, является НЕ ПОДТВЕРЖДЕННЫМ.\nДля его подтвеждения нажмите на ✅.")

        message = await ctx.send(embed=embed, delete_after=60)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        self.check = False

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=lambda r, u: u.id == ctx.author.id)
        except asyncio.TimeoutError:
            await self.__delete_message(ctx, message)
        else:
            await self.__send_message(reaction, ctx, message, embed)

    @commands.command(name="приказ", help="<префикс>приказ <№ приказа> <приказ>")
    async def order(self, ctx, order_id, *, order: str):
        if not self.check:
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.description = f"{ctx.author.mention}, предыдущий приказ является НЕ ПОДТВЕЖДЕННЫМ.\n" \
                                f"Подтвердите его, прежде чем перейти к следующему."
            embed.set_footer(text="Предупреждение.")
            await ctx.send(embed=embed)
            return

        if not order_id.isdigit():
            embed = discord.Embed(colour=discord.Colour.dark_magenta())
            embed.set_author(name="Неверно введны параметры для команды.")
            embed.description = f"{ctx.author.mention}, в команде неверно введены параметры." \
                                f"\nПример {self.client.command_prefix[0]}заступить 24 Николай Фоменко"
            return

        chief = self.get_name_of_role(ctx)

        if not chief:
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.description = f"{ctx.author.mention}, Вы не являетесь начальником какой-либо из служб.\n" \
                                f"Для получения доступа к приказам получите одну из ролей начальника."
            embed.set_footer(text="Предупреждение.")
            await ctx.send(embed=embed)
            return

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

        embed = discord.Embed(colour=discord.Colour.greyple())
        embed.set_author(name=f"Приказ №{order_id}")
        embed.description = f"\nДата: {now.strftime('%d.%m.%Y')}" \
                            f"\nВремя: {now.strftime('%H:%M:%S')}" \
                            f"\n\n**{order}**" \
                            f"\n\n{chief}: {ctx.author.mention}."
        embed.set_footer(text="Приказ, является НЕ ПОДТВЕРЖДЕННЫМ.\nДля его подтвеждения нажмите на ✅.")

        message = await ctx.send(embed=embed, delete_after=60)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        self.check = False

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=lambda r, u: u.id == ctx.author.id)
        except asyncio.TimeoutError:
            await self.__delete_message(ctx, message)
        else:
            await self.__send_message(reaction, ctx, message, embed)

    @commands.command(name="распоряжение", help="<префикс>распоряжение <распоряжение>")
    async def direction(self, ctx, *, direction: str):
        if not self.check:
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.description = f"{ctx.author.mention}, предыдущий приказ является НЕ ПОДТВЕЖДЕННЫМ.\n" \
                                f"Подтвердите его, прежде чем перейти к следующему."
            embed.set_footer(text="Предупреждение.")
            await ctx.send(embed=embed)
            return

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

        chief = self.get_name_of_role(ctx)

        if not chief:
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.description = f"{ctx.author.mention}, Вы не являетесь начальником какой-либо из служб.\n" \
                                f"Для получения доступа к приказам получите одну из ролей начальника."
            embed.set_footer(text="Предупреждение.")
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(colour=discord.Colour.greyple())
        embed.set_author(name=f"Распоряжение")
        embed.description = f"\nДата: {now.strftime('%d.%m.%Y')}" \
                            f"\nВремя: {now.strftime('%H:%M:%S')}" \
                            f"\n\n**{direction}**" \
                            f"\n\n{chief}: {ctx.author.mention}."
        embed.set_footer(text="Приказ, является НЕ ПОДТВЕРЖДЕННЫМ.\nДля его подтвеждения нажмите на ✅.")

        message = await ctx.send(embed=embed, delete_after=60)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        self.check = False

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=lambda r, u: u.id == ctx.author.id)
        except asyncio.TimeoutError:
            await self.__delete_message(ctx, message)
        else:
            await self.__send_message(reaction, ctx, message, embed)

    @commands.command(name="сдать", help="<префикс>сдать <№ приказа>")
    async def hand_over(self, ctx, *, number_of_order: int):
        if not self.check:
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.description = f"{ctx.author.mention}, предыдущий приказ является НЕ ПОДТВЕЖДЕННЫМ.\n" \
                                f"Подтвердите его, прежде чем перейти к следующему."
            embed.set_footer(text="Предупреждение.")
            await ctx.send(embed=embed)
            return

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

        embed = discord.Embed(colour=discord.Colour.greyple())
        embed.set_author(name=f"Приказ №{number_of_order}")
        embed.description = f"\nДата: {now.strftime('%d.%m.%Y')}" \
                            f"\nВремя: {now.strftime('%H:%M:%S')}" \
                            f"\n\nПоездной диспетчер {ctx.author.mention} сдал смену."
        embed.set_footer(text="Приказ, является НЕ ПОДТВЕРЖДЕННЫМ.\nДля его подтвеждения нажмите на ✅.")

        message = await ctx.send(embed=embed, delete_after=60)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        self.check = False

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=lambda r, u: u.id == ctx.author.id)
        except asyncio.TimeoutError:
            await self.__delete_message(ctx, message)
        else:
            await self.__send_message(reaction, ctx, message, embed)
