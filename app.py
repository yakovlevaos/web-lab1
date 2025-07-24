import os
import uuid
import random
import traceback
from flask import Flask, render_template, request, session
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import matplotlib

# Используем "Agg" бэкэнд для matplotlib — чтобы не требовался графический интерфейс
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'твой_секретный_ключ_здесь'  # обязательно для работы с сессиями

# Папка для загрузок — в static/uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаём папку для загрузок, если её нет (exist_ok=True — без ошибки, если есть)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Выводим абсолютный путь для уверенности, где создаётся папка
print(f"Upload folder full path: {os.path.abspath(UPLOAD_FOLDER)}")

def generate_captcha():
    # Генерируем простой вопрос капчи — сложение двух чисел
    a, b = random.randint(1, 9), random.randint(1, 9)
    return (f"{a} + {b}", str(a + b))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # При GET-запросе показываем форму и новую капчу
        captcha_question, captcha_answer = generate_captcha()
        session['captcha_answer'] = captcha_answer
        return render_template('index.html', captcha_question=captcha_question)

    # Обработка POST-запроса
    try:
        # Получаем ответ пользователя по капче и ожидаемый ответ из сессии
        captcha_user_answer = request.form.get('captcha_answer')
        captcha_expected = session.get('captcha_answer')

        # Проверяем капчу
        if captcha_user_answer != captcha_expected:
            captcha_question, captcha_answer = generate_captcha()
            session['captcha_answer'] = captcha_answer
            return render_template('index.html', error='Неверный ответ на капчу.',
                                   captcha_question=captcha_question)

        # Получаем остальные параметры формы
        direction = request.form.get('direction')
        stripe_width = int(request.form.get('stripe_width', 10))
        file = request.files.get('image')

        # Проверяем, что файл загружен
        if not file or file.filename == '':
            captcha_question, captcha_answer = generate_captcha()
            session['captcha_answer'] = captcha_answer
            return render_template('index.html', error="Файл не был загружен.",
                                   captcha_question=captcha_question)

        # Безопасное имя файла + уникальный префикс
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"

        # Полный путь для сохранения файла
        path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        print(f"Saving uploaded file to: {path}")  # Вывод пути для проверки

        # Сохраняем файл
        file.save(path)

        # Открываем изображение, конвертируем в RGB и получаем numpy-массив
        img = Image.open(path).convert("RGB")
        arr = np.array(img)

        # Рисуем гистограмму RGB каналов
        plt.figure()
        for i, color in enumerate(['r', 'g', 'b']):
            plt.hist(arr[:, :, i].ravel(), bins=256, color=color, alpha=0.5)
        base, ext = os.path.splitext(path)
        hist_path = base + "_hist.png"
        plt.savefig(hist_path)
        plt.close()

        # Обработка изображения — меняем полосы местами
        processed = swap_stripes(arr, direction, stripe_width)
        result_path = base + "_result.jpg"
        Image.fromarray(processed).save(result_path)

        # Новая капча для формы
        captcha_question, captcha_answer = generate_captcha()
        session['captcha_answer'] = captcha_answer

        # Передаём пути картинок и капчу в шаблон
        return render_template('index.html',
                               original_image=path,
                               result_image=result_path,
                               hist_image=hist_path,
                               captcha_question=captcha_question)

    except Exception:
        # Логируем ошибку на сервере
        error_trace = traceback.format_exc()
        print(error_trace)

        # Новая капча, выводим сообщение об ошибке
        captcha_question, captcha_answer = generate_captcha()
        session['captcha_answer'] = captcha_answer
        return render_template('index.html', error="Произошла внутренняя ошибка, посмотри логи.",
                               captcha_question=captcha_question)

def swap_stripes(image_array, direction, stripe_width):
    """
    Функция меняет местами полосы изображения:
    - Если направление горизонтальное — полосы меняются по вертикали (по строкам)
    - Если вертикальное — полосы меняются по горизонтали (по столбцам)
    """
    img = np.copy(image_array)

    if direction == 'horizontal':
        for i in range(0, img.shape[0], stripe_width * 2):
            if i + stripe_width < img.shape[0]:
                # Меняем полосы местами, копируем, чтобы не потерять данные
                img[i:i + stripe_width], img[i + stripe_width:i + stripe_width * 2] = \
                    img[i + stripe_width:i + stripe_width * 2], img[i:i + stripe_width].copy()
    else:
        for i in range(0, img.shape[1], stripe_width * 2):
            if i + stripe_width < img.shape[1]:
                img[:, i:i + stripe_width], img[:, i + stripe_width:i + stripe_width * 2] = \
                    img[:, i + stripe_width:i + stripe_width * 2], img[:, i:i + stripe_width].copy()

    return img

if __name__ == '__main__':
    app.run(debug=True)
