from environs import Env
from dataclasses import dataclass

@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту

@dataclass
class SteamApi:
    key: str              # Ключ для доступа к Steam API


@dataclass
class Config:
    tg_bot: TgBot
    steam_api: SteamApi


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN')),
                  steam_api=SteamApi(key=env('STEAM_API_KEY')))