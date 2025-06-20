# callback API + Asyncia

from flask import Flask, request, jsonify
import sys, json, requests
application = Flask(__name__)

@application.route("/webhook/", methods=["POST"])
def webhook():
    request_data = request.json
    call_back = requests.post(request_data['callback_url'], json={
        "version": "2.0", "template": { "outputs": [{
            "simpleText": {"text": request_data['result']['choices'][0]['message']['content']}
        }]}})
    print(call_back.status_code, call_back.json())
    return 'OK'

@application.route("/question", methods=["POST"])
def call_openai_api():
    user_request = request.json.get('userRequest', {})
    callback_url = user_request.get('callbackUrl')
    try:
        api = requests.post('https://api.asyncia.com/v1/api/request/', json={
            "apikey": "(OpenAI API 키 입력하기)",
            "messages" :[{"role": "user", "content": user_request.get('utterance', '')}],
            "userdata": [["callback_url", callback_url]]},
            headers={"apikey":"(Asyncia API 키 입력하기)"}, timeout=2)
    except requests.exceptions.ReadTimeout:
        pass    
    return jsonify({
      "version" : "2.0",
      "useCallback" : True
    })

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=80, debug=True)
