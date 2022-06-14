"""
オウム返し Line Bot
"""

import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
)
import boto3

client = boto3.client('rekognition')

handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))


def lambda_handler(event, context):
    headers = event["headers"]
    body = event["body"]

    # get X-Line-Signature header value
    signature = headers['x-line-signature']

    # handle webhook body
    handler.handle(body, signature)

    return {"statusCode": 200, "body": "OK"}


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """ TextMessage handler """
    input_text = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=input_text))


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    file_path = '/tmp/sent-image.jpg'
    with open(file_path, 'wb') as fd:  # 送られてきたイメージをファイルに書き込んで保存している
        for chunk in message_content.iter_content():
            fd.write(chunk)

    # Rekognition　で感情分析する
    with open(file_path, 'rb') as fd:
        sent_image_binary = fd.read()
        response = client.detect_faces(Image={'Bytes': sent_image_binary},
                                       Attributes=['ALL']
                                       )
    def all_happy(result):
        for detail in result["FaceDetails"]:
            if most_confident_emotion(detail["Emotions"]) !="HAPPY":
                return False
        return True

    def most_confident_emotion(emotions):

        max_conf = 0
        result =""
        for e in emotions:
            if max_conf < e["Confidence"]:
                max_conf = e["Confidence"]
                result = e["Type"]
        return result

    #メッセージの内容
    if all_happy(response):
        message = "all happy!!"

    else:
        message = "uh soso"

    # 返答を送信する
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))
    # file_path の画像を削除
    os.remove(file_path)
