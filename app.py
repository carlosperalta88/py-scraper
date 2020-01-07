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
from report.csv_parser import parser

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
            exe = Executor('roles')
            response = Responder()
            role = exe.format_scrapped_data(exe.execute_scraper())
            update_role = response.update_role(role)
            app.logger.info(update_role)
            return
        except Exception as e:
            app.logger.error(e)
            return


@client.task()
def retry_scraping():
    with app.app_context():
        try:
            app.logger.info('start scrapping')
            exe = Executor('failed_roles')
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
        queue = Queue('roles')
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
        if request.args.get('queue') == 'roles':
            start_scraping.apply_async(countdown=5)

        if request.args.get('queue') == 'failed_roles':
            retry_scraping.apply_async(countdown=5)

        app.logger.info('will start scrapping')
        return jsonify(message='Starting...'), 202
    except Exception as e:
        app.logger.error(e)
        return handle_500(e)


@app.route('/report/generate', methods=['POST'])
def generate_report():
    try:
        data = request.json['data']
        parser(data)
        return jsonify(code='201'), 201
    except Exception as e:
        app.logger.error(e)
        return handle_500(e)


@app.route('/scraper/count', methods=['GET'])
def get_queue_length():
    try:
        queue_name = request.args.get('name')
        q = Queue(queue_name)
        list_length = q.get_list_length(queue_name)
        return jsonify(listName=queue_name, listLength=list_length, code=200), 200
    except Exception as e:
        app.logger.error(e)
        return handle_500(e)


if __name__ == "__main__":
    handler = RotatingFileHandler('logs.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True)
