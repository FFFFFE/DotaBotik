import requests

def generateMessageText(match_id, live_df, teamid_stats, clf):
    radiant_team = live_df[live_df['match_id'] == match_id]['radiant_team'].tolist()[0]
    dire_team = live_df[live_df['match_id'] == match_id]['dire_team'].tolist()[0]
    rad_team_id = live_df[live_df['match_id'] == match_id]['rad_team_id'].tolist()[0]
    dire_team_id = live_df[live_df['match_id'] == match_id]['dire_team_id'].tolist()[0]
    map_cnt = live_df[live_df['match_id'] == match_id]['map_cnt'].tolist()[0]

    predict_and_probability = make_predict_upd(rad_team_id, dire_team_id, teamid_stats, clf)
    winner_predict = [dire_team, radiant_team][predict_and_probability[0]]

    new_message = f"""*{radiant_team} - {dire_team}*
`Match id:` [{match_id}](https://www.dotabuff.com/matches/{match_id}/)
`Map: {map_cnt}`
`Prediction:` *{winner_predict}*"""
    return new_message


def make_predict_upd(rad_team_id, dire_team_id, teamid_stats, clf):
    teams_rating_ratio = teamid_stats[rad_team_id]['rating'] / teamid_stats[dire_team_id]['rating']
    rad_wr = teamid_stats[rad_team_id]['wins'] / teamid_stats[rad_team_id]['matches']
    dire_wr = teamid_stats[rad_team_id]['wins'] / teamid_stats[rad_team_id]['matches']
    wr_ratio = rad_wr - dire_wr

    new_match = [teams_rating_ratio, wr_ratio]
    # 1 - radiant_win, 0 - dire_win
    probability = round(max(clf.predict(new_match, prediction_type='Probability')), 4)
    return clf.predict(new_match), probability


# Оптравка сообщений в тг
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

# Правим сообщения
def edit_message(token, message_id, text):
    url = f'https://api.telegram.org/bot{token}/editMessageText'
    response = requests.post(url, data={'chat_id': "@D2Pred", 'message_id': message_id, 'text': text, "parse_mode": 'Markdown', 'disable_web_page_preview': True})
    response_dict = response.json()
    return response_dict

