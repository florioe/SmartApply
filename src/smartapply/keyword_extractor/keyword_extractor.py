import re
import spacy
from bs4 import BeautifulSoup
import os
import re
import spacy
from bs4 import BeautifulSoup
from typing import Set
from openai import OpenAI

nlp = spacy.load("de_core_news_sm")

def extract_keywords_from_html(html_content: str) -> Set[str]:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Extract keywords from the description and keywords sections
        description = soup.find('div', class_='description')
        keywords_container = soup.find('div', class_='keywords-container')
        text = ""
        if description:
            text += description.get_text(separator='\n', strip=True)
        if keywords_container:
            text += keywords_container.get_text(separator='\n', strip=True)

        doc = nlp(text)
        keywords = set()
        for token in doc:
            if token.pos_ in ("NOUN", "VERB"):
                keywords.add(token.lemma_)
        return keywords
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return set()

def extract_keywords_with_ai(keywords: Set[str]) -> Set[str]:
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment variables.")
            return keywords

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts keywords from a text."},
                {"role": "user", "content": f"Extract keywords from the following text: {', '.join(keywords)}"}
            ]
        )
        extracted_keywords = set(response.choices[0].message.content.split(", "))
        return extracted_keywords
    except Exception as e:
        print(f"Error extracting keywords with AI: {e}")
        return keywords
