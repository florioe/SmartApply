import argparse
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

# Import shared functions from job_offer_analyzer.py
# Assuming job_offer_analyzer.py is in the same directory or accessible via PYTHONPATH
from job_offer_analyzer import log_message, extract_job_offer_details

def parse_markdown_profile(md_content):
    """
    Parses the markdown profile content into a structured dictionary.
    """
    profile_data = {
        'Kurzprofil': '',
        'Verfügbarkeit': '',
        'AI Experience & Ambitionen': '',
        'Leistungen': '',
        'Nehmen Sie Kontakt mit mir auf': '',
        'Projekthistorie (Auswahl)': [],
        'Ausbildung / Skills': {
            'Fort-, Zusatzausbildungen (Auswahl) / Studium': [],
            'Auszeichnungen': [],
            'Veröffentlichungen': [],
            'Sprachen': '',
            'Skill-Profil': ''
        }
    }
    
    lines = md_content.split('\n')
    current_section = None
    current_subsection = None
    project_entry = None

    section_keys = list(profile_data.keys())
    subsection_keys = list(profile_data['Ausbildung / Skills'].keys())

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line in section_keys:
            current_section = line
            current_subsection = None
            if current_section == 'Projekthistorie (Auswahl)' and project_entry:
                profile_data['Projekthistorie (Auswahl)'].append(project_entry)
                project_entry = None
            continue
        
        if current_section == 'Ausbildung / Skills' and line in subsection_keys:
            current_subsection = line
            continue

        if current_section == 'Projekthistorie (Auswahl)':
            if re.match(r'^\d{2}/\d{4}', line):
                if project_entry:
                    profile_data['Projekthistorie (Auswahl)'].append(project_entry)
                project_entry = {'title': line, 'role': '', 'description': [], 'technologies': []}
            elif project_entry:
                if line.startswith('Rolle:'):
                    project_entry['role'] = line.replace('Rolle:', '').strip()
                elif line.startswith('Technologien/Werkzeuge:'):
                    project_entry['technologies'] = [t.strip() for t in line.replace('Technologien/Werkzeuge:', '').split(',')]
                else:
                    project_entry['description'].append(line)
        elif current_section == 'Ausbildung / Skills':
            if current_subsection:
                if isinstance(profile_data['Ausbildung / Skills'][current_subsection], list):
                    profile_data['Ausbildung / Skills'][current_subsection].append(line)
                elif isinstance(profile_data['Ausbildung / Skills'][current_subsection], str):
                    profile_data['Ausbildung / Skills'][current_subsection] += line + '\n'
        elif current_section:
            if isinstance(profile_data.get(current_section), str):
                profile_data[current_section] += line + '\n'

    if project_entry:
        profile_data['Projekthistorie (Auswahl)'].append(project_entry)

    # Clean up multiline strings
    for key in profile_data:
        if isinstance(profile_data.get(key), str):
            profile_data[key] = profile_data[key].strip()
    
    for key in profile_data['Ausbildung / Skills']:
        if isinstance(profile_data['Ausbildung / Skills'].get(key), str):
            profile_data['Ausbildung / Skills'][key] = profile_data['Ausbildung / Skills'][key].strip()

    return profile_data

def match_keywords_to_text(keywords, text):
    """
    Finds and scores keyword matches in a given text.
    Returns a dictionary of matched keywords with their scores.
    """
    matched_keywords = {}
    text_lower = text.lower()
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in text_lower:
            matched_keywords[keyword] = 100 # Direct match
        else:
            # Fuzzy matching for partial matches
            for word in text_lower.split():
                similarity = fuzz.ratio(keyword_lower, word)
                if similarity >= 75: # Threshold for fuzzy match
                    matched_keywords[keyword] = max(matched_keywords.get(keyword, 0), similarity)
    return matched_keywords

def filter_and_sort_projects(job_offer_keywords, all_projects):
    """
    Scores and sorts projects based on relevance to job offer keywords.
    Returns a list of relevant projects and other projects.
    """
    scored_projects = []
    for project in all_projects:
        project_text = project['title'] + " " + project['role'] + " " + " ".join(project['description']) + " " + " ".join(project['technologies'])
        project_text = project_text.lower()
        
        score = 0
        for keyword in job_offer_keywords:
            if keyword.lower() in project_text:
                score += 1
        
        project['relevance_score'] = score
        scored_projects.append(project)

    # Sort projects by relevance score (descending)
    scored_projects.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Separate into relevant and other projects
    relevant_projects = scored_projects[:5] # Take the top 5
    other_projects = scored_projects[5:]

    return relevant_projects, other_projects

def generate_optimized_profile_markdown(base_profile_data, job_details, relevant_projects, other_projects, missing_keywords_log):
    """
    Generates the optimized profile in markdown format.
    """
    optimized_profile_content = []

    # Title and Contact Info
    optimized_profile_content.append("# Florian von Mengershausen - {}".format(job_details['title']))
    optimized_profile_content.append("")
    optimized_profile_content.append("---")
    optimized_profile_content.append("")
    
    # Contact Data
    contact_info = base_profile_data['Nehmen Sie Kontakt mit mir auf']
    phone_match = re.search(r'\+?\d[\d\s]+', contact_info)
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', contact_info)
    
    phone = phone_match.group(0).strip() if phone_match else 'N/A'
    email = email_match.group(0).strip() if email_match else 'N/A'

    optimized_profile_content.append("**Mobile:** {}".format(phone))
    optimized_profile_content.append("**Email:** {}".format(email))
    optimized_profile_content.append("")

    # Kurzprofil - ADAPT THIS SECTION
    optimized_profile_content.append("## Kurzprofil")
    optimized_profile_content.append("")
    
    original_kurzprofil = base_profile_data['Kurzprofil']
    job_keywords_lower = [kw.lower() for kw in job_details['keywords']]
    
    # Reorder sentences to prioritize those with keywords
    sentences = re.split(r'(?<=[.!?])\s+', original_kurzprofil)
    scored_sentences = []
    for sentence in sentences:
        score = 0
        for keyword in job_keywords_lower:
            if keyword in sentence.lower():
                score += 1
        scored_sentences.append((score, sentence))
    
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    
    # Reconstruct the summary with prioritized sentences first
    optimized_kurzprofil = " ".join([s[1] for s in scored_sentences])
    optimized_profile_content.append(optimized_kurzprofil)
    optimized_profile_content.append("")

    # Verfügbarkeit (keep as is)
    optimized_profile_content.append("## Verfügbarkeit")
    optimized_profile_content.append("")
    optimized_profile_content.append(base_profile_data['Verfügbarkeit'])
    optimized_profile_content.append("")

    # Projekthistorie (Auswahl) (keep as is)
    optimized_profile_content.append("## Projekthistorie (Auswahl)")
    optimized_profile_content.append("")
    
    relevant_projects.sort(key=lambda x: get_project_start_date(x['title']), reverse=True)

    for project in relevant_projects:
        optimized_profile_content.append("### {}".format(project['title']))
        
        role = project['role']
        if "projektleiter" in job_details['description'].lower() or "projektmanager" in job_details['description'].lower():
            if "scrum-master" in role.lower():
                role = role.replace("Scrum-Master", "???Projektleiter / Scrum Master???")
            if "scrum master" in role.lower():
                role = role.replace("Scrum Master", "???Projektleiter / Scrum Master???")
            if "rte" in role.lower():
                role = role.replace("RTE", "???Projektleiter / RTE???")

        optimized_profile_content.append("**Rolle:** {}".format(role))
        
        description_lines = []
        for desc_line in project['description']:
            if desc_line.strip() and not desc_line.strip().startswith('Technologien/Werkzeuge:'):
                description_lines.append(desc_line.strip())
        
        if len(description_lines) > 4:
            optimized_profile_content.append("- " + "\n- ".join(description_lines[:4]))
        else:
            optimized_profile_content.append("- " + "\n- ".join(description_lines))
        
        if project['technologies']:
            optimized_profile_content.append("**Technologien/Werkzeuge:** {}".format(', '.join(project['technologies'])))
        optimized_profile_content.append("")

    # Skills - FILTERED AND SORTED
    optimized_profile_content.append("## Skills")
    optimized_profile_content.append("")
    
    skill_profile = base_profile_data['Ausbildung / Skills']['Skill-Profil']
    
    if skill_profile:
        optimized_profile_content.append("| Skill | Junior | Senior | Expert |")
        optimized_profile_content.append("|---|---|---|---|")
        
        relevant_skills = []
        for skill, levels in skill_profile.items():
            for keyword in job_keywords_lower:
                if fuzz.partial_ratio(skill.lower(), keyword) > 80:
                    relevant_skills.append((skill, levels))
                    break
        
        for skill, levels in relevant_skills:
            junior = levels.get('Junior', '')
            senior = levels.get('Senior', '')
            expert = levels.get('Expert', '')
            optimized_profile_content.append("| {} | {} | {} | {} |".format(skill, junior, senior, expert))
        optimized_profile_content.append("")

    # Zertifizierungen - FILTERED AND SORTED
    optimized_profile_content.append("## Zertifizierungen")
    optimized_profile_content.append("")
    
    certifications = base_profile_data['Ausbildung / Skills']['Fort-, Zusatzausbildungen (Auswahl) / Studium']
    
    relevant_certifications = []
    for cert in certifications:
        for keyword in job_keywords_lower:
            if keyword in cert.lower():
                relevant_certifications.append(cert)
                break
    
    for cert in relevant_certifications:
        optimized_profile_content.append("- {}".format(cert))
    optimized_profile_content.append("")
    optimized_profile_content.append("")

    # Appendix for extended history (keep as is)
    optimized_profile_content.append("\n\n---\n\n") # Page break
    optimized_profile_content.append("# Anhang: Erweiterte Projekthistorie")
    optimized_profile_content.append("")

    other_projects.sort(key=lambda x: get_project_start_date(x['title']), reverse=True)

    for project in other_projects:
        optimized_profile_content.append("## {}".format(project['title']))
        optimized_profile_content.append("**Rolle:** {}".format(project['role']))
        
        description_lines = []
        for desc_line in project['description']:
            if desc_line.strip() and not desc_line.strip().startswith('Technologien/Werkzeuge:'):
                description_lines.append(desc_line.strip())
        
        if len(description_lines) > 4:
            optimized_profile_content.append("- " + "\n- ".join(description_lines[:4]))
        else:
            optimized_profile_content.append("- " + "\n- ".join(description_lines))
        
        optimized_profile_content.append("")

    return "\n".join(optimized_profile_content)

def log_missing_keywords(job_offer_keywords, optimized_profile_content, log_file_path):
    """
    Logs which keywords from the job offer are not contained in the optimized profile.
    """
    missing_kws = []
    optimized_profile_lower = optimized_profile_content.lower()
    for keyword in job_offer_keywords:
        if keyword.lower() not in optimized_profile_lower:
            missing_kws.append(keyword)
    
    if missing_kws:
        log_message(log_file_path, "Missing keywords in optimized profile: {}".format(', '.join(missing_kws)))
    else:
        log_message(log_file_path, "All job offer keywords found in optimized profile.")

def get_project_start_date(project_title):
    # Helper function for sorting projects
    match = re.match(r'(\d{2}/\d{4})', project_title)
    if match:
        return datetime.strptime(match.group(1), '%m/%Y')
    return datetime.min # Return a very old date if no date found

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize a base profile for a specific job offer.")
    parser.add_argument('job_offer_html_path', type=str, help='Path to the job offer HTML file.')
    parser.add_argument('base_profile_md_path', type=str, help='Path to the base profile markdown file.')
    parser.add_argument('optimized_profile_md_output_path', type=str, help='Path to save the optimized profile markdown file.')
    parser.add_argument('log_file_path', type=str, help='Path to the log file.')
    
    args = parser.parse_args()

    log_message(args.log_file_path, "Starting profile optimization process.")

    try:
        # 1. Extract Job Offer Details
        with open(args.job_offer_html_path, 'r', encoding='utf-8') as f:
            job_html_content = f.read()
        job_details = extract_job_offer_details(job_html_content)
        log_message(args.log_file_path, "Job Offer Details Extracted: {}".format(job_details['title']))

        # 2. Parse Base Profile
        with open(args.base_profile_md_path, 'r', encoding='utf-8') as f:
            base_md_content = f.read()
        base_profile_data = parse_markdown_profile(base_md_content)
        log_message(args.log_file_path, "Base Profile Markdown Parsed.")

        # Handle Product Owner specific profile
        if 'product owner' in job_details['title'].lower():
            log_message(args.log_file_path, "Product Owner role detected. Using Product Owner profile as base.")
            with open('product_owner_profile.md', 'r', encoding='utf-8') as f:
                po_md_content = f.read()
            base_profile_data = parse_markdown_profile(po_md_content)
        else:
            log_message(args.log_file_path, "Not a Product Owner role. Using standard profile.")

        # 3. Filter and Sort Projects
        relevant_projects, other_projects = filter_and_sort_projects(
            job_details['keywords'], 
            base_profile_data['Projekthistorie (Auswahl)']
        )
        log_message(args.log_file_path, "Found {} relevant projects and {} other projects.".format(len(relevant_projects), len(other_projects)))

        # 4. Generate Optimized Profile Markdown
        optimized_md_content = generate_optimized_profile_markdown(
            base_profile_data, 
            job_details, 
            relevant_projects, 
            other_projects,
            args.log_file_path # Pass log_file_path for logging missing keywords
        )
        
        # 5. Save Optimized Profile Markdown
        with open(args.optimized_profile_md_output_path, 'w', encoding='utf-8') as f:
            f.write(optimized_md_content)
        log_message(args.log_file_path, "Optimized profile saved to {}".format(args.optimized_profile_md_output_path))

        # 6. Log missing keywords
        log_missing_keywords(job_details['keywords'], optimized_md_content, args.log_file_path)

        print("PROFILE_OPTIMIZED: Optimized profile created successfully.")

    except FileNotFoundError as e:
        log_message(args.log_file_path, "Error: File not found - {}".format(e.filename))
        print("ERROR: File not found - {}".format(e.filename))
    except Exception as e:
        log_message(args.log_file_path, "An unexpected error occurred during profile optimization: {}".format(e))
        print("ERROR: An unexpected error occurred during profile optimization: {}".format(e))
