from flask import (Flask, request, Response, jsonify)
from flask_cors import CORS
import json
import http.client, urllib.parse
from gensim.models import FastText
from seq2seq.evaluate.seq2seq import evaluate
from seq2seq.merger.merger import composer
import kss
# import seq2seq.merger.unicode

app = Flask(__name__)
CORS(app, send_wildcard=True)

@app.route('/')
def home():
    return 'test'

@app.route('/extractverbphrase', methods=['POST'])
        
def extractVerbPhrase():
    "call the NLP API to extract sentence-final verb-phrase and attendant form data from given sourceText"
    if request.is_json:
        sourceText = request.json.get('sourceText')
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
        conn = http.client.HTTPSConnection("alpha.mirinae.io")
        # local test:  
        # conn = http.client.HTTPConnection("localhost:2000")
        conn.request("POST", "/api/nlp/extractverbphrase", body, headers)
        response = conn.getresponse()
    except:
        # server down?
        return dict(success=False, error="Server not responding")
    #
    if response.status != 200:
        failReason = response.reason
        return dict(success=False, status=response.status, error=response.reason)
    else:
        try:
            # reading data from verbphrase extraction
            data = response.read()
            data = json.loads(data.decode('utf-8'))

            # front part of sentence ex. 나는 자전거를
            frontpart = data['response'][0]['sentence']
            verbpart = data['response'][0]['verbPhrase'].split('~ ')[1]
            frontpart = frontpart.split(verbpart)[0]

            # morpheme analysis of verbphrase ex. 타:VV ㄹ 수 있:VMOD 다:SEF
            text = data['response'][0]['morphemeString'].replace(' ','_').replace(';', ' ')

            # generate sequence for seq2seq = morpheme array + target conjugation mode
            text = text + conjugation

            # seq2seq evaluate calculation
            decoded_words = evaluate(text)

            # re-compose output morpheme sequence into complete verb phrase
            renewed_words =[]
            for word in decoded_words:
                if word != '<EOS>':
                    word = word.split(':')[0]
                    word = word.replace('_', ' ')
                    renewed_words.append(word)
            renewed_words = composer(renewed_words)

            # put front part and complete verb phase together
            renewed_words = frontpart + renewed_words

            # return
            return jsonify(success=True, response=dict(reconjugation=renewed_words))
        except:
            return dict(success=False, error="Illegal JSON response")

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)