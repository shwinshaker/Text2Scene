# Text2Scene

## Requirements
* python3

## Installation

```
pip install -r 'requirements.txt'
```

* If `hunspell` not install correctly, please refer to [spacy_hunspell](https://github.com/tokestermw/spacy_hunspell/blob/master/README.md) and manually install it.

* Necessary models in spacy needs to be downloaded.

## Run
```
cd app
export FLASK_APP=demo.py
export FLASK_ENV=development # if development mode
python -m flask run --host=0.0.0.0
```
The default port is 5000.


