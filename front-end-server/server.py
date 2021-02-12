import copy
import re
import socket
import ssl
import kss
from seq2seq.merger.merger import composer
from seq2seq.evaluate.seq2seq import evaluate
from gensim.models import FastText
from flask_mail import Mail, Message
import urllib.parse
from smtplib import SMTPException
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.inspection import inspect
from oauth2client.contrib.flask_util import UserOAuth2
from flask_cors import CORS, cross_origin
from flask import Flask, request, Response, jsonify, session, redirect
import http.client
import json
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)

app.config.from_object('config')

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    historys = db.relationship('History', backref='users', lazy='dynamic')

    def __repr__(self):
        return '%s' % (self.userid)

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}


class History(db.Model):
    __tablename__ = 'history'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    id = db.Column(db.Integer, primary_key=True)
    before = db.Column(db.Text)
    after = db.Column(db.Text)
    userid = db.Column(db.String(100), ForeignKey('users.userid'))

    def __repr__(self):
        return '%d,%s,%s,%s' % (self.id, self.userid, self.before, self.after)

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}


CORS(app, send_wildcard=True)


@app.route('/loadUserInfo', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def loadUserInfo():
    if 'id' in session:
        return session['id']
    else:
        return jsonify(success=False, error="Cant load yourInfo")


@app.route('/')
@cross_origin(supports_credentials=True)
def home():
    return 'test'


@app.route('/login', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def createUser():
    user_data = request.get_json()
    user_id = user_data['googleId']
    json.dumps(user_id)
    email = user_data['userEamil']
    json.dumps(email)
    session['id'] = user_id

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User()
        user.email = email
        user.userid = user_id
    db.session.add(user)
    db.session.commit()
    if user_id is None:
        print('로그인 버튼을 누르세요')
    else:
        session['id'] = user_id
        session.permanent = True
    return user_id


@ app.route('/logout', methods=['POST', 'GET', 'OPTIONS'])
@ cross_origin(supports_credentials=True)
def logout():

    if 'id' in session:
        session.clear()
    else:
        print("not logged in user")
    return redirect('/')


@ app.route('/extractverbphrase', methods=['POST'])
@ cross_origin(supports_credentials=True)
def extractVerbPhrase():
    user_data = request.get_json()
    req_data = user_data['content']
    json_data = jsonify(req_data)
    "call the NLP API to extract sentence-final verb-phrase and attendant form data from given sourceText"
    if request.is_json:
        # print("is json")
        sourceText = request.json.get('content')
        conjugation = request.json.get('conjugation')
        options = request.json.get('options')

        if options is None:
            options = dict(phraseForm='verbPhrase')
    else:
        return jsonify(success=False, error="Expected application/json POST data")
    # set up the call
    body = json.dumps(dict(sourceText=sourceText, options=options))
    headers = {"Content-Type": "application/json; charset=utf-8",
               "Accept": "application/json; charset=utf-8",
               "Cache-Control": "no-cache",
               "Content-Length": str(len(body))
               }
    try:
        conn = http.client.HTTPSConnection("mirinae.io")
        conn.request("POST", "/api/nlp/extractverbphrase", body, headers)
        response = conn.getresponse()
    except:
        # server down?
        return dict(success=False, error="Server not responding")

    if response.status != 200:
        failReason = response.reason
        return dict(success=False, status=response.status, error=failReason)
    else:
        try:
            # reading data from verbphrase extraction
            data = response.read()
            data = json.loads(data.decode('utf-8'))
            res_value = data['response']
            # front part of sentence ex. 나는 자전거를
            tempconjugations = []
            aconjugations = []
            renew = []
            for i in range(len(res_value)):
                sentence = res_value[i]['sentence']
                verbpart = res_value[i]['verbPhrase'].split('~ ')[1]
                frontpart = sentence.split(verbpart)[0]
                tempconjugation = res_value[i]['conjugation'].split(',')
                tempconjugations.append(tempconjugation)
                aconjugation = ''
                for temp in tempconjugation:
                    if temp == 'past' or temp == ' past':
                        aconjugation += 'past '
                    elif temp == 'future' or temp == ' future':
                        aconjugation += 'future '
                    elif temp == 'present' or temp == ' present':
                        aconjugation += 'present '

                aconjugation += 'formal polite '

                if 'question' in res_value[i]['conjugation']:
                    aconjugation += 'question'
                aconjugations.append(aconjugation)

                if 'honorific' in res_value[i]['conjugation']:
                    nonrenew = res_value[i]['sentence'] + ' '
                    renew.append(nonrenew)
                else:
                    punc = ''
                    if 'question' in res_value[i]['conjugation']:
                        punc += '? '
                    else:
                        punc += '. '
                    text = res_value[i]['morphemeString'].replace(
                        ' ', '_').replace(';', ' ')

                    eval_text = text + aconjugation
                    decode_text = evaluate(eval_text)
                    renewed_words = []
                    for word in decode_text:
                        if word != '<EOS>':
                            word = word.split(':')[0]
                            word = word.replace('_', ' ')
                            renewed_words.append(word)
                    renewed_words = composer(renewed_words)
                    renewed_words = frontpart + renewed_words + punc
                    renew.append(renewed_words)
            renew_list = []
            renew_list2 = []
            last = []
            for i in renew:
                renew_list.append(i.split('\\n'))
                renew_list.append(['\n'])

            print('개행 리스트로 추가: ', renew_list)
            renew_list2 = sum(renew_list, [])
            a = (''.join(renew_list2))
            last.append(a)
            print(a)
            if 'id' in session:
                id = session['id']
                user = User.query.filter(
                    User.userid == session['id']).all()
                history = History(before=sourceText,
                                  after=last, userid=user[0])
                db.session.add(history)
                db.session.commit()
            else:
                id = None
            return jsonify(success=True, response=dict(historyid=history.id, input=history.before, output=history.after))
        except:
            return dict(success=False, error="Illegal JSON response")


mail = Mail(app)

@ app.route('/history', methods=['POST', 'GET', 'OPTIONS'])
@ cross_origin(supports_credentials=True)
def history():
    try:
        # 리턴 아래형식으로 할 수 있게 db에서 데이터 새롭게 끌어오기
        if 'id' in session:
            history = History.query.filter(
                History.userid == session['id']).all()
            history_list = []
            print(history)
            for r in history:
                result = {'historyid': r.id,
                          'input': r.before, 'output': r.after}
                history_list.append(copy.deepcopy(result))
            history_list.reverse()
        else:
            print('failed')
        return jsonify(success=True, response=history_list)
    except:
        return dict(success=False, error="Not able to load history")


@ app.route('/delhistory', methods=['POST', 'GET', 'OPTIONS'])
@ cross_origin(supports_credentials=True)
def DelHistory():
    # 프론트에서 보내는 히스토리 아이디
    del_id = request.json.get('historyid')
    del_history = History.query.get_or_404(del_id)
    print('삭제할 id ', del_id, '삭제할 히스토리', del_history)
    if 'id' in session:
        db.session.delete(del_history)
        db.session.commit()
    else:
        print('Fail to delete history')
    return jsonify(success=True, response=dict(historyid=del_id))


@ app.errorhandler(500)
@ app.route('/mail', methods=['POST', 'GET', 'OPTIONS'])
@ cross_origin(supports_credentials=True)
def index():
    try:
        mail_data = request.get_json()
        json.dumps(mail_data)
        msg = Message(mail_data["emailSubject"], sender='ganzi410@gmail.com',
                      recipients=[mail_data["emailAdress"]])
        print(msg)
        msg.body = mail_data["emailContent"]
        mail.send(msg)
        return "Sent"
    except SMTPException as e:
        print(str(e))
        return jsonify(success=False, error="Mail error")


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5003, debug=True)