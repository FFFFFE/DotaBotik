import pandas as pd
from database import *
import os
from numpy import nan
from manage_data import getMatchWinner
import requests
pd.set_option('display.max_columns', None)


matchID = 7259912747
steam_key = ''
token = ""


def send_message(token, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(url, data={'chat_id': "@D2Pred", 'text': message, "parse_mode": 'Markdown', 'disable_web_page_preview': True})
    response_dict = response.json()
    if response_dict:
        if response_dict.get('result'):
            message_id = response_dict.get('result').get('message_id')
            return message_id, message
    else:
        return -1, -1

print(send_message(token, 'text'))