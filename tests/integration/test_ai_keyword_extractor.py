import unittest
import os
from keyword_extractor.keyword_extractor import extract_keywords_with_ai

class TestAIKeywordExtractor(unittest.TestCase):

    def test_extract_keywords_with_ai_placeholder(self):
        # TODO: Implement this test with a real AI model
        # API key should be set via environment variable, not hardcoded
        if "OPENAI_API_KEY" not in os.environ:
            self.skipTest("OPENAI_API_KEY environment variable not set")
            
        keywords = {"projektmanagement", "agile", "methoden", "senior", "it", "consultant", "projekt", "management", "methodenmodellen", "aufgabe", "beratung"}
        extracted_keywords = extract_keywords_with_ai(keywords)
        #self.assertEqual(extracted_keywords, keywords)
        self.assertTrue(len(extracted_keywords) > 0)

if __name__ == '__main__':
    unittest.main()
