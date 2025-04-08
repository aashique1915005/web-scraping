import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

# Load environment variables
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Check the API key
if not api_key:
    print("No API key was found!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start with 'sk-proj-'.")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have spaces or tabs at the start or end.")
else:
    print("API key found and looks good so far!")

# Initialize OpenAI client
openai = OpenAI()

# Function to interact with OpenAI API
def chat_with_openai(message):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

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
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

# Prompts for OpenAI
system_prompt = (
    "You are an assistant that analyzes the contents of a website and provides a short summary, "
    "ignoring text that might be navigation related. Respond in markdown."
)

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}.\n"
    user_prompt += "The contents of this website are as follows. Please provide a short summary in markdown.\n\n"
    user_prompt += website.text
    return user_prompt

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

def summarize(url):
    website = Website(url)
    print(f"Website Title: {website.title}")
    print(f"Website Text (sample): {website.text[:500]}")  # Debugging: print the first 500 characters
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for(website)
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during summarization: {e}"

def display_summary(url):
    summary = summarize(url)
    print("Generated Summary:")
    print(summary)

# Call the function
display_summary("https://www.infosys.com")
