import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from collections import Counter

# Ensure NLTK is set up
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Load environment variables (optional, if you have URLs stored in .env file)
load_dotenv(override=True)

# User-Agent for web scraping
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# Class for scraping website data
class Website:
    def __init__(self, url):
        """Create a Website object using BeautifulSoup."""
        self.url = url
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.title = "Error: Unable to fetch website content"
            self.text = ""

# Text summarization using NLTK
class Summarizer:
    def __init__(self, text):
        self.text = text

    def summarize(self, num_sentences=3):
        # Tokenize into sentences
        sentences = sent_tokenize(self.text)

        # Tokenize words and calculate frequency
        words = word_tokenize(self.text.lower())
        stop_words = set(stopwords.words("english"))
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        word_freq = Counter(filtered_words)

        # Score sentences based on word frequency
        sentence_scores = {}
        for sentence in sentences:
            for word in word_tokenize(sentence.lower()):
                if word in word_freq:
                    sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_freq[word]

        # Sort and extract top sentences
        top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        return "\n".join(top_sentences)

# Function to display summary
def display_summary(url):
    website = Website(url)
    print(f"Website Title: {website.title}")
    print("Fetching summary...")
    if website.text:
        summarizer = Summarizer(website.text)
        summary = summarizer.summarize()
        print("Generated Summary:")
        print(summary)
    else:
        print("No content available to summarize.")

# Call the function with a URL
display_summary("https://www.infosys.com")
