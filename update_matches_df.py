import pandas as pd
import requests
import time

from manage_data import get_match_by_id


# Импортируем df и отбросим столбцы, которые будем обновлять
df = pd.read_csv('database/maindf.csv')
df.drop(['rad_rating', 'rad_wr', 'rad_matches_cnt', 'dire_rating', 'dire_wr', 'dire_matches_cnt'], axis=1, inplace=True)

original_shape = df.shape[0]


# Список скаченных match_id
my_ids = df['match_id'].tolist()


# Соберем df с новыми матчами
response = requests.get('https://api.opendota.com/api/proMatches/').json()
new_matches_ids = [m['match_id'] for m in response if m['match_id'] not in my_ids]

while True:
    response = requests.get(
        'https://api.opendota.com/api/proMatches?less_than_match_id=' + str(min(new_matches_ids))).json()
    time.sleep(0.5)

    temp_list = [m['match_id'] for m in response if
                 m['match_id'] not in new_matches_ids and m['match_id'] > max(my_ids)]
    new_matches_ids.extend(temp_list)

    if len(temp_list) < 5:
        break


# Создание датафрейма новых матчей
new_df = pd.DataFrame()

for i, match_id in enumerate(new_matches_ids):
    new_data = get_match_by_id(match_id)
    time.sleep(0.1)

    if new_data is not None:
        new_df = pd.concat([new_df, new_data], ignore_index=True)

# Избавимся от пропусков в пиках и сбросим индекс
new_df.dropna(subset=['picks_bans', 'radiant_team', 'dire_team'], inplace=True)
new_df.reset_index(drop=True, inplace=True)

print(f'Будет добавленно {len(new_df)} матчей')


# Обработка new_df
# Создадим столбцы с пиками и банами
def radiant_bans(lst):
    return list(map(lambda x: x['hero_id'], (filter(lambda x: not x['is_pick'] and x['team'] == 0, lst))))


def dire_bans(lst):
    return list(map(lambda x: x['hero_id'], (filter(lambda x: not x['is_pick'] and x['team'], lst))))


def radiant_picks(lst):
    return list(map(lambda x: x['hero_id'], (filter(lambda x: x['is_pick'] and x['team'] == 0, lst))))


def dire_picks(lst):
    return list(map(lambda x: x['hero_id'], (filter(lambda x: x['is_pick'] and x['team'], lst))))


new_df['radiant_bans'] = new_df['picks_bans'].apply(radiant_bans)
new_df['dire_bans'] = new_df['picks_bans'].apply(dire_bans)
new_df['radiant_picks'] = new_df['picks_bans'].apply(radiant_picks)
new_df['dire_picks'] = new_df['picks_bans'].apply(dire_picks)


# 4.2 Создадим столбцы с инфой по игрокам
# Создадим столбец со значеним player_accaunt_id
def account_id(lst):
    return list(map(lambda x: x['account_id'], lst))


new_df['account_id'] = [account_id(new_df['players'].iloc[i]) for i in range(len(new_df))]


# Создадим столбец со значеним [playernaname, hero_id]
def personaname(lst):
    return list(map(lambda x: x.get('personaname', None), lst))


new_df['personaname'] = [personaname(new_df['players'].iloc[i]) for i in range(len(new_df))]

# 4.3 Столбцы с инфой по турниру
new_df['league_tier'] = [new_df['league'].iloc[i].get('tier', None) for i in range(len(new_df))]
new_df['league_name'] = [new_df['league'].iloc[i].get('name', None) for i in range(len(new_df))]

# 4.4 Столбцы с инфой по командам
new_df['rad_team_id'] = [new_df['radiant_team'].iloc[i].get('team_id', 0) for i in range(len(new_df))]
new_df['rad_team_name'] = [new_df['radiant_team'].iloc[i].get('name', 0) for i in range(len(new_df))]

new_df['dire_team_id'] = [new_df['dire_team'].iloc[i].get('team_id', 0) for i in range(len(new_df))]
new_df['dire_team_name'] = [new_df['dire_team'].iloc[i].get('name', 0) for i in range(len(new_df))]

# 4.5 Приведение столбцов к нужным типам
cols = ['match_id', 'patch', 'region', 'leagueid', 'rad_team_id', 'dire_team_id']
new_df[cols] = new_df[cols].fillna(0).apply(pd.to_numeric)

new_df = new_df[['match_id', 'radiant_picks', 'dire_picks', 'radiant_bans', 'dire_bans', 'account_id', 'personaname',
                 'rad_team_id', 'rad_team_name', 'dire_team_id', 'dire_team_name', 'league_tier', 'leagueid',
                 'league_name', 'region', 'patch', 'radiant_win']]

# 5. Обоготим исходный df новыми матчами
df = pd.concat([df, new_df], ignore_index=True)

# 6. Скачаем рейтинги команд
teams = pd.DataFrame()
for i in range(16):
    new_teams = requests.get(f'https://api.opendota.com/api/teams?page={i}').json()
    new_teams = pd.json_normalize(new_teams)
    new_teams = new_teams.drop(['logo_url', 'last_match_time'], axis=1)

    if 'logo_url' in new_teams.columns and 'last_match_time' in new_teams.columns:
        teams = pd.concat([teams, new_teams], ignore_index=True)

        time.sleep(0.5)

teams.drop_duplicates(inplace=True)

# Создадим две новых метрики
teams['wr'] = teams['wins'] / (teams['losses'] + teams['wins'])
teams['matches_cnt'] = teams['wins'] + teams['losses']

# Удалим команды без игр
teams.dropna(inplace=True)


# 7. Обогащение df рейтингом команд
# Добавим инфу про rad_team
test = df.merge(teams[['team_id', 'rating', 'wr', 'matches_cnt']],
                left_on='rad_team_id', right_on='team_id', how='left')
test.rename(columns={"team_id": "rad_team_id", "rating": "rad_rating",
                     'wr': 'rad_wr', 'matches_cnt': 'rad_matches_cnt'}, inplace=True)

# Добавим инфу про dire_team
test = test.merge(teams[['team_id', 'rating', 'wr', 'matches_cnt']],
                  left_on='dire_team_id', right_on='team_id', how='left')
test.rename(columns={"team_id": "dire_team_id", "rating": "dire_rating",
                     'wr': 'dire_wr', 'matches_cnt': 'dire_matches_cnt'}, inplace=True)

# Удалим пропуски
test.dropna(subset=['rad_team_id', 'dire_team_id'], inplace=True)

# Удалим дубли столбцов
test = test.loc[:, ~test.columns.duplicated()].copy()

# Приведем новые столбцы к типу int
test[['rad_team_id', 'rad_matches_cnt', 'dire_team_id', 'dire_matches_cnt']] = test[['rad_team_id',
                                            'rad_matches_cnt', 'dire_team_id', 'dire_matches_cnt']].astype(int)

assert test.shape[0] > original_shape, 'Данные потерялись'
test.to_csv('database/maindf.csv', index=False)