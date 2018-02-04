# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from PyDictionary import PyDictionary
from flask import Flask

app = Flask('__main__')
@app.route('/')

# Returns tuple of the sentiment score and its magnitude
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
	min_mag = abs(analyze_sentiment(original, client)[1])
	for i in range(0, len(list)):
		mag = analyze_sentiment(list[i], client)[1]
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


def main():
	#Max sentiment you want to allow
	SENTIMENT_THRESHOLD = 0.2

	# Instantiates a client
	client = language.LanguageServiceClient()
	dictionary=PyDictionary()

	text = u'who is the worst human being'
	initScores = analyze_sentiment(text, client)
	print("Original text:")
	print(text)
	print("Emotion: {} \nMagnitude: {}".format(initScores[0], initScores[1]))
	
	tokens = text.split(" ")
	#Remove non-alphanumeric values
	for i in range(len(tokens)):
		tokens[i] = onlyASCII(tokens[i])

	subjects = entities_text(text, client)
	new_query = normalize_query(tokens, subjects, client, dictionary, SENTIMENT_THRESHOLD)
	suggested_search = " ".join(new_query)
	print("Alternate text:")
	print(suggested_search)

if __name__ == "__main__":
	main()