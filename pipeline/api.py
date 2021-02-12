#  training/utilities/nlpAPI.py  - utility calls to the NLP back-end API
#
#  Copyright © Mirinae Corp., John Wainwright 2020
#
import json
import http.client, urllib.parse

def extractVerbPhrase(sourceText, options=None):   # 'endingForm'):
    "call the NLP API to extract sentence-final verb-phrase and attendant form data from given sourceText"

    # set up the call
    if options is None:
        options = dict(phraseForm='verbPhrase')
    body = json.dumps(dict(sourceText=sourceText, options=options))

    headers = {"Content-Type": "application/json; charset=utf-8",
               "Accept": "application/json; charset=utf-8",
               "Cache-Control": "no-cache",
               "Content-Length": str(len(body))
               }
    try:
        conn = http.client.HTTPSConnection("alpha.mirinae.io")
        # local test:  conn = http.client.HTTPConnection("localhost:2000")
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
            data = response.read()
            return json.loads(data.decode('utf-8'))
        except:
            return dict(success=False, error="Illegal JSON response")

if __name__ == "__main__":

    # test it
    result = extractVerbPhrase("나는 자전거를 탈 수 있을 것이야. 나는 배가 고파.")
    print(result)