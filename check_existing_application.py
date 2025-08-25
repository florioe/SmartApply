#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

def log_message(log_file_path, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write("[{}] {}\n".format(timestamp, message))
    print("Log: {}".format(message))

def extract_keywords_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_meta:
        keywords_str = keywords_meta.get('content', '')
        return [kw.strip().lower() for kw in keywords_str.split(',') if kw.strip()]
    return []

def extract_project_id_from_url(url):
    match = re.search(r'/projekt/(\w+)', url)
    if match:
        return match.group(1)
    return None

def check_existing_applications(current_job_offer_html_path, current_job_offer_url_path, beworben_dir, log_file_path):
    log_message(log_file_path, "Starting check for existing applications.")

    try:
        with open(current_job_offer_html_path, 'r', encoding='utf-8') as f:
            current_html_content = f.read()
        current_keywords = extract_keywords_from_html(current_html_content)
        log_message(log_file_path, "Current job offer keywords: {}".format(', '.join(current_keywords)))
    except Exception as e:
        log_message(log_file_path, "Error reading current job offer HTML or extracting keywords: {}".format(e))
        return "Error: Could not read current job offer HTML or extract keywords."

    try:
        with open(current_job_offer_url_path, 'r', encoding='utf-8') as f:
            current_url = f.read().strip()
        current_project_id = extract_project_id_from_url(current_url)
        log_message(log_file_path, "Current job offer URL: {}".format(current_url))
        log_message(log_file_path, "Current job offer Project ID: {}".format(current_project_id))
    except Exception as e:
        log_message(log_file_path, "Error reading current job offer URL or extracting project ID: {}".format(e))
        return "Error: Could not read current job offer URL or extract project ID."

    cutoff_date = datetime.now() - timedelta(days=14)
    log_message(log_file_path, "Checking for applications not older than: {}".format(cutoff_date.strftime('%Y-%m-%d')))

    for root, dirs, files in os.walk(beworben_dir):
        for file in files:
            if file == 'original_url.txt':
                app_url_path = os.path.join(root, file)
                try:
                    with open(app_url_path, 'r', encoding='utf-8') as f:
                        app_url = f.read().strip()
                    app_project_id = extract_project_id_from_url(app_url)

                    # Get modification date of the directory (or a file within it)
                    # Using the directory's modification time as a proxy for application date
                    dir_mtime = datetime.fromtimestamp(os.path.getmtime(root))

                    if dir_mtime < cutoff_date:
                        log_message(log_file_path, "Skipping old application in {} (modified on {})".format(root, dir_mtime.strftime('%Y-%m-%d')))
                        continue

                    log_message(log_file_path, "Found application: {} (Project ID: {}, Modified: {})".format(app_url, app_project_id, dir_mtime.strftime('%Y-%m-%d')))

                    if current_project_id and app_project_id == current_project_id:
                        log_message(log_file_path, "MATCH: Project ID '{}' already processed in {}. Stopping process.".format(current_project_id, root))
                        return "MATCH: Project ID already processed."

                    # Check for keyword match if no project ID match
                    app_html_path = os.path.join(root, 'job_offer.html')
                    if os.path.exists(app_html_path):
                        with open(app_html_path, 'r', encoding='utf-8') as f:
                            app_html_content = f.read()
                        app_keywords = extract_keywords_from_html(app_html_content)
                        
                        if current_keywords and app_keywords:
                            common_keywords = set(current_keywords).intersection(set(app_keywords))
                            match_percentage = (len(common_keywords) / len(current_keywords)) * 100 if current_keywords else 0
                            
                            log_message(log_file_path, "Comparing keywords for {}: Current: {}, App: {}, Common: {}, Match: {:.2f}%".format(root, len(current_keywords), len(app_keywords), len(common_keywords), match_percentage))

                            if match_percentage >= 80:
                                log_message(log_file_path, "MATCH: Keywords match by {:.2f}% for application in {}. Asking user to proceed.".format(match_percentage, root))
                                return "ASK_USER: Keywords match by {:.2f}% for application in {}. Do you want to proceed?".format(match_percentage, root)

                except Exception as e:
                    log_message(log_file_path, "Error processing application in {}: {}".format(root, e))
                    continue
    
    log_message(log_file_path, "No matching existing applications found.")
    return "No match."

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python check_existing_application.py <current_job_offer_html_path> <current_job_offer_url_path> <beworben_dir> <log_file_path>")
        sys.exit(1)

    current_job_offer_html_path = sys.argv[1]
    current_job_offer_url_path = sys.argv[2]
    beworben_dir = sys.argv[3]
    log_file_path = sys.argv[4]

    result = check_existing_applications(current_job_offer_html_path, current_job_offer_url_path, beworben_dir, log_file_path)
    print(result)
