import os
import uuid
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Используем бэкенд matplotlib для сохранения графиков без GUI
import matplotlib.pyplot as plt
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'  # Папка для сохранения загруженных файлов
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Функция для генерации простой капчи (сложение двух чисел)
def generate_captcha():
    a, b = random.randint(1, 9), random.randint(1, 9)
    return (f"{a} + {b}", str(a + b))

@app.route('/', methods=['GET', 'POST'])
def index():
    # Генерируем новый вопрос и ответ капчи
    captcha_question, captcha_answer = generate_captcha()

    if request.method == 'POST':
        # Проверяем правильность ответа на капчу
        if request.form['captcha_answer'] != request.form['captcha_expected']:
            return render_template('index.html', error='Неверный ответ на капчу.',
                                   captcha_question=captcha_question, captcha_expected=captcha_answer)

        # Получаем параметры из формы
        direction = request.form['direction']  # направление полос (horizontal/vertical)
        stripe_width = int(request.form['stripe_width'])  # ширина полос
        file = request.files['image']  # загруженный файл изображения

        # Создаем безопасное имя файла и полный путь для сохранения
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(path)  # сохраняем файл

        # Открываем изображение и конвертируем в RGB
        img = Image.open(path).convert("RGB")
        arr = np.array(img)  # переводим изображение в numpy-массив

        # Создаем гистограмму распределения цветов по каналам
        plt.figure()
        for i, color in enumerate(['r', 'g', 'b']):
            plt.hist(arr[:, :, i].ravel(), bins=256, color=color, alpha=0.5)
        hist_path = path.replace(".jpg", "_hist.png").replace(".png", "_hist.png")
        plt.savefig(hist_path)  # сохраняем гистограмму
        plt.close()

        # Применяем функцию перестановки полос
        processed = swap_stripes(arr, direction, stripe_width)
        result_path = path.replace(".jpg", "_result.jpg").replace(".png", "_result.jpg")
        Image.fromarray(processed).save(result_path)  # сохраняем обработанное изображение

        # Отправляем на рендеринг шаблон с путями к изображениям и капчей
        return render_template('index.html',
                               original_image=path,
                               result_image=result_path,
                               hist_image=hist_path,
                               captcha_question=captcha_question,
                               captcha_expected=captcha_answer)

    # При GET-запросе просто отображаем форму с капчей
    return render_template('index.html', captcha_question=captcha_question, captcha_expected=captcha_answer)

# Функция для перестановки полос изображения по горизонтали или вертикали
def swap_stripes(image_array, direction, stripe_width):
    img = np.copy(image_array)  # копируем массив, чтобы не менять исходный

    if direction == 'horizontal':
        # Переставляем полосы по горизонтали
        for i in range(0, img.shape[0], stripe_width * 2):
            if i + stripe_width < img.shape[0]:
                # Меняем местами две соседние полосы
                img[i:i + stripe_width], img[i + stripe_width:i + stripe_width * 2] = \
                    img[i + stripe_width:i + stripe_width * 2], img[i:i + stripe_width].copy()
    else:
        # Переставляем полосы по вертикали
        for i in range(0, img.shape[1], stripe_width * 2):
            if i + stripe_width < img.shape[1]:
                # Меняем местами две соседние вертикальные полосы
                img[:, i:i + stripe_width], img[:, i + stripe_width:i + stripe_width * 2] = \
                    img[:, i + stripe_width:i + stripe_width * 2], img[:, i:i + stripe_width].copy()

    return img  # возвращаем обработанный массив

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # создаем папку для загрузок, если ее нет
    app.run(debug=True)  # запускаем приложение в режиме отладки

