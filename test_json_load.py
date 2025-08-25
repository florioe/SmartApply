import json

try:
    with open('job_offers_1.json', 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    print("job_offers_1.json loaded successfully.")
except json.JSONDecodeError as e:
    print(f"Error loading job_offers_1.json: {e}")
    with open('job_offers_1.json', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Problematic content around error: {content[max(0, e.pos-50):e.pos+50]}")
except FileNotFoundError:
    print("job_offers_1.json not found.")

try:
    with open('job_offers_2.json', 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    print("job_offers_2.json loaded successfully.")
except json.JSONDecodeError as e:
    print(f"Error loading job_offers_2.json: {e}")
    with open('job_offers_2.json', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Problematic content around error: {content[max(0, e.pos-50):e.pos+50]}")
except FileNotFoundError:
    print("job_offers_2.json not found.")
