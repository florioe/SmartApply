import os
import re
import logging
import spacy
from bs4 import BeautifulSoup
from typing import Set, List, Optional, Dict, Tuple
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Language models mapping
LANGUAGE_MODELS = {
    'en': 'en_core_web_sm',
    'de': 'de_core_news_sm'
}

# Structural elements to remove from HTML
STRUCTURAL_ELEMENTS = ['header', 'footer', 'nav', 'aside', 'script', 'style']
STRUCTURAL_SELECTORS = [
    '#header', '#footer', '#navigation', '#nav', '#sidebar',
    '#menu', '#breadcrumb', '#pagination', '#social-media',
    '#advertisement', '#ads', '#banner',
    '.header', '.footer', '.navigation', '.nav', '.sidebar',
    '.menu', '.breadcrumb', '.pagination', '.social-media',
    '.advertisement', '.ads', '.banner', '.cookie', '.consent'
]

def extract_keywords_from_html(html_content: str, language: str = 'en') -> Set[str]:
    """
    Extract keywords from HTML content using spaCy NLP processing.
    Supports both English and German languages.
    
    Args:
        html_content: HTML string to extract keywords from
        language: Language code ('en' for English, 'de' for German)
        
    Returns:
        Set of extracted keywords with original casing preserved
    """
    if not html_content or html_content.strip() == "":
        logger.warning("Empty HTML content provided")
        return set()
        
    # Load appropriate spaCy model
    if language not in LANGUAGE_MODELS:
        logger.warning(f"Unsupported language: {language}. Defaulting to English.")
        language = 'en'
        
    try:
        nlp = spacy.load(LANGUAGE_MODELS[language])
    except OSError:
        logger.error(f"spaCy model {LANGUAGE_MODELS[language]} not installed. "
                    f"Please run: python -m spacy download {LANGUAGE_MODELS[language]}")
        return set()
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove structural elements using predefined constants
    for element in soup.find_all(STRUCTURAL_ELEMENTS):
        element.decompose()
    
    # Remove structural elements by CSS selectors
    for selector in STRUCTURAL_SELECTORS:
        for element in soup.select(selector):
            element.decompose()
    
    # Extract clean text content
    text = soup.get_text(separator='\n', strip=True)
    
    if not text or text.strip() == "":
        logger.warning("No meaningful text content found in HTML")
        return set()
    
    # Clean up text while preserving special characters for both languages
    text = re.sub(r'\n\s*\n', '\n', text)  # Remove multiple empty lines
    text = re.sub(r'\s+', ' ', text)       # Normalize whitespace
    
    logger.info(f"Processing {language.upper()} text of length: {len(text)} characters")
    
    # Process text with spaCy
    doc = nlp(text)
    
    # Extract meaningful keywords (nouns, proper nouns, verbs)
    keywords = set()
    for token in doc:
        if (token.pos_ in ["NOUN", "PROPN", "VERB"] and 
            not token.is_stop and 
            not token.is_punct and
            len(token.text) > 2):
            # Keep original casing for better readability
            keywords.add(token.text)
    
    logger.info(f"Extracted {len(keywords)} keywords using spaCy {language.upper()} model")
    return keywords

def extract_keywords_with_ai(keywords: Set[str], original_text: str = "", 
                           model: str = "gpt-3.5-turbo", return_categorized: bool = False) -> Set[str]:
    """
    Enhance and refine keywords using AI with categorization support.
    Can return either a simple set of keywords or categorized keywords.
    
    Args:
        keywords: Set of initial keywords to refine
        original_text: Optional original text for better context
        model: OpenAI model to use for keyword extraction
        return_categorized: If True, returns categorized keywords with categories
        
    Returns:
        Set of refined keywords (or categorized dict if return_categorized=True)
    """
    try:
        if not keywords:
            logger.warning("No keywords provided for AI enhancement")
            return set() if not return_categorized else {}
            
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return keywords if not return_categorized else {kw: "Uncategorized" for kw in keywords}

        client = OpenAI(api_key=api_key)
        
        # Create a comprehensive prompt based on the example
        prompt = f"""
        Du bist ein KI-Assistent für CV-Optimierung.

        Hier ist eine Roh-Liste von extrahierten Nomen/Verben:
        {', '.join(sorted(keywords))}

        {'Hier ist der vollständige Text zur besseren Kontextualisierung:' if original_text else ''}
        {'\"\"\"' + original_text + '\"\"\"' if original_text else ''}

        Bitte extrahiere alle für eine Bewerbung relevanten Schlüsselwörter.
        Nutze die Roh-Liste als Hilfsmittel, aber entscheide auf Basis des Kontexts.

        Regeln:
        - Entferne irrelevante Wörter.
        - Fasse zusammengehörige Begriffe zu sinnvollen Keywords.
        - Zerlege Listenbegriffe (z. B. Programmiersprachen, Frameworks, API-Stile, Container) in Einzelelemente,
          UND behalte den Oberbegriff, falls er relevant ist.
        - Kategorisiere jedes Keyword in eine der Kategorien:
          Fachlich, Methoden & Frameworks, Tools, Zertifizierung, Erfahrungen & Soft Skills, Allgemein.
        - Gib nur die Ergebnisliste im Format "Schlüsselwort\\tKategorie" zurück.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at extracting and refining keywords from professional content. Return only tab-separated keyword-category pairs."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more deterministic results
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        if return_categorized:
            # Parse categorized results
            categorized_keywords = {}
            for line in content.split('\n'):
                if '\t' in line:
                    keyword, category = line.split('\t', 1)
                    cleaned_keyword = keyword.strip()
                    if cleaned_keyword:
                        categorized_keywords[cleaned_keyword] = category.strip()
            
            logger.info(f"AI extracted {len(categorized_keywords)} categorized keywords")
            return categorized_keywords
        else:
            # Extract simple keywords from response
            extracted_keywords = set()
            for line in content.split('\n'):
                if '\t' in line:
                    keyword = line.split('\t')[0].strip()
                    if keyword:
                        extracted_keywords.add(keyword)
                else:
                    # Also handle comma-separated format as fallback
                    for keyword in line.split(','):
                        cleaned_keyword = keyword.strip()
                        if cleaned_keyword:
                            extracted_keywords.add(cleaned_keyword)
            
            logger.info(f"AI extracted {len(extracted_keywords)} refined keywords")
            return extracted_keywords if extracted_keywords else keywords
        
    except Exception as e:
        logger.error(f"Error extracting keywords with AI: {e}")
        return keywords if not return_categorized else {kw: "Uncategorized" for kw in keywords}

def extract_text_from_html(html_content: str) -> str:
    """
    Extract clean text from HTML content, removing structural elements.
    
    Args:
        html_content: HTML string to extract text from
        
    Returns:
        Clean text content
    """
    try:
        if not html_content or html_content.strip() == "":
            return ""
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove structural elements
        for element in soup.find_all(STRUCTURAL_ELEMENTS):
            element.decompose()
        
        # Remove structural elements by CSS selectors
        for selector in STRUCTURAL_SELECTORS:
            for element in soup.select(selector):
                element.decompose()
        
        # Extract clean text content
        text = soup.get_text(separator='\n', strip=True)
        
        if not text or text.strip() == "":
            return ""
        
        # Clean up text while preserving special characters
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return ""

def detect_language(text: str) -> str:
    """
    Simple language detection based on common words.
    Returns 'de' for German, 'en' for English, or defaults to 'en'.
    
    Args:
        text: Text to analyze for language detection
        
    Returns:
        Language code ('en' or 'de')
    """
    if not text:
        return 'en'
    
    text_lower = text.lower()
    
    # Common German words (including umlauts)
    german_indicators = ['der', 'die', 'das', 'und', 'für', 'mit', 'von', 'zu', 'auf', 'ist', 'sind', 
                        'wir', 'sie', 'ich', 'du', 'er', 'es', 'einer', 'eine', 'einem', 'einen',
                        'über', 'under', 'zwischen', 'durch', 'wegen', 'während', 'seit', 'bis',
                        'ä', 'ö', 'ü', 'ß']  # German umlauts and eszett
    
    # Common English words  
    english_indicators = ['the', 'and', 'for', 'with', 'from', 'to', 'on', 'is', 'are', 'of', 'in',
                         'a', 'an', 'this', 'that', 'these', 'those', 'have', 'has', 'had', 'will',
                         'would', 'could', 'should', 'can', 'may', 'might', 'must', 'shall']
    
    # Count occurrences (not just presence)
    german_count = sum(text_lower.count(word) for word in german_indicators)
    english_count = sum(text_lower.count(word) for word in english_indicators)
    
    # Also check for German-specific characters
    has_german_chars = any(char in text_lower for char in ['ä', 'ö', 'ü', 'ß'])
    
    if german_count > english_count or (german_count > 0 and has_german_chars):
        return 'de'
    else:
        return 'en'

def process_job_description(html_content: str, use_ai: bool = True, categorize: bool = False) -> Dict:
    """
    Complete processing pipeline for job descriptions.
    
    Args:
        html_content: HTML content of job description
        use_ai: Whether to use AI enhancement
        categorize: Whether to return categorized keywords
        
    Returns:
        Dictionary with extracted keywords and metadata
    """
    # Extract clean text
    clean_text = extract_text_from_html(html_content)
    if not clean_text:
        return {"keywords": set(), "language": "en", "text_length": 0}
    
    # Detect language
    language = detect_language(clean_text)
    
    # Extract keywords with spaCy
    raw_keywords = extract_keywords_from_html(html_content, language)
    
    # Enhance with AI if requested
    if use_ai:
        if categorize:
            enhanced_keywords = extract_keywords_with_ai(
                raw_keywords, clean_text, return_categorized=True
            )
        else:
            enhanced_keywords = extract_keywords_with_ai(raw_keywords, clean_text)
    else:
        enhanced_keywords = raw_keywords if not categorize else {kw: "Extracted" for kw in raw_keywords}
    
    return {
        "keywords": enhanced_keywords,
        "language": language,
        "text_length": len(clean_text),
        "raw_keywords_count": len(raw_keywords),
        "enhanced_keywords_count": len(enhanced_keywords) if not categorize else len(enhanced_keywords)
    }
