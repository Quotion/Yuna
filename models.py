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


# class UserGame(BaseModel):
#     id = AutoField(primary_key=True)
#     steamid = CharField(max_length=64, null=True, default="STEAM_0:0:0000000000")
#     name = CharField(max_length=256, null=False, default="invalid_name")
#     rank = ForeignKeyField(model="ma_players", column_name="role", on_delete="cascade", on_update="cascade")
#
#     class Meta:
#         db_table = "userGame"
#         order_by = ("role",)

class Player(BaseModel):
    SID = CharField(max_length=24, default='STEAM_0:0:0000000000')
    group = TextField(null=False)
    status = TextField(null=False)
    nick = TextField(null=False)
    synch = SmallIntegerField(null=False)
    synchgroup = TextField(null=False)

    class Meta:
        db_table = "ma_players"
        order_by = ("SID",)


class Role(BaseModel):
    role_id = BigIntegerField(null=False, default=0)
    role_gmod = CharField(max_length=32, null=False, default="invalid-role")
    name = CharField(max_length=64, null=False, default="invalid-role")

    class Meta:
        db_table = "role"
        order_by = ("name",)


class User(BaseModel):
    discord_id = BigIntegerField(null=False, primary_key=True)
    mgil = BigIntegerField(null=False, default=0)
    gil = BigIntegerField(null=False, default=0)
    fortuna_wheel = BooleanField(default=True)
    created_at = DateTimeField(null=False, default=datetime.now())
    SID = CharField(max_length=24, default='STEAM_0:0:0000000000')

    class Meta:
        db_table = "user"
        order_by = ("created_at",)

