
import json

from flask import Flask, jsonify, request, abort
from flask.helpers import make_response
from flask.wrappers import Response
from flask_cors import CORS
import numpy as np
import portfolio_analyzer as pa


app = Flask(__name__)
CORS(app)


@app.route('/portfolio/', methods=['POST'])
def upload_report():
    rbody = request.json
    scrips = set(rbody.get("scrips", []))
    if not scrips:
        return error400(0)
    print(scrips)
    portfolios = pa.create_portfolios(scrips)
    return jsonify([port.serialize for port in portfolios])


@app.errorhandler(400)
def error400(error):
    return make_response(jsonify({'error': 'Request body may not be correct'}), 400)


@app.errorhandler(404)
def not_found(error):
    print("eror", error)
    return make_response(jsonify({'error': '404 Not found'}), 404)


if __name__ == '__main__':
    app.run(debug=True, port='8080')
