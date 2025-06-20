# callback API + threading

from flask import Flask, jsonify, request
from openai import OpenAI
from bs4 import BeautifulSoup
from PIL import Image
import requests
import threading
import json
import pytesseract
import io

# Flask 앱 객체 생성
app = Flask(__name__)

# 채팅 모델 컨텍스트
CHAT_MODEL_CONTEXT = "친절한 말투를 사용해줘."

# OpenAI 클라이언트 설정
client = OpenAI(api_key="(OpenAI API 키 입력하기)")


# Callback
def gpt_reply(callback_url, msg, is_summary=False):
    
    # 시스템 컨텍스트로 메시지 리스트 초기화
    messageList = [{"role": "system", "content": CHAT_MODEL_CONTEXT}]
    
    # 웹 페이지 요약 요청 문구 추가
    if is_summary:
        messageList.append({"role": "system", "content": f"다음 웹 페이지의 내용을 요약해줘."})

    # 사용자 메시지를 메시지 리스트에 추가
    messageList.append({"role": "user", "content": msg})

    # OpenAI 채팅 모델에서 응답 받기
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messageList
    )
    response_message = completion.choices[0].message

    # 응답 형식 구성
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"{response_message.content}"

                    }
                }
            ]
        }
    }
    
    requests.post(callback_url, json=response)
    
    return 'OK'


# 챗GPT와 대화하기
@app.route('/question', methods=['POST'])
def chat_response():
    
    # 사용자 요청 데이터 추출
    user_request = request.json.get('userRequest', {})
    callback_url = user_request.get('callbackUrl')
    utterance = user_request.get('utterance', '')
    
    # 비동기 처리
    threading.Thread(target=gpt_reply, args=(callback_url, utterance)).start()

    #JSON 응답 반환
    return jsonify({
      "version" : "2.0",
      "useCallback" : True
    })


# 웹 페이지 요약
@app.route('/url', methods=['POST'])
def chat_summary():
    
    # 사용자 요청 데이터 추출
    user_request = request.json.get('userRequest', {})
    callback_url = user_request.get('callbackUrl')
    utterance = user_request.get('utterance', '')
    
    # 웹페이지 요청
    res = requests.get(utterance)
    
    # 본문 추출
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 텍스트 추출할 태그
    paragraphs = soup.find_all(['p', 'h1', 'h2', 'article'])
    text_content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
    
    print("==== 추출된 본문 내용 ====")
    print(text_content)
    print("==== 끝 ====")
    
    # 비동기 처리
    threading.Thread(target=gpt_reply, args=(callback_url, text_content, True)).start()

    #JSON 응답 반환
    return jsonify({
      "version" : "2.0",
      "useCallback" : True
    })


@app.route('/img', methods=['POST'])
def img_txt():
    
    # 사용자 요청 데이터 추출
    user_request = request.json.get('userRequest', {})
    # callback_url = user_request.get('callbackUrl')
    # utterance = user_request.get('utterance', '')
    
    # 액션 파라미터
    action = request.json.get('action', {})
    params = action.get('params', {})
    secureimg_raw = params.get('secureimage', '')

    # JSON 파싱
    secureimg_data = json.loads(secureimg_raw)
    secure_urls_str = secureimg_data.get('secureUrls', '')

    # URL 추출
    urls = secure_urls_str[5:-1].split(', ')
    img_url = urls[0]

    # 이미지 다운로드
    img_res = requests.get(img_url)
    img = Image.open(io.BytesIO(img_res.content))

    # OCR
    extracted_txt = pytesseract.image_to_string(img, lang='kor+eng')

    # 비동기 처리
    # threading.Thread(target=gpt_reply, args=(callback_url, utterance)).start()
    
    #JSON 응답 반환
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"{extracted_txt}"

                    }
                }
            ]
        }
    })


# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
