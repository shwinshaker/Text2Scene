#!./env python
import time
import glob
import os
from tools.common import wait
from tools.common import static_vars

from tools.image_process import stack_svgs
from models.pipeline import Translate
translate = Translate(img_dir='../images', dict_dir='..')

from flask import Flask, request, render_template, send_from_directory, url_for
app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello, World!'

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/results/<imgname>')
# def display(imgname):
#     return render_template('index.html', imgname=imgname)

def clean_results(d='results'):
    for svg in glob.glob('static/%s/*.svg' % d):
        os.remove(svg)

@app.route('/', methods=['GET', 'POST'])
def index():
    text = ''
    imgname = ''
    error = ''
    if request.method == "POST":

        """
        we can instantiate a translate each time posting.
        But that would consume two much time
        """
        clean_results()

        """
        turn this into a reset method like threading module
        """
        print('---------- exit last instance!')
        # translate.ground.exit.set()
        # translate.metric.exit.set()
        translate.ground.exit = True
        translate.metric.exit = True
        wait(2)
        # while not translate.ground.exited:
        #     print(translate.ground.exited)
        #     time.sleep(1)
        #     # wait(1)
        ### this will never work because sys.exit terminate the entire process
        ### thus metric.exited will never be set to True
        # while not translate.metric.exited:
        #     print(translate.ground.exited)
        #     time.sleep(1)
        #     # wait(1)
        print('---------- start new instance!')
        translate.ground.exited = False
        translate.metric.exited = False
        # translate.ground.exit.clear()
        # translate.metric.exit.clear()
        translate.ground.exit = False
        translate.metric.exit = False

        text = request.form['url'].strip('\n')
        print(text)
        materials = ['../material/%s.png' % l.s for l in translate(text)]
        if not materials:
            imgname = 'results/error.gif'
            error='Material not found..'
        else:
            # unique name to prevent loading from cache
            URI = '%.7f' % time.time()
            opt_file='static/results/%s.svg' % URI
            print('output to: %s' % opt_file)
            stack_svgs(materials, opt_file=opt_file)
            imgname = 'results/%s.svg' % URI
    return render_template('index.html', text=text, imgname=imgname, error=error)

if __name__ == '__main__':
    app.run()
