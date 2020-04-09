from flask import Flask, jsonify, request, json
import logging
from logging.handlers import RotatingFileHandler
from celery import Celery
from werkzeug.exceptions import HTTPException, InternalServerError
from urllib.parse import unquote
import functools

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']

from handler.api import Responder
from report.csv_parser import parser
from scraper.scraper import Scraper
from scraper.formatter import Formatter

client = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
client.conf.update(app.config)


def compose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


@client.task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def start_scraping(role):
    with app.app_context():
        try:
            app.logger.info('start scrapping')
            response = Responder()
            scraper = Scraper()
            formatter = Formatter()

            print(unquote(role))
            if role:
                result_role = compose(formatter.formatter, scraper.scrape)(unquote(role))
                update_role = response.update_role(result_role)
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
        role = request.json['roles']
        if role:
            start_scraping.apply_async(role, countdown=5)
            return jsonify(message='role added', code=201)
        app.logger.error('could not save roles')
        return jsonify(error='Ooops... Something went wrong', code=500)
    except Exception as e:
        print(e.args[0])
        app.logger.error(e.args[0])
        return jsonify(error=e.args[0], code=500)


@app.route('/report/generate', methods=['POST'])
def generate_report():
    try:
        data = request.json['data']
        parser(data)
        return jsonify(code='201'), 201
    except Exception as e:
        app.logger.error(e)
        return handle_500(e)


if __name__ == "__main__":
    handler = RotatingFileHandler('logs.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True)
