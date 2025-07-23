import os
import uuid
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def generate_captcha():
    a, b = random.randint(1, 9), random.randint(1, 9)
    return (f"{a} + {b}", str(a + b))

@app.route('/', methods=['GET', 'POST'])
def index():
    captcha_question, captcha_answer = generate_captcha()
    if request.method == 'POST':
        if request.form['captcha_answer'] != request.form['captcha_expected']:
            return render_template('index.html', error='Неверный ответ на капчу.', captcha_question=captcha_question, captcha_expected=captcha_answer)

        direction = request.form['direction']
        stripe_width = int(request.form['stripe_width'])
        file = request.files['image']
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(path)

        img = Image.open(path).convert("RGB")
        arr = np.array(img)

        plt.figure()
        for i, color in enumerate(['r', 'g', 'b']):
            plt.hist(arr[:, :, i].ravel(), bins=256, color=color, alpha=0.5)
        hist_path = path.replace(".jpg", "_hist.png").replace(".png", "_hist.png")
        plt.savefig(hist_path)
        plt.close()

        processed = swap_stripes(arr, direction, stripe_width)
        result_path = path.replace(".jpg", "_result.jpg").replace(".png", "_result.jpg")
        Image.fromarray(processed).save(result_path)

        return render_template('index.html',
                               original_image=path,
                               result_image=result_path,
                               hist_image=hist_path,
                               captcha_question=captcha_question,
                               captcha_expected=captcha_answer)

    return render_template('index.html', captcha_question=captcha_question, captcha_expected=captcha_answer)

def swap_stripes(image_array, direction, stripe_width):
    img = np.copy(image_array)
    if direction == 'horizontal':
        for i in range(0, img.shape[0], stripe_width * 2):
            if i + stripe_width < img.shape[0]:
                img[i:i + stripe_width], img[i + stripe_width:i + stripe_width * 2] =                     img[i + stripe_width:i + stripe_width * 2], img[i:i + stripe_width].copy()
    else:
        for i in range(0, img.shape[1], stripe_width * 2):
            if i + stripe_width < img.shape[1]:
                img[:, i:i + stripe_width], img[:, i + stripe_width:i + stripe_width * 2] =                     img[:, i + stripe_width:i + stripe_width * 2], img[:, i:i + stripe_width].copy()
    return img

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
