from configparser import ConfigParser
from datetime import datetime

from peewee import *

config = ConfigParser()
config.read("config.ini")

dbhandle = MySQLDatabase(
    host=config.get("MySQL", "host"),
    user=config.get("MySQL", "user"),
    password=config.get("MySQL", "password"),
    database=config.get("MySQL", "database"),
    port=3306
)


class BaseModel(Model):
    class Meta:
        database = dbhandle


class User(BaseModel):
    discord_id = BigIntegerField(null=False, primary_key=True)
    name = CharField(max_length=32, null=False, default="invalid_name")
    role = CharField(max_length=64, null=False, default="invalid_role")
    gil = BigIntegerField(null=False, default=0)
    fortuna_wheel = BooleanField(default=True)
    created_at = DateTimeField(null=False, default=datetime.now())
    steamid = CharField(max_length=64, null=True, default="STEAM_0:0:0000000000")

    class Meta:
        db_table = "user"
        order_by = ("created_at",)


class UserGame(BaseModel):
    steamid = ForeignKeyField(User, column_name="steamid", on_delete="cascade", on_update="cascade", primary_key=True)
    name = CharField(max_length=256, null=False, default="invalid_name")
    rank = ForeignKeyField(User, column_name="role", on_delete="cascade", on_update="cascade")

    class Meta:
        db_table = "userGame"
        order_by = ("role",)


class Role(BaseModel):
    role_id = BigIntegerField(null=False, default=0)
    name = CharField(max_length=32, null=False, default="invalid-role")

    class Meta:
        db_table = "role"
        order_by = ("name", )


class RoleAndUser(BaseModel):
    discord_id = BigIntegerField(null=False, default=0)
    role_id = BigIntegerField(null=False, default=0)

    class Meta:
        db_table = "discord_id"
        order_by = ("roleanduser", )
