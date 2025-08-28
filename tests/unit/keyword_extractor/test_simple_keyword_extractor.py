import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))  # Adjust for src layout

from src.smartapply.keyword_extractor.simple_keyword_extractor import extract_keywords_from_html_simple

def test_extract_keywords_from_html_simple_with_valid_html():
    # Use the test data from resources
    test_file = os.path.join(os.path.dirname(__file__), "resources", "test_data.html")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    actual_keywords = extract_keywords_from_html_simple(html_content)
    
    # Basic validation - should extract some keywords
    assert isinstance(actual_keywords, set)
    assert len(actual_keywords) > 0
    
    # Check that common expected keywords are present
    expected_keywords = {'projektmanagement', 'consultant', 'senior', 'agilen', 'methoden', 'beratung'}
    for keyword in expected_keywords:
        assert keyword in actual_keywords
