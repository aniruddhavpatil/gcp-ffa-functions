from flask import Flask
from flask import request
from flask import make_response
app = Flask(__name__)

@app.route('/')
def hello_world(request):
    return make_response(({'lit': 'stuff'}, {'Access-Control-Allow-Origin': '*'}))