import re
from bs4 import BeautifulSoup
import html

def clean_web_content(html_content: str) -> str:
    # Remove any markdown-style URLs [text](url)
    html_content = re.sub(r'\[([^\]]+)\]\((https?:\/\/[^\)]+)\)', r'\1', html_content)

    # Use BeautifulSoup to parse and clean up
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted tags like script, style, img, iframe, a
    for tag in soup(["script", "style", "img", "iframe", "a"]):
        tag.decompose()

    # Get plain text
    text = soup.get_text(separator='\n')

    # Remove URLs (http, https, ftp, etc.)
    text = re.sub(r'https?://\S+', '', text)

    # Remove multiple newlines and excessive whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)

    # Optional: Strip leading/trailing whitespace
    return text.strip()

def clean_html_and_entities(text):
    # Remove HTML using BeautifulSoup (better than regex for real HTML)
    soup = BeautifulSoup(text, "html.parser")
    text_no_html = soup.get_text(separator=' ')
    
    # Decode HTML entities (e.g., &amp;, &#39;)
    text_unescaped = html.unescape(text_no_html)
    
    # Remove unicode control characters, excess whitespace
    text_cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text_unescaped)  # remove control chars
    text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()  # normalize whitespace

    return text_cleaned