import os
import re
from job_offer_analyzer import log_message

def extract_keywords(text):
    # Simple keyword extraction
    keywords = set(re.findall(r'\b[A-Za-z-]+\b', text.lower()))
    return keywords

def calculate_match_score(job_offer_keywords, profile_keywords):
    # Simple matching based on keyword intersection (replace with more sophisticated logic if needed)
    intersection = set(job_offer_keywords) & set(profile_keywords)
    return len(intersection) / len(job_offer_keywords) * 100 if job_offer_keywords else 0

def review_profile(job_offer_html_file, optimized_profile_md_file, job_folder):
    with open(job_offer_html_file, "r") as f:
        job_offer_html = f.read()
    with open(optimized_profile_md_file, "r") as f:
        optimized_profile = f.read()

    job_offer_keywords = extract_keywords(job_offer_html)
    profile_keywords = extract_keywords(optimized_profile)

    match_score = calculate_match_score(job_offer_keywords, profile_keywords)
    missing_keywords = list(job_offer_keywords - set(profile_keywords))

    with open(os.path.join(job_folder, f"score_{match_score:.2f}"), "w") as f:
        f.write(str(match_score))

    suggestions = [
        "Add more specific examples of your accomplishments.",
        "Quantify your achievements whenever possible.",
        "Tailor your skills to match the job description more closely."
    ]

    review = f"## Review\n\nMatch Score: {match_score:.2f}%\n\nMissing Keywords:\n- " + "\n- ".join(missing_keywords) + "\n\nSuggestions for Improvement:\n- " + "\n- ".join(suggestions)

    review_file_path = os.path.join(job_folder, "review.md")
    try:
        with open(review_file_path, "w") as f:
            f.write(review)
        log_message(os.path.join(job_folder, "job_application.log"), f"Successfully wrote review to file: {review_file_path}")
    except Exception as e:
        log_message(os.path.join(job_folder, "job_application.log"), f"Error writing review to file: {e}")
        print(f"Error writing review to file: {e}")
        return "rejected: Could not write review file"

    # Check for subtitle
    if not re.search(r"^## .+$", optimized_profile, re.MULTILINE):
        return "rejected: Incorrect subtitle"

    # Check for Kurzprofil length
    kurzprofil_match = re.search(r"(?s)# Kurzprofil\n(.+?)\n#", optimized_profile)
    if kurzprofil_match:
        kurzprofil_content = kurzprofil_match.group(1)
        num_lines = len(kurzprofil_content.splitlines())
        if num_lines > 10:
            return "rejected: Kurzprofil zu lang"

    # Check for unwanted sections
    if re.search(r"# AI Experience & Ambitionen|# Leistungen|# Nehmen Sie Kontakt mit mir auf", optimized_profile):
        return "rejected: Unwanted sections found"

    if match_score < 70:
        return f"rejected: Match score too low ({match_score:.2f}%)"

    return "approved"


def main(job_folder):
    job_offer_html_file = os.path.join(job_folder, "job_offer.html")
    optimized_profile_md_file = os.path.join(job_folder, "optimized_profile.md")
    status = review_profile(job_offer_html_file, optimized_profile_md_file, job_folder)
    print(f"REVIEW_STATUS: {status}")
    return status


if __name__ == "__main__":
    # Example usage (replace with inter-agent communication)
    job_folder = "Job_ExampleTitle"
    main(job_folder)
