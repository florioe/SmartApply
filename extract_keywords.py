import re
import sys

def extract_keywords(job_description_file, cv_file, output_file):
    with open(job_description_file, 'r', encoding='utf-8') as f:
        job_description = f.read()

    with open(cv_file, 'r', encoding='utf-8') as f:
        cv_content = f.read()

    # This is a simple keyword extraction, it can be improved.
    keywords = set(re.findall(r'\b[A-Za-z-]+\b', job_description.lower()))
    cv_words = set(re.findall(r'\b[A-Za-z-]+\b', cv_content.lower()))

    missing_keywords = keywords - cv_words

    with open(output_file, 'w', encoding='utf-8') as f:
        for keyword in sorted(list(missing_keywords)):
            f.write(keyword + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extract_keywords.py <job_description_file> <cv_file> <output_file>")
        sys.exit(1)
    
    job_description_file = sys.argv[1]
    cv_file = sys.argv[2]
    output_file = sys.argv[3]
    
    extract_keywords(job_description_file, cv_file, output_file)
