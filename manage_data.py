import requests
import pandas as pd
import json
import time
import os
from numpy import nan


# Функция возвращающая датафрейм с лайв матчем
def get_live_matches(steam_key):
    r_steam = None
    for _ in range(5):
        r_steam = requests.get(f'https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1/?key={steam_key}')
        if r_steam.status_code == 200:
            break
        time.sleep(1)
    if r_steam.status_code != 200:
        return None

    live_games = json.loads(r_steam.text)
    live_df = pd.json_normalize(live_games['result']['games'])

    if len(live_df) > 0:
        live_df['map_cnt'] = live_df['radiant_series_wins'] + live_df['dire_series_wins'] + 1

        live_df = live_df[['match_id', 'league_id', 'radiant_team.team_name', 'radiant_team.team_id',
                           'dire_team.team_name', 'dire_team.team_id', 'map_cnt']]
        # Переименуем столбцы
        live_df = live_df.rename(columns={'radiant_team.team_name': 'radiant_team',
                                          'dire_team.team_name': 'dire_team',
                                          'radiant_team.team_id': 'rad_team_id',
                                          'dire_team.team_id': 'dire_team_id'})
        # Избавимся от пропусков и приведем столбцы к нужному типу
        live_df.dropna(inplace=True)
        live_df[['rad_team_id', 'dire_team_id']] = live_df[['rad_team_id', 'dire_team_id']].astype('int64')
        live_df.reset_index(drop=True, inplace=True)

        return live_df
    return



# Функция возращающая по id матча строчку датафрейма с информацией по игре
def get_match_by_id(match_id):
    response = requests.get('https://api.opendota.com/api/matches/' + str(match_id))
    data = response.json()

    data = pd.DataFrame(data.values(), data.keys()).T

    # Избавимся от массивных пока не нужных столбцов
    data[['chat', 'cosmetics', 'draft_timings', 'all_word_counts', 'replay_url',
          'objectives', 'radiant_gold_adv', 'radiant_xp_adv']] = ['-'] * 8

    return data


def update_ratings(rating1, rating2, win1):
    k_factor = 32
    win1 = float(win1)
    win2 = float(not win1)
    r1 = 10 ** (rating1 / 400)
    r2 = 10 ** (rating2 / 400)
    e1 = r1 / (r1 + r2)
    e2 = r2 / (r1 + r2)
    rating_diff1 = k_factor * (win1 - e1)
    rating_diff2 = k_factor * (win2 - e2)

    return rating1 + rating_diff1, rating2 + rating_diff2


# Обновление рейтинга команд
def rewrite_stats(radiant_team_id, dire_team_id, radiant_win):
    # Откроем файл с данными по статистике команд
    with open(os.path.abspath("database/team_info.txt"), 'r', encoding='utf-8') as file:
        team_info = eval(file.read())

    # Считаем рейтинги команд
    rating1 = team_info[radiant_team_id]['rating']
    rating2 = team_info[dire_team_id]['rating']

    print(team_info[radiant_team_id], rating1, team_info[radiant_team_id]['wins'],
          team_info[dire_team_id], rating2, team_info[radiant_team_id]['wins'])

    # Пересчитаем рейтинги
    rating1, rating2 = update_ratings(rating1, rating2, radiant_win)

    # Запишем новые рейтинги
    team_info[radiant_team_id]['rating'] = rating1
    team_info[dire_team_id]['rating'] = rating2

    # Добавим инфу о числе матчей
    team_info[radiant_team_id]['matches'] += 1
    team_info[dire_team_id]['rating'] += 1

    # Добавим инфу о числе побед
    if radiant_win:
        team_info[radiant_team_id]['wins'] += 1
    else:
        team_info[dire_team_id]['wins'] += 1

    print(team_info[radiant_team_id], rating1, team_info[radiant_team_id]['wins'],
          team_info[dire_team_id], rating2, team_info[radiant_team_id]['wins'])

    # Сохраним обновлённый файл со статистикой
    with open("database/team_info.txt", 'w', encoding='utf-8') as file:
        file.write(str(team_info))


def get_match_data(matchID, steam_key):
    apiUrl = f"https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/?match_id={matchID}&key={steam_key}"
    response = requests.get(apiUrl)
    return response.json()


# Узнаем победителя если он есть
def getMatchWinner(matchID, steam_key):
    data = get_match_data(matchID, steam_key)

    if 'result' in data and 'radiant_win' in data['result']:
        radiant_name = data['result']['radiant_name']
        dire_name = data['result']['dire_name']

        # radiant_team_id = data['result']['radiant_team_id']
        # dire_team_id = data['result']['dire_team_id']

        radiant_win = data['result']['radiant_win']

        # rewrite_stats(radiant_team_id, dire_team_id, radiant_win)
        return radiant_name if radiant_win else dire_name
    return



