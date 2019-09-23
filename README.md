# Text2Scene

## Requirements
* python3

## Installation

```
pip install -r 'requirements.txt'
```

* If `hunspell` not install correctly, please refer to [spacy_hunspell](https://github.com/tokestermw/spacy_hunspell/blob/master/README.md) and manually install it.

* `hunspell` requires to specify the path of the dictionary `en_US.dic`. Normally on linux is `/usr/share/hunspell`. Check `lib/tools/text_process.py` to change accordingly.

* Necessary models for `spaCy` needs to be downloaded, such as `en_core_web_sm` and `en_core_web_md`.

## Offline demo
```
demo.py <text_input>
```

## Backend (flask)
```
export FLASK_APP=app.py
export FLASK_ENV=development # if development mode
python -m flask run --host=0.0.0.0
```
The default port is 5000.

## Frontend (React)

### Installation
```
cd ui
yarn add react-bootstrap bootstrap
yarn add react-d3 d3 # not actually used
```

### Run
```
cd ui
yarn start
```

The default port is 3000.

