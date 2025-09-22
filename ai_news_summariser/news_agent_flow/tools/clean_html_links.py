import re
from bs4 import BeautifulSoup

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