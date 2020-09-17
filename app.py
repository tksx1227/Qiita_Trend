import os
import re
import json
import threading

import mojimoji
from flask import Flask, request, abort, jsonify
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

import setting
from qiita_scraper import get_trend_info, set_session

app = Flask(__name__)

line_bot_api = LineBotApi(setting.LINE_CHANNEL_ACCESS_TOKEN)  # チャネルアクセストークン
handler = WebhookHandler(setting.LINE_CHANNEL_SECRET)  # チャネルシークレット
user_id = setting.USER_ID   # ユーザーID


def make_message(info):
    scope = info["scope"]
    reply = f"【{scope[0].upper() + scope[1:]} Trend】\n"
    for title, likes, url in zip(info["title"], info["likes_count"], info["url"]):
        with open("reply_template.txt", "r") as f:
            text = f.read()
            reply += text.format(title=title, likes=likes, url=url)

    return reply


@app.route("/")
def index():
    return "Hello World!"


@app.route("/alexa/prepare", methods=["GET"])
def prepare():
    thread = threading.Thread(target=set_session)
    thread.start()
    return "SET SESSION."


@app.route("/alexa/ask-info", methods=["POST", "GET"])
def ask_info():
    scope = request.args.get("scope", default="daily", type=str)
    max_amount = request.args.get("max_amount", default=5, type=int)
    info = get_trend_info(scope, max_amount)

    return jsonify(info)


@app.route("/alexa/send-message", methods=["POST", "GET"])
def send_message():
    trend_info = request.args.get("trend_info", default=None)

    if trend_info is None:
        print("No message")
        return "No message"

    trend_info = json.loads(trend_info)
    message = make_message(trend_info)

    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=message)
    )

    return "SUCCESS."


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.reply_token == "00000000000000000000000000000000":
        return

    message = mojimoji.zen_to_han(event.message.text.lower(), kana=False)

    # 期間を抽出
    if re.match(".*(日|デイリー|daily).*", message):
        scope = "daily"
    elif re.match(".*(週|ウィークリー|weekly).*", message):
        scope = "weekly"
    elif re.match(".*(月|マンスリー|monthly).*", message):
        scope = "monthly"
    else:
        scope = None

    # scopeがある場合、記事数を取得
    if scope is None:
        return "No reply"
    else:
        max_amount = re.search("[0-9]+[(つ|こ|個|本|記事)]", message)
        if max_amount is not None:
            max_amount = int(re.search("[0-9]+", max_amount.group()).group())
        else:
            max_amount = 5

    info = get_trend_info(scope, max_amount)
    info["scope"] = scope
    reply = make_message(info)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.debug = True  # デバッグモード有効化
    app.run(host="0.0.0.0", port=port)
