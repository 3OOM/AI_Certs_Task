from flask import Flask, request, jsonify
import pandas as pd
import requests
import os
import logging
from dotenv import load_dotenv

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
load_dotenv()
# Groq API details
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.getenv("GROQ_API_KEY")
def perform_sentiment_analysis(reviews):
    total_positive, total_negative, total_neutral = 0, 0, 0
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    for review in reviews:
        payload = {
            "model": "mixtral-8x7b-32768",  # I used this model
            "messages": [
                {"role": "system", "content": "You are a sentiment analysis expert. Classify the sentiment of the following text as positive, negative, or neutral."},
                {"role": "user", "content": review}
            ],
            "temperature": 0
        }

        logging.info(f"Sending request to Groq API: {GROQ_API_URL}")
        logging.info(f"Payload: {payload}")
        
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            logging.error(f"Error in Groq API request: {response.status_code}")
            logging.error(f"Response content: {response.text}")
            continue

        result = response.json()
        sentiment = result['choices'][0]['message']['content'].lower()
        
        if 'positive' in sentiment:
            total_positive += 1
        elif 'negative' in sentiment:
            total_negative += 1
        else:
            total_neutral += 1

    return {
        "positive": total_positive,
        "negative": total_negative,
        "neutral": total_neutral
    }

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    # Get the uploaded file from the request
    file = request.files.get('file')

    # Check if a file was provided
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    # Handle XLSX and CSV file formats
    if file.filename.lower().endswith('.csv'):
        reviews = pd.read_csv(file)
    elif file.filename.lower().endswith('.xlsx'):
        reviews = pd.read_excel(file)
    else:
        return jsonify({'error': f'Unsupported file format: {file.filename}'}), 400

    # Check if the 'Review' column exists
    if 'Review' not in reviews.columns:
        return jsonify({'error': 'Missing "Review" column in file'}), 400

    # Extract review texts from the 'Review' column
    reviews_text = reviews['Review'].tolist()

    # Limit to 50 reviews if more are provided
    reviews_text = reviews_text[:50]

    # Perform sentiment analysis using Groq API
    sentiment_results = perform_sentiment_analysis(reviews_text)

    return jsonify(sentiment_results), 200

if __name__ == '__main__':
    app.run(debug=True)