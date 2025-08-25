import re
from bs4 import BeautifulSoup
from typing import Set

def extract_keywords_from_html_simple(html_content: str) -> Set[str]:
    """
    Simplified keyword extraction without spacy dependency
    Uses regex patterns to extract German nouns and verbs
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text from description and keywords sections
        description = soup.find('div', class_='description')
        keywords_container = soup.find('div', class_='keywords-container')
        
        text = ""
        if description:
            text += description.get_text(separator='\n', strip=True)
        if keywords_container:
            text += keywords_container.get_text(separator='\n', strip=True)
        
        # Clean text - remove special characters, numbers, etc.
        text = re.sub(r'[^\w\säöüÄÖÜß]', ' ', text)  # Keep German umlauts
        text = re.sub(r'\d+', ' ', text)  # Remove numbers
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        # Extract words that look like German nouns (capitalized) and verbs
        words = text.split()
        keywords = set()
        
        for word in words:
            word_lower = word.lower()
            # Skip short words and common stop words
            if len(word) < 3:
                continue
                
            # Common German stop words
            stop_words = {'der', 'die', 'das', 'und', 'oder', 'für', 'mit', 'von', 'zu', 'auf', 'in', 'aus'}
            if word_lower in stop_words:
                continue
                
            # Add words that are likely nouns (capitalized) or longer words
            if (word[0].isupper() and len(word) > 3) or len(word) > 5:
                keywords.add(word_lower)
        
        return keywords
        
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return set()

def extract_keywords_with_ai_simple(keywords: Set[str]) -> Set[str]:
    """
    Simplified AI keyword extraction placeholder
    In a real implementation, this would call an AI service
    """
    # This is a placeholder - in real implementation, call OpenAI API
    print("AI keyword extraction would be implemented here")
    return keywords
