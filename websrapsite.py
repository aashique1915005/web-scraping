import requests
from bs4 import BeautifulSoup
from collections import Counter


class Website:
    def __init__(self, url):
        """Create a Website object that extracts basic info (title and content) using BeautifulSoup."""
        self.url = url
        self.title = None
        self.text = None
        self.error = None
        self.soup = None

        # Define headers to mimic a real browser for requests
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            )
        }

        # Try to fetch the webpage content and parse it
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()  # Will raise an exception for HTTP errors
            self.soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the title of the webpage
            self.title = self.soup.title.string if self.soup.title else "No title found"

            # Remove irrelevant tags (scripts, styles, images, inputs, etc.)
            for irrelevant in self.soup.find_all(["script", "style", "img", "input"]):
                irrelevant.decompose()

            # Get the remaining text content from the page
            self.text = self.soup.get_text(separator="\n", strip=True)

        except requests.exceptions.RequestException as e:
            self.error = f"Error fetching {url}: {e}"

    def get_title(self):
        """Returns the title of the webpage."""
        return self.title

    def get_text(self):
        """Returns the main text content of the webpage."""
        return self.text

    def get_error(self):
        """Returns error message if the webpage failed to load."""
        return self.error

    def get_company_details(self):
        """Extract additional information like overview, services, contact, about us, and who we are."""
        details = {
            'Overview': self.extract_section(['overview', 'about']),
            'Services': self.extract_section(['services', 'solutions']),
            'Contact': self.extract_section(['contact', 'contact us']),
            'About Us': self.extract_about_us(),
            'Who We Are': self.extract_who_we_are()
        }
        return details

    def extract_section(self, keywords):
        """Search for sections related to the keywords and extract."""
        for keyword in keywords:
            # Find all elements containing the keyword in their text
            sections = self.soup.find_all(string=lambda text: text and keyword.lower() in text.lower())
            if sections:
                # Try to find a parent section and return the text content
                parent_section = sections[0].find_parent(['section', 'div'])
                if parent_section:
                    return parent_section.get_text(separator="\n", strip=True)
        return f"Section not found for {', '.join(keywords)}."

    def extract_about_us(self):
        """Check for 'About Us' section and extract relevant text."""
        return self.extract_section(['about us'])

    def extract_who_we_are(self):
        """Check for 'Who We Are' section and extract relevant text."""
        return self.extract_section(['who we are'])


def summarize_text(text, word_limit=200):
    """Summarize the text by extracting key sentences based on word frequency, ensuring the word limit is respected."""
    words = text.split()
    word_counts = Counter([word.lower() for word in words if word.isalpha()])
    most_common_words = [word for word, _ in word_counts.most_common(50)]

    sentences = text.split("\n")

    sentence_scores = []
    for sentence in sentences:
        sentence_score = sum(1 for word in sentence.split() if word.lower() in most_common_words)
        sentence_scores.append((sentence_score, sentence))

    ranked_sentences = sorted(sentence_scores, reverse=True, key=lambda x: x[0])

    summary = []
    word_count = 0

    for _, sentence in ranked_sentences:
        words_in_sentence = sentence.split()
        if word_count + len(words_in_sentence) <= word_limit:
            summary.append(sentence)
            word_count += len(words_in_sentence)
        else:
            break

    return ' '.join(summary)


if __name__ == "__main__":
    # Example Usage
    url = "https://www.cognizant.com"  # Replace with the website URL you want to scrape
    website = Website(url)

    if website.error:
        print(f"Error: {website.error}")
    else:
        print(f"Website Title: {website.get_title()}")

        # Summarize website content
        content = website.get_text()
        print(f"\nWebsite Content Summary :\n{summarize_text(content)}\n")

        # Get company details
        details = website.get_company_details()

        print("\nCompany Details:")
        print(f"Overview: {details['Overview']}")
        print(f"Services: {details['Services']}")

        print(f"Contact: {details['Contact']}")
        print(f"About Us: {details['About Us']}")
        print(f"Who We Are: {details['Who We Are']}")