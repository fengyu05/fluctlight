from botchan.discord.bot_client import DiscordBotClient
from botchan.discord.discord_bot_proxy import DiscordBotProxy
from botchan.settings import BOT_CLIENT

if BOT_CLIENT == "DISCORD":
    DISCORD_BOT_CLIENT = DiscordBotClient.get_instance()
    DISCORD_BOT_CLIENT.add_proxy(DiscordBotProxy.get_instance())