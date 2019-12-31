from flask import Flask, jsonify, request, json
import logging
from logging.handlers import RotatingFileHandler
from celery import Celery
from werkzeug.exceptions import HTTPException, InternalServerError

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']


from scraper.executor import Executor
from handler.data import Queue
from handler.api import Responder
client = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
client.conf.update(app.config)


@client.task()
def start_scraping():
    with app.app_context():
        try:
            app.logger.info('start scrapping')
            exe = Executor()
            response = Responder()
            role = exe.format_scrapped_data(exe.execute_scraper())
            update_role = response.update_role(role)
            app.logger.info(update_role)
            return
        except Exception as e:
            app.logger.error(e)
            return


@app.errorhandler(HTTPException)
def handler_exception(e):
    response = e.get_response(e)
    response.data = json.dumps({
        'code': e.code,
        'name': e.name,
        'description': e.description
    })
    response.content_type = 'application/json'
    return response


@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, 'original_exception', None)
    response = {}

    if original is None:
        response.data = json.dumps({
            'code': 500,
            'name': 'Internal Server Error'
        })

        return response

    response.data = json.dumps({
        'code': 500,
        'name': 'Internal Server Error',
        'description': original
    })

    return response


@app.route('/')
def hello():
    return 'Not Found'


@app.route('/scraper/add', methods=['POST'])
def add_to_scraper_queue():
    try:
        roles = request.json['roles']
        queue = Queue()
        response = queue.queue_roles(roles)
        if response == 201:
            app.logger.info('roles saved')
            return jsonify(message='saved', code=201)
        app.logger.error('could not save roles')
        return jsonify(error='Ooops... Something went wrong', code=500)
    except Exception as e:
        print(e.args[0])
        app.logger.error(e.args[0])
        return jsonify(error=e.args[0], code=500)


@app.route('/scraper/execute', methods=['GET'])
def start_async_scraper():
    try:
        start_scraping.apply_async(countdown=5)
        app.logger.info('will start scrapping')
        return jsonify({'message': 'Starting...'}), 202
    except Exception as e:
        app.logger.error(e)
        return handle_500(e)


if __name__ == "__main__":
    handler = RotatingFileHandler('logs.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True)
