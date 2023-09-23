import os
import time
from numpy import nan
from catboost import CatBoostClassifier
from database import *

from config_data.config import Config, load_config
from manage_data import get_live_matches, getMatchWinner, get_match_data, rewrite_stats
from publishing import generateMessageText, send_message, edit_message

config: Config = load_config()
steam_key = config.steam_api.key
token = config.tg_bot.token

# В директории с данными находим последнюю модель
listdir = os.listdir(r"database\models")
last_model = max(filter(lambda x: x.startswith('team_model'), listdir))

# Загружаем обученную модель
from_file = CatBoostClassifier()
clf = from_file.load_model(os.path.abspath(rf"database\models\{last_model}"))


def get_team_info():
    with open(os.path.abspath("database/team_info.txt"), 'r', encoding='utf-8') as file:
        team_info = eval(file.read())
        return team_info


# Для всех матчей из лайва, если они еще не опубликованы, сделаем прогноз и запостим в группу, обновив df published
def predictAndPost(live_df):
    for _, row in live_df.iterrows():
        published = select_data(conn, "SELECT * FROM published_matches")
        team_info = get_team_info()

        # Ищем неопубликованные и присутcтвующие в словаре матчи
        if str(row['match_id']) not in published['match_id'].tolist() and \
                row['rad_team_id'] in team_info and row['dire_team_id'] in team_info:
            text = generateMessageText(row['match_id'], live_df, team_info, clf)

            message_id, message_text = send_message(token, text)

            if message_id != -1 and 'match_id' in row.columns:
                data = {'match_id': row['match_id'], 'message_id': message_id, 'message_text': message_text}
                insert_data(conn, 'published_matches', data)


# Записать в published.xlsx и wr.xlsx информацию о закончившимся матче
def updateResults():
    published = select_data(conn, "SELECT * FROM published_matches")  # Датафрейм с опубликованными матчами
    counter = select_data(conn, "SELECT * FROM winrate")  # Счётчик побед и поражений

    wins, losses = counter.loc[0, 'wins'], counter.loc[0, 'losses']

    exclude_list = []  # match_id`s результат которых уже опубликован в тг

    for i in range(len(published)):
        message_id = published.loc[i, 'message_id']
        message = published.loc[i, 'message_text']
        match_id = published.loc[i, 'match_id']

        predict_string = message[message.find("Prediction:` ") + len("Prediction:` "):].strip("*")
        # curr_winner = getMatchWinner(match_id, steam_key)
        curr_data = get_match_data(match_id, steam_key)

        if 'result' not in curr_data or 'radiant_win' not in curr_data['result']:
            # if not curr_winner:
            continue

        radiant_team_id = curr_data['result']['radiant_team_id']
        dire_team_id = curr_data['result']['dire_team_id']
        radiant_win = curr_data['result']['radiant_win']
        # rewrite_stats(radiant_team_id, dire_team_id, radiant_win)

        if getMatchWinner(match_id, steam_key) != predict_string:
            edit_message(token, message_id, message + '\n✖️ ' + f'*{wins} - {losses + 1}*')
            losses += 1
        else:
            edit_message(token, message_id, message + '\n✅✅✅ ' + f'*{wins + 1} - {losses}*')
            wins += 1

        exclude_list.append(match_id)  # Add match_id to excluding list

        del curr_data, radiant_team_id, dire_team_id, radiant_win,

    counter.loc[0, 'wins'], counter.loc[0, 'losses'] = wins, losses

    # Lets delete from dataframe 'published' rows with ended-published-redacted mathes
    # published = published[~published['match_id'].isin(exclude_list)].reset_index(drop=True)

    delete_data(conn, f"DELETE FROM published_matches WHERE match_id IN ({tuple(exclude_list)})")

    # for _, row in published.iterrows():
    #     insert_data(conn, "published_matches", row)

    insert_data(conn, "winrate", counter.loc[0, :])


with create_connection("database/dota_base.db") as conn:
    while True:
        live_df = get_live_matches(steam_key)
        if live_df is None:
            print('live_df is None')
            time.sleep(2)
            continue
        updateResults()
        predictAndPost(live_df)
        print("wow")
        for _ in range(60 * 15):
            time.sleep(1)
