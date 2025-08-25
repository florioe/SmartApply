#!/usr/bin/env python3
"""
Test script to demonstrate keyword extraction without AI
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))  # Adjust for src layout

from src.smartapply.keyword_extractor.simple_keyword_extractor import extract_keywords_from_html_simple

def main():
    # Read test data
    test_file = 'src/smartapply/keyword_extractor/resources/test_data.html'
    
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} not found")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("Testing keyword extraction from HTML...")
    print("=" * 50)
    
    # Extract keywords using simple method
    keywords = extract_keywords_from_html_simple(html_content)
    
    print(f"Extracted {len(keywords)} keywords:")
    print("=" * 50)
    
    # Display keywords in a readable format
    for i, keyword in enumerate(sorted(keywords), 1):
        print(f"{i:3d}. {keyword}")
    
    print("=" * 50)
    print(f"Total keywords extracted: {len(keywords)}")

if __name__ == "__main__":
    main()
