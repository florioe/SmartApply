import json
import os
import re
import shutil
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from generate_documents import convert_md_to_docx # Import the conversion function

# --- Configuration Paths ---
BASE_PROFILE_MD_PATH = '/Users/flo/Library/CloudStorage/OneDrive-Personal/Documents/profil.md'
BASE_PROFILE_DOCX_PATH = '/Users/flo/Library/CloudStorage/OneDrive-Personal/Documents/Profil_v.-Mengershausen-AI-Process-Opt.docx'
EXAMPLE_PO_PROFILE_DOCX_PATH = '/Users/flo/Library/CloudStorage/OneDrive-Personal/Documents/Profil_v.-Mengershausen_Beispiel_Product-Owner.docx'
COVER_LETTER_TEMPLATE_PATH = '/Users/flo/Library/CloudStorage/OneDrive-Personal/Documents/Anschreiben.rtf'
MAIN_APPLICATION_DIR = '/Users/flo/Library/Mobile Documents/com~apple~CloudDocs/flo/Job/Freiberufler/Bewerbungen/2025-05/in Arbeit'
LOCAL_JOB_OFFERS_DIR = '/Users/flo/Library/Mobile Documents/com~apple~CloudDocs/flo/Job/Freiberufler/Bewerbungen/2025-05/zu bewerben'

# --- Personal Information (Placeholders - to be filled by user or inferred) ---
MY_NAME = "Florian von Mengershausen"
MY_MOBILE = "+49 123 456789" # Placeholder
MY_EMAIL = "florian.mengershausen@example.com" # Placeholder

def fetch_with_retries(url, retries=3, delay=10):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=30) # Added timeout
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                print(f"Got status 429 Too Many Requests. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Double the delay for the next retry
            else:
                print(f"Failed to fetch data: {response.status_code} {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
    print("Failed to fetch data after multiple retries.")
    return None

def sanitize_filename(title):
    # Remove invalid characters and replace spaces with hyphens
    s = re.sub(r'[^\w\s-]', '', title).strip()
    s = re.sub(r'[-\s]+', ' ', s) # Replace multiple spaces/hyphens with single space
    return s

def create_project_directory(job_title):
    project_path = os.path.join(MAIN_APPLICATION_DIR, sanitize_filename(job_title))
    os.makedirs(project_path, exist_ok=True)
    return project_path

def save_job_description_files(project_path, job_data):
    job_url = job_data.get('url')
    job_title = job_data.get('projectTitle', 'Job Description')
    
    html_content = ""
    text_content = ""

    if job_url and job_url.startswith('http'):
        print(f"Fetching job description from URL: {job_url}")
        fetched_html = fetch_with_retries(job_url)
        if fetched_html:
            soup = BeautifulSoup(fetched_html, 'html.parser')
            html_content = str(soup.prettify())
            text_content = soup.get_text(separator=' ', strip=True)
        else:
            print(f"Could not fetch content for {job_url}. Using job_data description.")
            text_content = job_data.get('description', '')
            html_content = f"<html><body><h1>{job_title}</h1><pre>{text_content}</pre></body></html>" # Basic HTML fallback
    elif job_url and job_url.startswith('file://'):
        file_path = job_url[len('file://'):]
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if file_path.lower().endswith(('.html', '.htm')):
                    soup = BeautifulSoup(content, 'html.parser')
                    html_content = str(soup.prettify())
                    text_content = soup.get_text(separator=' ', strip=True)
                else: # Assume plain text or markdown
                    text_content = content
                    html_content = f"<html><body><h1>{job_title}</h1><pre>{text_content}</pre></body></html>"
            except Exception as e:
                print(f"Error reading local file {file_path}: {e}")
                text_content = job_data.get('description', '')
                html_content = f"<html><body><h1>{job_title}</h1><pre>{text_content}</pre></body></html>"
        else:
            print(f"Local file not found: {file_path}. Using job_data description.")
            text_content = job_data.get('description', '')
            html_content = f"<html><body><h1>{job_title}</h1><pre>{text_content}</pre></body></html>"
    else: # No URL or invalid URL, use description from job_data
        text_content = job_data.get('description', '')
        html_content = f"<html><body><h1>{job_title}</h1><pre>{text_content}</pre></body></html>"

    # Save HTML file
    job_html_path = os.path.join(project_path, 'job_description.html')
    with open(job_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Save Markdown file with URL and description
    job_md_path = os.path.join(project_path, 'job_details.md')
    with open(job_md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Job Details: {job_title}\n\n")
        if job_url:
            f.write(f"## URL: {job_url}\n\n")
        f.write(f"## Description:\n{text_content}\n")
    
    return text_content # Return the plain text description for profile optimization

def get_profile_sections(profile_content):
    sections = {
        "Kurzprofil": "",
        "Availability": "",
        "Projekthistorie": [],
        "Skills": "",
        "Zertifizierungen": ""
    }
    current_section = None
    project_entry = {}
    
    lines = profile_content.split('\n')
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.lower().startswith("kurzprofil"):
            current_section = "Kurzprofil"
        elif line_stripped.lower().startswith("availability"):
            current_section = "Availability"
        elif line_stripped.lower().startswith("projekthistorie"):
            current_section = "Projekthistorie"
        elif line_stripped.lower().startswith("skills"):
            current_section = "Skills"
        elif line_stripped.lower().startswith("zertifizierungen"):
            current_section = "Zertifizierungen"
        elif line_stripped.startswith("### Projekt:"): # Start of a new project
            if project_entry: # Save previous project if exists
                sections["Projekthistorie"].append(project_entry)
            project_entry = {"title": line_stripped[len("### Projekt:"):].strip(), "details": []}
            current_section = "ProjectDetails"
        elif current_section == "ProjectDetails":
            project_entry["details"].append(line)
        elif current_section:
            if current_section == "Projekthistorie": # Content before first project
                pass # Ignore, actual projects are handled by "### Projekt:"
            else:
                sections[current_section] += line + '\n'
    
    if project_entry: # Add the last project
        sections["Projekthistorie"].append(project_entry)

    # Clean up leading/trailing newlines in sections
    for key in ["Kurzprofil", "Availability", "Skills", "Zertifizierungen"]:
        sections[key] = sections[key].strip()
    
    return sections

def optimize_profile(job_data, base_profile_content, job_description_text):
    job_title = job_data.get('projectTitle', 'Requested Role')
    
    # Extract keywords from job description
    job_keywords = set(re.findall(r'\b\w+\b', job_description_text.lower()))
    
    # Parse base profile
    profile_sections = get_profile_sections(base_profile_content)

    optimized_profile_md = []

    # Title and Contact Data
    optimized_profile_md.append(f"# {MY_NAME} - {job_title}\n")
    optimized_profile_md.append(f"**Mobile:** {MY_MOBILE}\n")
    optimized_profile_md.append(f"**Email:** {MY_EMAIL}\n\n")

    # Kurzprofil
    optimized_profile_md.append("## Kurzprofil\n")
    # Simple approach: include original Kurzprofil and try to inject job-relevant keywords
    # This needs more sophisticated NLP for real optimization
    kurzprofil_content = profile_sections["Kurzprofil"]
    # For now, just append the original Kurzprofil. Advanced logic would rewrite it.
    optimized_profile_md.append(kurzprofil_content + "\n\n")

    # Availability
    optimized_profile_md.append("## Availability\n")
    optimized_profile_md.append(profile_sections["Availability"] + "\n\n")

    # Projekthistorie (Auswahl) - relevant projects
    optimized_profile_md.append("## Projekthistorie (Auswahl)\n")
    relevant_projects = []
    for project in profile_sections["Projekthistorie"]:
        project_text = project["title"].lower() + " ".join(project["details"]).lower()
        # Simple relevance check: if any job keyword is in project text
        if any(keyword in project_text for keyword in job_keywords):
            relevant_projects.append(project)
    
    # Sort projects by start date (assuming date is in project title or details) - reverse chronological
    # This is a placeholder, needs robust date parsing
    relevant_projects.sort(key=lambda x: x["title"], reverse=True) # Sort by title as a proxy for date

    for project in relevant_projects:
        optimized_profile_md.append(f"### Projekt: {project['title']}\n")
        # Shorten project details - for now, just include first few lines or summarize
        # This needs more advanced summarization
        for detail_line in project["details"][:5]: # Take first 5 lines as a "shorten" example
            optimized_profile_md.append(detail_line)
        optimized_profile_md.append("\n")
    optimized_profile_md.append("\n")

    # Skills
    optimized_profile_md.append("## Skills\n")
    # This is a very basic skill matching. A real solution would parse skills from base profile
    # and match them against job keywords, potentially rephrasing.
    profile_skills = set(re.findall(r'\b\w+\b', profile_sections["Skills"].lower()))
    matching_skills = [skill for skill in profile_skills if skill in job_keywords]
    
    # Propose similar skills if appropriate - placeholder logic
    proposed_skills = []
    if "agile" in job_keywords and "scrum" not in profile_skills:
        proposed_skills.append("???Agile Methoden (z.B. Scrum)???")
    
    optimized_profile_md.append(", ".join(matching_skills) + "\n")
    if proposed_skills:
        optimized_profile_md.append("Proposed: " + ", ".join(proposed_skills) + "\n")
    optimized_profile_md.append("\n")

    # Zertifizierungen
    optimized_profile_md.append("## Zertifizierungen\n")
    # Filter relevant certifications based on job keywords
    relevant_certs = []
    certs_content = profile_sections["Zertifizierungen"]
    # Simple keyword match for certs
    for cert_line in certs_content.split('\n'):
        if any(keyword in cert_line.lower() for keyword in job_keywords):
            relevant_certs.append(cert_line)
    
    # Sort certs (placeholder for actual date sorting)
    relevant_certs.sort(reverse=True) # Reverse alphabetical as a proxy

    optimized_profile_md.append("\n".join(relevant_certs) + "\n\n")

    # Appendix for full project history
    optimized_profile_md.append("\n---\n\n") # Page break
    optimized_profile_md.append("## Appendix: Full Projekthistorie\n")
    for project in profile_sections["Projekthistorie"]:
        optimized_profile_md.append(f"### Projekt: {project['title']}\n")
        optimized_profile_md.append("\n".join(project["details"]) + "\n")
    
    return "".join(optimized_profile_md)

def generate_cover_letter(job_data, template_path):
    job_title = job_data.get('projectTitle', 'die ausgeschriebene Position')
    company_name = job_data.get('from', 'dem Unternehmen')
    contact_person = job_data.get('contactPerson', 'Sehr geehrte Damen und Herren')
    
    # Read RTF template - this will be read as plain text, RTF formatting will be lost
    # A proper RTF parsing library would be needed for full fidelity
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        return "Cover letter template not found."
    
    # Replace placeholders
    cover_letter_content = template_content.replace("[Datum]", datetime.now().strftime("%d.%m.%Y"))
    cover_letter_content = cover_letter_content.replace("[Ansprechpartner]", contact_person)
    cover_letter_content = cover_letter_content.replace("[Firmenname]", company_name)
    cover_letter_content = cover_letter_content.replace("[Position]", job_title)
    cover_letter_content = cover_letter_content.replace("[Ihr Name]", MY_NAME)
    cover_letter_content = cover_letter_content.replace("[Ihre Mobilnummer]", MY_MOBILE)
    cover_letter_content = cover_letter_content.replace("[Ihre E-Mail]", MY_EMAIL)

    # Remove any remaining RTF control words for a cleaner plain text output
    cover_letter_content = re.sub(r'\{\\.*?\}|\\[a-zA-Z]+\d*|[\{\}]', '', cover_letter_content)
    cover_letter_content = re.sub(r'\s+', ' ', cover_letter_content).strip() # Normalize whitespace

    return cover_letter_content

def main_process_application():
    # Load all matching jobs from the saved JSON file
    try:
        with open('matching_jobs_list.json', 'r', encoding='utf-8') as f:
            all_matching_jobs = json.load(f)
    except FileNotFoundError:
        print("Error: 'matching_jobs_list.json' not found. Please run process_jobs.py first.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode 'matching_jobs_list.json'. File might be corrupted.")
        return

    # User selected jobs 3 and 8 (indices 2 and 7)
    selected_job_indices = [2, 7] # Hardcoded for now based on user's previous input "3, 8"
    
    jobs_to_process = []
    for idx in selected_job_indices:
        if 0 <= idx < len(all_matching_jobs):
            jobs_to_process.append(all_matching_jobs[idx])
        else:
            print(f"Warning: Selected index {idx + 1} is out of bounds. Skipping.")

    if not jobs_to_process:
        print("No valid jobs selected for processing.")
        return

    # Read base profile content once
    try:
        with open(BASE_PROFILE_MD_PATH, 'r', encoding='utf-8') as f:
            base_profile_content = f.read()
    except FileNotFoundError:
        print(f"Error: Base profile Markdown not found at {BASE_PROFILE_MD_PATH}")
        return

    for job_data in jobs_to_process:
        job_title = job_data.get('projectTitle', 'Unknown Job')
        print(f"\n--- Processing application for: {job_title} ---")

        project_dir = create_project_directory(job_title)
        
        # Initialize log file for this job
        log_file_path = os.path.join(project_dir, 'log.md')
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Log for Job Offer: {job_title}\n\n")
            f.write(f"## Date: {datetime.now().strftime('%d/%m/%Y, %I:%M:%S %p (Europe/Berlin, UTC+2:00)')}\n\n")
            f.write("## Activities:\n")
            f.write(f"- Created project directory: {project_dir}\n")

        # Copy base profile
        shutil.copy(BASE_PROFILE_MD_PATH, os.path.join(project_dir, 'profil.md'))
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"- Copied base profile to {os.path.join(project_dir, 'profil.md')}\n")

        # Save job description (HTML and MD)
        job_description_text = save_job_description_files(project_dir, job_data)
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"- Saved job description as HTML and Markdown in {project_dir}\n")

        # Optimize profile
        optimized_profile_md_content = optimize_profile(job_data, base_profile_content, job_description_text)
        optimized_profile_md_path = os.path.join(project_dir, 'optimized_profile.md')
        with open(optimized_profile_md_path, 'w', encoding='utf-8') as f:
            f.write(optimized_profile_md_content)
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"- Created optimized profile (Markdown) at {optimized_profile_md_path}\n")

        # Convert optimized profile to DOCX
        optimized_profile_docx_path = os.path.join(project_dir, 'profile-mengershausen.docx')
        # Use the imported convert_md_to_docx function
        if convert_md_to_docx(optimized_profile_md_path, optimized_profile_docx_path, BASE_PROFILE_DOCX_PATH):
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"- Converted optimized profile to DOCX at {optimized_profile_docx_path}\n")
        else:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"- Failed to convert optimized profile to DOCX. Check Pandoc installation and logs.\n")

        # Generate cover letter
        cover_letter_content = generate_cover_letter(job_data, COVER_LETTER_TEMPLATE_PATH)
        cover_letter_path = os.path.join(project_dir, 'Anschreiben.txt')
        with open(cover_letter_path, 'w', encoding='utf-8') as f:
            f.write(cover_letter_content)
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"- Generated cover letter at {cover_letter_path}\n")

        print(f"--- Finished processing for: {job_title} ---\n")

if __name__ == "__main__":
    main_process_application()
