from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1521359/2d597f5095d98fcb5385', '1521359/35e7ee463c484a6feec1'],
    'нью-йорк': ['1533899/0dd15c0a369a7f37bb60', '14236656/4af886109f68fbc3adb3'],
    'париж': ["14236656/6da78ab6eceb34b6108a", '1533899/c490c7ab3a2e0c7550b6']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return
    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True

                },
                {
                    'title': 'Нет',
                    'hide': True

                },
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True

                    },
                    {
                        'title': 'Нет',
                        'hide': True

                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ]
        elif req['request']['original_utterance'].lower() == 'помощь':
            res['response']['text'] = 'Это текст помощи.'
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
        res['response']['buttons'] = [
            {
                'title': 'Помощь',
                'hide': True
            }
        ]
    else:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            res['response']['text'] = 'Правильно! Сыграем ещё?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True

                },
                {
                    'title': 'Нет',
                    'hide': True

                },
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем ещё?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True

                    },
                    {
                        'title': 'Нет',
                        'hide': True

                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ]
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
                res['response']['buttons'] = [
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ]
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
