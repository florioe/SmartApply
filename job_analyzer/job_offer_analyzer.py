import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from keyword_extractor.keyword_extractor import extract_keywords_from_html

def extract_job_offer_details(html_content):
    """
    Extracts job offer details from HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True).replace('auf www.freelancermap.de', '').strip() if title_tag else 'N/A'

    project_id_dt = soup.find('dt', string='Project ID:')
    project_id_tag = project_id_dt.find_next_sibling('dd') if project_id_dt else None
    project_id = project_id_tag.get_text(strip=True) if project_id_tag else 'N/A'

    keywords = []
    keywords_container = soup.find('div', class_='keywords-container')
    if keywords_container:
        keyword_spans = keywords_container.find_all('span', class_='keyword')
        keywords = [span.get_text(strip=True) for span in keyword_spans]

    description_container = soup.find('div', class_='description')
    description_div = description_container.find('div', itemprop='description') if description_container else None
    description = description_div.get_text(separator='\n', strip=True) if description_div else 'N/A'

    published_date_tag = soup.find('div', itemprop='datePosted')
    published_date_str = published_date_tag.get_text(strip=True) if published_date_tag else 'N/A'
    published_date = datetime.strptime(published_date_str, '%d.%m.%Y') if published_date_str != 'N/A' else None

    return {
        'title': title,
        'project_id': project_id,
        'keywords': keywords,
        'description': description,
        'published_date': published_date
    }

def check_for_duplicate_job_offers(current_job_offer, beworben_path, log_file_path):
    """
    Checks for duplicate job offers in the 'beworben' directory.
    """
    log_message(log_file_path, "Scanning for duplicate job offers in: {}".format(beworben_path))
    
    current_project_id = current_job_offer['project_id']
    #current_keywords = current_job_offer['keywords']
    current_keywords = extract_keywords_from_html(current_job_offer['description'])
    
    found_duplicates = []

    for root, _, files in os.walk(beworben_path):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        html_content = f.read()
                    
                    job_details = extract_job_offer_details(html_content)
                    
                    # Check date (not older than 14 days)
                    if job_details['published_date']:
                        age = datetime.now() - job_details['published_date']
                        if age > timedelta(days=14):
                            continue # Skip if older than 14 days

                    # Check project ID
                    if job_details['project_id'] == current_project_id and current_project_id != 'N/A':
                        log_message(log_file_path, "Duplicate found by Project ID: {} (ID: {})".format(job_details['title'], job_details['project_id']))
                        found_duplicates.append({'type': 'project_id', 'details': job_details})
                        continue

                    # Check keywords similarity
                    #if current_keywords and job_details['keywords']:
                    # Create a single string from keywords for fuzzy matching
                    #current_kw_str = " ".join(current_keywords).lower()
                    #found_kw_str = " ".join(job_details['keywords']).lower()
                    found_kw_str = " ".join(extract_keywords_from_html(job_details['description'])).lower()
                    
                    similarity = fuzz.ratio(current_kw_str, found_kw_str)
                    if similarity >= 80:
                        log_message(log_file_path, "Duplicate found by Keyword Similarity ({}%): {}".format(similarity, job_details['title']))
                        found_duplicates.append({'type': 'keywords', 'details': job_details, 'similarity': similarity})
                            
                except Exception as e:
                    log_message(log_file_path, "Error processing file {}: {}".format(file_path, e))
                    
    return found_duplicates

def log_message(log_file, message):
    """Appends a message to the log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as f:
        f.write("[{}] {}\n".format(timestamp, message))
    print("LOG: {}".format(message))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze job offer and check for duplicates.")
    parser.add_argument('current_job_offer_path', type=str, help='Path to the current job offer HTML file.')
    parser.add_argument('beworben_base_path', type=str, help='Base path to the directory containing previously applied job offers.')
    parser.add_argument('log_file_path', type=str, help='Path to the log file.')
    
    args = parser.parse_args()

    log_message(args.log_file_path, "Starting job offer analysis.")

    try:
        with open(args.current_job_offer_path, 'r') as f:
            current_html_content = f.read()
        
        current_job_details = extract_job_offer_details(current_html_content)
        log_message(args.log_file_path, "Current Job Offer Title: {}".format(current_job_details['title']))
        log_message(args.log_file_path, "Current Job Offer Project ID: {}".format(current_job_details['project_id']))
        log_message(args.log_file_path, "Current Job Offer Keywords: {}".format(', '.join(current_job_details['keywords'])))
        log_message(args.log_file_path, "Current Job Offer Published Date: {}".format(current_job_details['published_date'].strftime('%d.%m.%Y') if current_job_details['published_date'] else 'N/A'))

        duplicates = check_for_duplicate_job_offers(current_job_details, args.beworben_base_path, args.log_file_path)

        if duplicates:
            log_message(args.log_file_path, "Found potential duplicate job offers:")
            for dup in duplicates:
                if dup['type'] == 'project_id':
                    log_message(args.log_file_path, "- Match by Project ID: {} (ID: {})".format(dup['details']['title'], dup['details']['project_id']))
                elif dup['type'] == 'keywords':
                    log_message(args.log_file_path, "- Match by Keywords (Similarity: {}%): {}".format(dup['similarity'], dup['details']['title']))
            
            # If project ID matches, stop the process
            if any(d['type'] == 'project_id' for d in duplicates):
                log_message(args.log_file_path, "Process stopped: Exact Project ID match found.")
                print("STOP_PROCESS: Exact Project ID match found. No further processing.")
            else:
                # If keywords match >= 80%, ask to proceed
                keyword_matches = [d for d in duplicates if d['type'] == 'keywords' and d['similarity'] >= 80]
                if keyword_matches:
                    log_message(args.log_file_path, "Asking user to proceed: High keyword similarity found.")
                    print("ASK_PROCEED: High keyword similarity found. Do you want to proceed? (Yes/No)")
                else:
                    log_message(args.log_file_path, "No significant duplicates found. Proceeding with the task.")
                    print("PROCEED: No significant duplicates found. Proceeding with the task.")
        else:
            log_message(args.log_file_path, "No duplicate job offers found. Proceeding with the task.")
            print("PROCEED: No duplicate job offers found. Proceeding with the task.")

    except FileNotFoundError: # Changed from IOError back to FileNotFoundError for Python 3.x compatibility
        log_message(args.log_file_path, "Error: Job offer HTML file not found at {}".format(args.current_job_offer_path))
        print("ERROR: Job offer HTML file not found at {}".format(args.current_job_offer_path))
    except Exception as e:
        log_message(args.log_file_path, "An unexpected error occurred: {}".format(e))
        print("ERROR: An unexpected error occurred: {}".format(e))
