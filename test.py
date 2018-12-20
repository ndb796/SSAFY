# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
import requests

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, render_template, make_response, jsonify

app = Flask(__name__)

slack_token = "xoxb-503818135714-507455748194-bwVhQAN3e2UQgwGFANR1Jism"
slack_client_id = "503818135714.507349651171"
slack_client_secret = "d106d5ff0c4968740af83e90da3803ab"
slack_verification = "Ry51tzOf9SERuGbNpWdtQ6eN"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_bugs_keywords():
    # 여기에 함수를 구현해봅시다.
    titles = []
    artists = []
    count = 1

    sourcecode = urllib.request.urlopen("https://music.bugs.co.kr/chart").read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    for data in soup.find_all("p", class_="title"):
        titles.append(str(count) + "위: " + data.get_text().strip('\n'))
        count = count + 1
    for data in soup.find_all("p", class_="artist"):
        artists.append(" / " + data.get_text().strip('\n'))

    keywords = []
    for i in range(0, 10):
        keywords.append(titles[i] + artists[i])
    print(keywords)

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        text = text[13:]
        userid = 'session'
        answer = get_answer(text, userid)

        if answer["intent"] == "Bugs Crawling":
            keywords = _crawl_bugs_keywords()
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=answer["speech"] + '\n' + keywords
            )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

def get_answer(text, user_key):
    data_send = {
        'query': text,
        'sessionId': user_key,
        'lang': 'ko',
    }

    data_header = {
        'Authorization': 'Bearer 26b580764fa0442d97ba550af5b8d9fc',
        'Content-Type': 'application/json; charset=utf-8'
    }

    dialogflow_url = 'https://api.dialogflow.com/v1/query?v=20150910'
    res = requests.post(dialogflow_url, data=json.dumps(data_send), headers=data_header)

    if res.status_code != requests.codes.ok:
        return '오류가 발생했습니다.'

    data_receive = res.json()
    result = {
        "speech" : data_receive['result']['fulfillment']['speech'],
        "intent" : data_receive['result']['metadata']['intentName']
    }
    return result

@app.route("/", methods=['GET', 'POST'])
def index():
    # 여기에 함수를 구현해봅시다.
    numbers = []
    titles = []
    artists = []
    count = 1

    sourcecode = urllib.request.urlopen("https://music.bugs.co.kr/chart").read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    for data in soup.find_all("p", class_="title"):
        titles.append(data.get_text().strip('\n'))
        numbers.append(str(count))
        count = count + 1
    for data in soup.find_all("p", class_="artist"):
        artists.append(data.get_text().strip('\n'))

    keywords = []
    for i in range(0, 10):
        keywords.append((numbers[i], titles[i], artists[i]))

    return render_template('index.html', results=keywords)

@app.route("/naver", methods=['GET', 'POST'])
def naver():

    url = "http://www.naver.com"
    req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    list = []

    count = 1
    for naver_text in soup.find_all("span", class_="ah_k"):
        list.append((count, naver_text.get_text()))
        count = count + 1

    print(list)

    return render_template('index2.html', results=list)

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
