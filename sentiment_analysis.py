from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = {
        'polarity': blob.polarity,
        'subjectivity': blob.subjectivity
    }
    return sentiment
