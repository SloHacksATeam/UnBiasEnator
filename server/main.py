from flask import Flask, redirect, render_template, request
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from .util import assets
from PyDictionary import PyDictionary

app = Flask(__name__)


@app.route('/')
def homepage():
    # Return a Jinja2 HTML template and pass in image_entities as a parameter.
    return render_template('homepage.html')

@app.route('/run_language', methods=['GET', 'POST'])
def run_language():
    #Max sentiment you want to allow
    SENTIMENT_THRESHOLD = 0.3
    # Create a Cloud Natural Language client.
    client = language.LanguageServiceClient()
    dictionary=PyDictionary()
    # Retrieve inputs and create document object
    text = request.form['text']
    output = {}

    initScores = analyze_sentiment(text, client)
    output["origEmotion"] = initScores[0]
    output["origMagnitude"] = initScores[1]
    
    tokens = text.split(" ")
    #Remove non-alphanumeric values
    for i in range(len(tokens)):
        tokens[i] = onlyASCII(tokens[i])

    subjects = entities_text(text, client)
    new_query = normalize_query(tokens, subjects, client, dictionary, SENTIMENT_THRESHOLD)
    suggested_search = " ".join(new_query)
    output["suggested"] = suggested_search
    newScores = analyze_sentiment(suggested_search, client)
    output["newEmotion"] = newScores[0]
    output["newMagnitude"] = newScores[1]

    return render_template('homepage.html', text=text, output = output)

def analyze_sentiment(text, client):
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)
    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment
    return (sentiment.score, sentiment.magnitude)

#Will return a set of subjects detected within text
def entities_text(text, client):
    text = text.decode('utf-8')

    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects entities in the document. You can also analyze HTML with:
    #   document.type == enums.Document.Type.HTML
    entities = client.analyze_entities(document).entities
    subjects = set()
    for entity in entities:
        subjects.add(entity.name)
    return subjects

def lowest_mag(list, client, original, thresh):
    min_i = -1
    readings = analyze_sentiment(original, client)
    min_mag = abs(readings[0]) + readings[1]
    for i in range(0, len(list)):
        readings = analyze_sentiment(list[i], client)
        mag = abs(readings[0]) + readings[1]
        if mag < min_mag:
            min_mag = mag
            min_i  = i
    if min_i == -1:
        return original
    if min_mag > thresh:
        return None
    
    return list[min_i]

def normalize_query(list, subjects, client, dictionary, thresh):
    new_query = []
    for i in range(len(list)):
        word = list[i]
        if word not in subjects:
            synonyms = dictionary.synonym(word)
            if synonyms != None:
                new_word = lowest_mag(dictionary.synonym(word), client, word, thresh)
                if new_word != None:
                    new_query.append(new_word)
            else:
                new_query.append(word)
        else:
            new_query.append(word)
    return new_query

def onlyASCII(text):
    return ''.join([x for x in text if ((ord(x) >= 48 and ord(x) <= 57) or (ord(x) >= 65 and ord(x) <= 90) or (ord(x)>= 97 and ord(x) <= 122))])

@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
