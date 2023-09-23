import pandas as pd
from datetime import datetime as dt
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split

df = pd.read_csv('database/maindf.csv')
df = df.sort_values(by='match_id').reset_index(drop=True)


# Функция для расчёта elo
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


# Инициализация начальных рейтингов и статистики матчей для всех команд
team_info = {}

# Пройдемся по всем матчам в датафрейме
for index, row in df.iterrows():
    team1 = row['rad_team_id']
    team2 = row['dire_team_id']

    # Если команда встречается впервые, установим ее рейтинг на 1000 и инициализируем статистику
    if team1 not in team_info:
        team_info[team1] = {'name': row['rad_team_name'], 'rating': 1000, 'matches': 0, 'wins': 0}
    if team2 not in team_info:
        team_info[team2] = {'name': row['dire_team_name'], 'rating': 1000, 'matches': 0, 'wins': 0}

    team1_old_rating = team_info[team1]['rating']
    team2_old_rating = team_info[team2]['rating']
    team1_win = row['radiant_win']

    # Обновляем рейтинги для обеих команд
    team1_new_rating, team2_new_rating = update_ratings(team1_old_rating, team2_old_rating, team1_win)
    team_info[team1]['rating'] = team1_new_rating
    team_info[team2]['rating'] = team2_new_rating

    # Обновляем рейтинги в датафрейме
    df.loc[index, 'new_rad_team_rating'] = team1_new_rating
    df.loc[index, 'new_dire_team_rating'] = team2_new_rating

    # Обновляем статистику матчей для команд
    team_info[team1]['matches'] += 1
    team_info[team2]['matches'] += 1
    if team1_win:
        team_info[team1]['wins'] += 1
    else:
        team_info[team2]['wins'] += 1

    # Обновляем винрейт в датафрейме
    df.loc[index, 'new_rad_team_winrate'] = team_info[team1]['wins'] / team_info[team1]['matches']
    df.loc[index, 'new_dire_team_winrate'] = team_info[team2]['wins'] / team_info[team2]['matches']


# Сохраним данные в словарь
with open("database/team_info.txt", 'w', encoding='utf-8') as file:
    file.write(str(team_info))


# Создадим столбцы-признаки для модели
df['radiant_win'] = df['radiant_win'].map(int).tolist()
df['teams_rating_ratio'] = df['new_rad_team_rating'] / df['new_dire_team_rating']
df['wr_ratio'] = df['new_rad_team_winrate'] - df['new_dire_team_winrate']

# Уберём из датафрейма лишние столбцы
df = df[['match_id', 'teams_rating_ratio', 'wr_ratio', 'patch', 'radiant_win']].reset_index(drop=True)
df.drop_duplicates(inplace=True)

# Разбиение на тестовую и обучающую выборку
x_train, x_test, y_train, y_test = train_test_split(df[['teams_rating_ratio', 'wr_ratio']],
                                                    df['radiant_win'], test_size=0.3, random_state=13)
print(x_train.shape, y_train.shape, x_test.shape, y_test.shape)


# Параметры модели
best_params = {'border_count': 70,
               'depth': 2,
               'l2_leaf_reg': 10,
               'iterations': 200,
               'learning_rate': 0.2}

# Обучение модели
clf = CatBoostClassifier(**best_params)
clf.fit(x_train.to_numpy(), y_train)

# Accuracy модели
print(clf.score(x_test.to_numpy(), y_test))

# Сохраним модель
clf.save_model(f'database/models/team_model_{dt.now().date()}', format='cbm')