import os
import requests
from flask import Flask, render_template, request
from core import db

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# from models import Result

@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}
    if request.method == "POST":
        # get url that the user has entered
        # try:
        print('request')
        url = request.form['url']
        r = requests.get(url)
        print(r.text)
        # print(text)
        # except:
        #    errors.append(
        #        "Unable to get URL. Please make sure it's valid and try again."
        #    )
    return render_template('index.html', errors=errors, results=results)


if __name__ == '__main__':
    app.run()
