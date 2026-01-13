import os
import threading
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, StickerSendMessage

app = Flask(__name__)

# ดึงค่าจาก Environment Variable (ที่เราจะไปตั้งใน Render)
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# ตัวเก็บตัวนับเวลาแยกตามกลุ่ม
timers = {}

def send_sticker(group_id):
    """ฟังก์ชันส่งสติ๊กเกอร์เมื่อครบ 2 นาที"""
    try:
        line_bot_api.push_message(
            group_id,
            StickerSendMessage(package_id='11538', sticker_id='51626501') # รูปคนยกนิ้ว CHOCO&Friend
        )
    except Exception as e:
        print(f"Error: {e}")
    
    if group_id in timers:
        del timers[group_id]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # หา ID ของกลุ่ม หรือ ห้องแชท
    if event.source.type == 'group':
        group_id = event.source.group_id
    elif event.source.type == 'room':
        group_id = event.source.room_id
    else:
        group_id = event.source.user_id

    # ถ้ามีการส่งภาพใหม่เข้ามา ให้ยกเลิกตัวนับเวลาเดิม (ถ้ามี)
    if group_id in timers:
        timers[group_id].cancel()

    # เริ่มนับถอยหลังใหม่ 120 วินาที (2 นาที)
    t = threading.Timer(120.0, send_sticker, args=[group_id])
    timers[group_id] = t
    t.start()

if __name__ == "__main__":
    # รันบน Port ที่ Render กำหนด
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
