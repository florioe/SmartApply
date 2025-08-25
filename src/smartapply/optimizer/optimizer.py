import requests
import os
import re
from job_offer_analyzer import extract_job_offer_details, log_message
from generate_cover_letter import generate_cover_letter
from convert_to_docx import convert_md_to_docx
import markdown
from bs4 import BeautifulSoup
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
import config

os.environ["OPENAI_API_KEY"] = config.model_list[0]["api_key"]

def download_job_html(url, job_folder):
    log_message(log_file_path, f"Downloading HTML from {url} to {job_folder}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html_content = response.text
            log_message(log_file_path, f"Successfully downloaded HTML from {url}")
            with open(os.path.join(job_folder, "job_offer.html"), "w") as f:
                f.write(html_content)
            log_message(log_file_path, f"Saved HTML to {os.path.join(job_folder, 'job_offer.html')}")
            return html_content
        except requests.exceptions.RequestException as e:
            log_message(log_file_path, f"Error downloading HTML: {e}")
            print(f"Error downloading HTML: {e}")
            return None
        except Exception as e:
            log_message(log_file_path, f"Unexpected error: {e}")
            print(f"Unexpected error: {e}")
            return None
        finally:
            log_message(log_file_path, f"Finished downloading HTML from {url}")
    except Exception as e:
        log_message(log_file_path, f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return None


def select_profile(job_title, job_keywords):
    log_message(log_file_path, f"Selecting profile for job title: {job_title} and keywords: {job_keywords}")
    try:
        try:
            if "product owner" in job_title.lower():
                profile_file = config.product_owner_profile_md_file
                log_message(log_file_path, f"Selected product owner profile: {profile_file}")
                return profile_file
            else:
                profile_file = config.default_profile_md_file
                log_message(log_file_path, f"Selected default profile: {profile_file}")
                return profile_file
        except Exception as e:
            log_message(log_file_path, f"Error selecting profile: {e}")
            print(f"Error selecting profile: {e}")
            return None
    except Exception as e:
        log_message(log_file_path, f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return None
    finally:
        log_message(log_file_path, "Finished selecting profile")

def optimize_profile_content(profile_content, job_title, url, summary):
    log_message(log_file_path, "Optimizing profile content")
    try:
        try:
            optimized_profile = f"# Florian v. Mengershausen\n\n## {job_title}\n\nOriginal URL: {url}\n\n{summary}"
            log_message(log_file_path, f"Optimized profile content: {optimized_profile}")
            return optimized_profile
        except Exception as e:
            log_message(log_file_path, f"Error optimizing profile content: {e}")
            print(f"Error optimizing profile content: {e}")
            return None
    except Exception as e:
        log_message(log_file_path, f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return None
    finally:
        log_message(log_file_path, "Finished optimizing profile content")

def optimize_profile(html_content, job_folder, url, log_file_path):
    log_message(log_file_path, f"Optimizing profile for job folder: {job_folder}, URL: {url}")
    try:
        log_message(log_file_path, "Extracting job details")
        job_details = extract_job_offer_details(html_content)
        job_title = job_details.get('title', '')
        log_message(log_file_path, f"Extracted job title: {job_title}")
    except Exception as e:
        log_message(log_file_path, f"Error extracting job details: {e}")
        print(f"Error extracting job details: {e}")
        return

    from keyword_extractor.keyword_extractor import extract_keywords_from_html
    job_keywords = extract_keywords_from_html(html_content)

    profile_md_file = select_profile(job_title, job_keywords)

    try:
        log_message(log_file_path, f"Reading profile file: {profile_md_file}")
        with open(profile_md_file, 'r') as f:
            profile_content = f.read()
        log_message(log_file_path, f"Successfully read profile file: {profile_md_file}")
    except FileNotFoundError:
        log_message(log_file_path, f"Profile file not found: {profile_md_file}")
        print(f"Profile file not found: {profile_md_file}")
        return
    except Exception as e:
        log_message(log_file_path, f"Error reading profile file: {e}")
        print(f"Error reading profile file: {e}")
        return

    try:
        log_message(log_file_path, f"Writing job keywords to file: {os.path.join(job_folder, 'job_keywords.txt')}")
        with open(os.path.join(job_folder, "job_keywords.txt"), "w") as f:
            f.write("\n".join(job_keywords))
        log_message(log_file_path, f"Successfully wrote job keywords to file: {os.path.join(job_folder, 'job_keywords.txt')}")
    except Exception as e:
        log_message(log_file_path, f"Error writing job keywords to file: {e}")
        print(f"Error writing job keywords to file: {e}")
        return

    try:
        log_message(log_file_path, f"Writing profile keywords to file: {os.path.join(job_folder, 'profile_keywords.txt')}")
        with open(os.path.join(job_folder, "profile_keywords.txt"), "w") as f:
            f.write(profile_content)
        log_message(log_file_path, f"Successfully wrote profile keywords to file: {os.path.join(job_folder, 'profile_keywords.txt')}")
    except Exception as e:
        log_message(log_file_path, f"Error writing profile keywords to file: {e}")
        print(f"Error writing profile keywords to file: {e}")
        return

    # Load the text document
    loader = TextLoader(profile_md_file)
    try:
        log_message(log_file_path, f"Loading profile document: {profile_md_file}")
        documents = loader.load()
        log_message(log_file_path, f"Successfully loaded profile document: {profile_md_file}")
    except Exception as e:
        log_message(log_file_path, f"Error loading profile document: {e}")
        print(f"Error loading profile document: {e}")
        return

    summary = ""
    for model_index in range(len(config.model_list)):
        try:
            log_message(log_file_path, f"Summarizing with model: {config.model_list[model_index]['name']}")
            llm = ChatOpenAI(model=config.model_list[model_index]["name"])
            os.environ["OPENAI_API_KEY"] = config.model_list[model_index]["api_key"]

            # Load the summarization chain (map_reduce is a common strategy)
            # Other strategies include 'stuff', 'refine', 'map_rerank'
            chain = load_summarize_chain(llm, chain_type="stuff")

            # Run the summarization chain
            summary = chain.run(documents)
            log_message(log_file_path, f"Successfully summarized with model: {config.model_list[model_index]['name']}")
            break  # If successful, break out of the loop
        except Exception as e:
            log_message(log_file_path, f"Error during summarization with model {config.model_list[model_index]['name']}: {e}")
            print(f"Error during summarization with model {config.model_list[model_index]['name']}: {e}")
            summary = f"Error: Could not summarize profile with model {config.model_list[model_index]['name']}."
            continue
    if summary == "":
        summary = "Error: Could not summarize profile with any available model."

    try:
        log_message(log_file_path, "Formatting optimized profile")
        optimized_profile = optimize_profile_content(profile_content, job_title, url, summary)
        log_message(log_file_path, "Successfully formatted optimized profile")
    except Exception as e:
        log_message(log_file_path, f"Error formatting optimized profile: {e}")
        print(f"Error formatting optimized profile: {e}")
        return

    md_filepath = os.path.join(job_folder, "optimized_profile.md")
    docx_filepath = os.path.join(job_folder, "optimized_profile.docx")

    try:
        log_message(log_file_path, f"Writing optimized profile to file: {md_filepath}")
        with open(md_filepath, "w") as f:
            f.write(optimized_profile)
        log_message(log_file_path, f"Successfully wrote optimized profile to file: {md_filepath}")
    except Exception as e:
        log_message(log_file_path, f"Error writing optimized profile to file: {e}")
        print(f"Error writing optimized profile to file: {e}")
        return

    convert_md_to_docx(md_filepath, docx_filepath)
    log_message(log_file_path, f"Converted markdown to docx: {docx_filepath}")
    finally:
        log_message(log_file_path, f"Finished optimizing profile for job folder: {job_folder}, URL: {url}")
