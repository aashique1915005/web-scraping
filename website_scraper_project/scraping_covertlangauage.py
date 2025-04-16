import time
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from urllib.parse import urlparse
import re
import json
from deep_translator import GoogleTranslator

# Setup logging
logging.basicConfig(filename='translation_errors.log', level=logging.ERROR)

visited_urls = set()
TARGET_KEYWORDS = ["about", "who-we-are", "company"]
MAX_URL_DEPTH = 3  # Max number of path segments (e.g., /about-us/ = 1)

# === Utility Functions ===

def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

def get_url_depth(url):
    path = urlparse(url).path
    return len([segment for segment in path.strip('/').split('/') if segment])

def close_cookie_popup(page):
    selectors = [
        "button:has-text('Accept')",
        "button:has-text('I Accept')",
        "button:has-text('OK')",
        "div[class*='cookie'] button",
        "[aria-label*='Accept']",
        "button[class*='cookie']"
    ]
    for sel in selectors:
        try:
            button = page.query_selector(sel)
            if button:
                button.click()
                time.sleep(1)
                break
        except:
            continue

def remove_unwanted_elements(page):
    tags_to_remove = ["script", "style", "img", "input"]
    for tag in tags_to_remove:
        try:
            page.eval_on_selector_all(tag, "els => els.forEach(el => el.remove())")
        except:
            continue

def safe_goto(page, url, max_retries=3):
    for i in range(max_retries):
        try:
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"Goto failed ({i+1}/{max_retries}): {e}")
            time.sleep(2)
    return False

def scrape_page_text(page, url):
    info = {"url": url}
    try:
        print(f"\nScraping: {url}")
        if not safe_goto(page, url):
            info["error"] = "Page load failed after retries"
            return info
        page.wait_for_selector("body", timeout=5000)
        close_cookie_popup(page)
        remove_unwanted_elements(page)
        text = page.inner_text("body")
        info["page_content"] = text
    except Exception as e:
        info["error"] = str(e)
    return info

def is_target_link(href):
    try:
        parsed = urlparse(href)
        return any(kw in parsed.path.lower() for kw in TARGET_KEYWORDS)
    except:
        return False

def summarize_paragraphs(text, num_sentences=3):
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 60]
    summarized = []
    for para in paragraphs:
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\؟|\!)\s', para)
        if len(sentences) <= num_sentences:
            summarized.append(para)
        else:
            summarized.append(' '.join(sentences[:num_sentences]))
    return summarized

def detect_and_translate(text, retries=3, delay=5):
    MAX_CHAR_LIMIT = 4999
    translated_text = ""
    text_chunks = [text[i:i + MAX_CHAR_LIMIT] for i in range(0, len(text), MAX_CHAR_LIMIT)]

    for chunk in text_chunks:
        attempt = 0
        while attempt < retries:
            try:
                translated_text += GoogleTranslator(source='auto', target='en').translate(chunk) + "\n"
                break
            except Exception as e:
                attempt += 1
                print(f"Translation attempt {attempt} failed: {e}")
                logging.error(f"Translation attempt {attempt} failed for chunk: {chunk}. Error: {e}")
                if attempt < retries:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print("Max retries reached. Skipping translation.")
                    translated_text += chunk + "\n"

    return translated_text.strip()

def scrape_company_info(start_url, max_depth=1):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        stealth_sync(page)

        def recurse(url, depth):
            normalized_url = normalize_url(url)
            if normalized_url in visited_urls or depth > max_depth:
                return []
            if get_url_depth(normalized_url) > MAX_URL_DEPTH:
                return []

            visited_urls.add(normalized_url)
            info = scrape_page_text(page, normalized_url)
            results = [info]

            if info.get("page_content"):
                summarized_paras = summarize_paragraphs(info["page_content"])
                info["summarized_content"] = summarized_paras
                translated = [detect_and_translate(p) for p in summarized_paras]
                info["translated_content"] = translated

            try:
                links = page.eval_on_selector_all("a", "elements => elements.map(el => el.href)")
                valid_links = [
                    href for href in links
                    if href.startswith("http")
                       and "linkedin.com" not in href.lower()
                       and is_target_link(href)
                       and normalize_url(href) not in visited_urls
                       and get_url_depth(href) <= MAX_URL_DEPTH
                ]
                for link in valid_links:
                    results.extend(recurse(link, depth + 1))
            except Exception as e:
                logging.error(f"Failed to extract links from {url}: {e}")

            return results

        all_info = recurse(start_url, depth=0)
        browser.close()
        return all_info

# === Run Script ===
if __name__ == "__main__":
    start_url = "https://www.beroepskaart.be/nl"  # Replace with your target URL
    info = scrape_company_info(start_url, max_depth=1)

    for page in info:
        print("\n" + "=" * 100)
        print(f"Context: Scraping company page for: {page.get('url')}")
        print("\nSUMMARY (Paragraphs):")
        for para in page.get("summarized_content", []):
            print(f"- {para}")
        print("\nTRANSLATED CONTENT (Paragraphs):")
        for para in page.get("translated_content", []):
            print(f"- {para}")

    with open("scraped_about_company_info_with_summary.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
