from flask import Flask, request, jsonify
import pickle
import numpy as np

# загружаем модель из файла
with open('./models/model.pkl', 'rb') as pkl_file:
    loaded_model = pickle.load(pkl_file)

# создаём приложение
app = Flask(__name__)

@app.route('/')
def index():
    msg = "Test message. The server is running!!!"
    return msg

@app.route('/predict', methods=['POST'])
def predict():
    try:
        features = request.json
        features = np.array(features).reshape(1, -1)
        print(features.shape)

        prediction = float(loaded_model.predict(features)[0])

        return jsonify({
            "prediction": prediction
        })
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# $ uwsgi --http :5000 --module server:app
#Разберём аргументы.
#Аргумент http :5000 указывает, что uWSGI должен обрабатывать HTTP-запросы на порте 5000.
#При необходимости перед двоеточием можно указать хост — localhost, 127.0.0.1 для локального запуска 
# (он используется по умолчанию, если ничего не указано) или 0.0.0.0, 
# чтобы сервис был доступен по всем сетевым интерфейсам.
#Аргумент server:app указывает, какое приложение будет запускать uWSGI: модуль server.py (до двоеточия) 
# и объект app внутри этого модуля (после двоеточия).

# Один PID процесс основной, когда запустили приложение и дочерний который слушает входящие запросы:
# $ uwsgi --http :5000 --module server:app

# Запустим сервер с 4-мя процессами:
# $ uwsgi --http :5000 --processes 4 --master --module server:app
# И посмотрим через Linux утилиту кол-ство проццесов на нашем сервере uWSGI :
# $ htop -t

# uwsgi --ini uwsgi_config.ini

# Но и это ещё не всё. Как мы уже отметили, на скриншотах, полученных с помощью htop и после запуска uwsgi, 
# видно, что процессов не четыре, а пять. Откуда взялся ещё один? 
# Этот последний процесс является HTTP-роутером, который слушает HTTP-трафик и отправляет 
# его на воркеры (рабочие процессы), то есть он выступает в роли пункта-распределителя.

# Однако uWSGI — это не самая оптимальная реализация HTTP-роутера. 
# Она существует скорее для отладки веб-разработчиками, что не является нашей зоной компетенции, 
# поэтому сами авторы uWSGI советуют использовать полноценный веб-сервер. И тут появляется NGINX.

# На сегодняшний день NGINX поддерживает протокол uwsgi, что позволяет приложениям WSGI, 
# запущенным на uWSGI, лучше взаимодействовать с NGINX.