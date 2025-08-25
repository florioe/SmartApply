import requests
from datetime import datetime, timedelta
from job_offer_analyzer import check_for_duplicate_job_offers, log_message, extract_job_offer_details

def is_active_and_recent(url, log_file_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Extract job details for duplicate check
        html_content = response.text
        job_details = extract_job_offer_details(html_content)

        # Check for keywords or elements in the HTML indicating archival or age
        # (Implementation for checking archival and age depends on the website structure)
        # Example: if "archived" in response.text.lower(): return False
        # Example: if job_details['published_date'] < datetime.now() - timedelta(days=2): return False

        return True, job_details  # Return job_details for duplicate check
    except requests.exceptions.RequestException as e:
        log_message(log_file_path, f"Error checking URL {url}: {e}")
        return False, None

def process_job_urls(job_urls_file, beworben_base_path, log_file_path):
    with open(job_urls_file, "r") as f:
        urls = f.readlines()
    urls = [url.strip() for url in urls]
    unique_urls = list(set(urls))

    filtered_urls = []
    for url in unique_urls:
        is_active, job_details = is_active_and_recent(url, log_file_path)
        if is_active:
            duplicates = check_for_duplicate_job_offers(job_details, beworben_base_path, log_file_path)
            if not duplicates:
                filtered_urls.append(url)
            else:
                log_message(log_file_path, f"Skipping duplicate job offer: {url}")


    return filtered_urls


def main():
    job_urls_file = "Context/job-urls.txt"
    log_file_path = "job_application.log"
    beworben_base_path = "Beworben"  # Assuming this is where previous applications are stored

    filtered_urls = process_job_urls(job_urls_file, beworben_base_path, log_file_path)

    for url in filtered_urls:
        print(f"Processing URL: {url}")
        # Pass URL to Optimizer Agent (implementation for inter-agent communication needed)

if __name__ == "__main__":
    main()
