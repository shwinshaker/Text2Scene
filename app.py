from flask import Flask, request, jsonify, make_response
from flask_restplus import Api, Resource, fields
from sklearn.externals import joblib
import numpy as np
import os
import sys
import time
import glob
from lib.models.predictor import Predict1
from lib.tools.text_process import Spell, Check
from lib.tools.image_process import stack_svgs

flask_app = Flask(__name__)
app = Api(app = flask_app,
          version = "1.0",
          title = "text2scene",
          description = "generate scene from text")

name_space = app.namespace('prediction', description='Prediction APIs')
model = app.model('Prediction params',
                  {'text': fields.String(required = True,
                                         description="input text",
                                         help="input text can not be blank")})

generate = Predict1()
# asciiCheck = Check()
spell = Spell(path='extras/google-10000-english-usa-no-swears.txt')

def clean_results(d='static/img'):
    for svg in glob.glob('%s/*.svg' % d):
        os.remove(svg)
    for png in glob.glob('%s/*.png' % d):
        os.remove(png)

def get_response(status='', path='', corrections={}):
    response = jsonify({"statusCode": 200,
                        "status": status,
                        "path": path,
                        "corrections": corrections})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def to_object(corrections):
    json = {}
    for token in corrections:
        json[token.text] = {}
        json[token.text]['id'] = token.i
        json[token.text]['suggestions'] = corrections[token]
    return json

@name_space.route("/")
class MainClass(Resource):
    def options(self):
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

    @app.expect(model)
    def post(self):
        clean_results()
        try:
            formData = request.json
            text = formData['text'].strip('\n').lower()
            print(formData)

            # correction
            corrections = spell(text)
            print(corrections)
            if corrections:
                print(to_object(corrections))
                return get_response(status='Corrections suggested',
                                    corrections=to_object(corrections))
            # generation
            pictures = generate(text, top=3, with_graph=False)
            print(pictures)
            files = []
            root = 'static/img'
            for i, pic in enumerate(pictures):
                print(i)
                materials = ['dataset/material/%s.png' % l.s for l in pic]
                # URI = '%.7f' % time.time()
                URI = '-'.join(text.split()) + str(i)
                print(URI)
                opt_file = '%s/%s.svg' % (root, URI)
                print('output to: %s' % opt_file)
                files.append(opt_file)
                stack_svgs(materials, opt_file=opt_file)
            return get_response(status='Prediction made',
                                path=['http://127.0.0.1:5000/' + f for f in files])

        except Exception as error:
            return jsonify({
                "statusCode": 500,
                "status": "Could not make prediction",
                "error": str(error)})
