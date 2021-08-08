import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = 'http://localhost:5000/'
    header['Access-Control-Allow-Headers'] = 'Authorization,Content-Type, true'
    header['Access-Control-Allow-Methods'] = 'POST,GET,PUT,DELETE,PATCH,OPTIONS'
    return response


# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = [i.short() for i in Drink.query.all()]
    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = [i.long() for i in Drink.query.all()]
    except Exception:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(payload):
    try:
        new_drink = Drink(title=json.loads(request.data.decode('utf-8'))['title'], recipe=json.dumps(json.loads(request.data.decode('utf-8'))['recipe']))
        Drink.insert(new_drink)
        drink = [new_drink.long()]

        return jsonify({
            "success": True,
            "drinks": drink
        }), 200
    except exc.SQLAlchemyError:
        abort(422)
    except Exception:
        abort(503)


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    try:
        drink_to_update = Drink.query.filter(id == id)
        title = request.get_json().get('title', None)
        drink_to_update.title = title

        recipe = request.get_json().get('recipe', None)
        drink_to_update.recipe = recipe

        drink_to_update.update()
        drink = [drink_to_update.long()]

        return jsonify({
            "success": True,
            "drinks": drink
        }), 200
    except Exception:
        abort(404)
    except exc.SQLAlchemyError:
        abort(422)


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    try:
        drink_to_delete = Drink.query.filter(Drink.id == id)

        drink_to_delete.delete()

        return jsonify({
            'success': True,
            'delete': id
        })
    except exc.SQLAlchemyError:
        abort(503)
    except Exception:
        abort(422)


# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    'success': False,
                    'error': 400,
                    'message': 'Bad Request'
                    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    'success': False,
                    'error': 404,
                    'message': 'Resources Not Found'
                    }), 404


@ app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
                    'success': False,
                    'error': 405,
                    'message': 'Method Not Allowed'
                    }), 405


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
                    'success': False,
                    'error': 500,
                    'message': 'Internal Server Error'
                    }), 500


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
