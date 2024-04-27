from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from data import db_session
from data.users import User
from data.games import Games
import json

app = Flask(__name__)
continue_game = '''<p>{}</p>
                    <p>Команда дала верный ответ?:</p>
                    <button onclick = "window.location.href = 'http://127.0.0.1:5000/start_game/{}/{}/0/YES';">Да</button>
                    <button onclick = "window.location.href = 'http://127.0.0.1:5000/start_game/{}/{}/0/NO';">Нет</button>'''
get_question = '''<p>{}</p>
                    <button onclick = "window.location.href = 'http://127.0.0.1:5000/get_answer/{}/{}';">Получить ответ</button>'''

on_start = '''<p>{}</p>
                <button onclick="window.location.href = 'http://127.0.0.1:5000/index';">На главную</button>
                '''


@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def main_page():
    if request.method == 'GET':
        db_sess = db_session.create_session()
        most_popular_game = sorted([(i.title, i.id) for i in db_sess.query(Games).all()])
        return render_template('index.html', range=most_popular_game)
    else:
        d = request.form['most']
        return redirect(f'/start_game/{d}/0/1/1')


@app.route('/start_game/<id_game>/<del_question>/<param>/<yn>', methods=['POST', 'GET'])
def start_game(id_game, del_question, param, yn):
    global number, deletes, c, r, current_command
    if request.method == 'GET' and int(param):
        return render_template('register_game.html', range=range(5))
    else:
        if c == {}:
            for i in range(5):
                c[request.form[str(i)]] = 0
                r[i] = request.form[str(i)]
            current_command = request.form['0']
        od_session = db_session.create_session()
        res = od_session.query(Games).filter(Games.id == int(id_game))[0]
        count = len(json.loads(res.content))
        deletes[int(del_question)] = False
        if yn == 'YES':
            plus = 100 * (int(del_question)) % 500
            c[current_command] += plus if plus != 0 else 500
        if len([i for i in list(deletes.values()) if i == False]) == count + 1:
            main_res = []
            for i in c:
                main_res.append((i, c[i]))
            main_res.sort(key=lambda x: x[-1], reverse=True)
            res = F'''Первое место команда "{main_res[0][0]}"-{main_res[0][1]}<p>
                    Второе место команда "{main_res[1][0]}"-{main_res[1][1]}<p>
                    Третье место команда "{main_res[2][0]}"-{main_res[2][1]}<p>
                    Четвертое место команда "{main_res[3][0]}"-{main_res[3][1]}<p>
                    Пятое место команда "{main_res[4][0]}"-{main_res[4][1]}<p>
                    <button onclick="window.location.href = 'http://127.0.0.1:5000/index';">На главную</button>'''
            return res
        return render_template('MAIN_HTML.html', range=range(1, count + 1), id=int(id_game), num=(number + 1) % 5 + 1,
                               t=deletes)


@app.route('/open_question/<id_question>/<id_game>')
def open_question(id_question, id_game):
    od_session = db_session.create_session()
    res = od_session.query(Games).filter(Games.id == int(id_game))[0]
    content = json.loads(res.content)
    return get_question.format(content[str(id_question)][0] + '?', id_question, id_game)


#
@app.route('/get_answer/<id_question>/<id_game>')
def get_answer(id_question, id_game):
    global number, current_command
    od_session = db_session.create_session()
    res = od_session.query(Games).filter(Games.id == int(id_game))[0]
    content = json.loads(res.content)
    number += 1
    current_command = r[number % 5]
    return 'Ответ:' + continue_game.format(content[id_question][1], id_game, id_question,
                                           id_game,
                                           id_question)


current_userid = ''
number = -1
deletes = {x: True for x in range(20)}
c = {}
current_command = ''
r = {}


@app.route('/create_game', methods=['POST', 'GET'])
def create_game():
    if current_userid == '':
        return on_start.format('Для создания игр необходимо войти или зарегистрироваться.')
    if request.method == 'GET':
        return render_template('create_game_base.html', range=range(20), k=0)
    else:
        name_game = request.form['name_game']
        db_sess = db_session.create_session()
        answers = []
        k = 0
        for i in range(1, 21):
            que, ans = request.form[f'Вопрос №{i}'], request.form[f'Ответ №{i}']
            if que != '' and ans != '':
                k += 1
                answers.append((k, (que, ans)))
        if len(answers) <= 5:
            return render_template('create_game_base.html', range=range(20), k=1)
        lib = dict(answers)
        json_object = json.dumps(lib)
        games = Games()
        games.title = name_game
        games.user_id = current_userid
        games.content = json_object
        db_sess.add(games)
        db_sess.commit()
        return on_start.format('Успешно!')


@app.route('/enter', methods=['POST', 'GET'])
def enter_user():  # войти
    global current_userid
    if request.method == 'GET':
        return render_template('enter.html', k=0)
    else:
        password = request.form['pass']
        name = request.form['name']
        db_sess = db_session.create_session()
        flag = 0
        for user in db_sess.query(User).all():
            if user.name == name and password == user.hashed_password:
                current_userid = user.id
                flag = user.id
        if not flag:
            return render_template('enter.html', k=1)
        else:
            current_userid = flag
            return on_start.format('Успешно!')


@app.route('/check_in', methods=['POST', 'GET'])
def check_in_user():
    if request.method == 'GET':
        return render_template('registration.html', k=0)
    else:
        name = request.form['name']
        password = request.form['pass']
        password_r = request.form['pass_r']
        db_sess = db_session.create_session()
        flag = any([j.name == name for j in db_sess.query(User).all()])
        if password != password_r:
            return render_template('registration.html', k=2)
        elif flag:
            return render_template('registration.html', k=1)
        else:
            user = User()
            user.name = name
            user.hashed_password = password
            db_sess.add(user)
            db_sess.commit()
            return on_start.format('Успешно!')


if __name__ == '__main__':
    db_session.global_init("db/games.db")
    app.run()
