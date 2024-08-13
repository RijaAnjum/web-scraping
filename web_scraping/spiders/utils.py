import json
import re

def sanitize_json(data):
    if data:
        return re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', data)
    return ''

def safe_load_json(data):
    try:
        return json.loads(sanitize_json(data))
    except json.JSONDecodeError as e:
        return []
    
def clean_text(text):
    if isinstance(text, list):
        text = ' '.join(text)
    text = text.replace('&nbsp;"', '')
    text = text.replace('\\"', '')
    text = text.strip('/"').strip()
    # Remove HTML entities and escape sequences
    text = re.sub(r'&[a-z]+;', '', text)  # e.g., &nbsp;, &amp;
    text = re.sub(r'\\[rntv]', '', text)  # e.g., \r, \n, \t, \v
    text = re.sub(r'\\"', '"', text)      # escaped double quotes
    text = re.sub(r"\\'", "'", text)      # escaped single quotes
    text = re.sub(r'\\', '', text)        # any remaining backslashes  
    # Remove patterns like \$2017
    text = re.sub(r'\\\$', '', text)      # matches and removes \$ sequences
    # Remove non-ASCII characters and control characters
    text = re.sub(r'[^\x20-\x7E]+', '', text)
    # Remove specific unwanted characters
    text = re.sub(r'[^A-Za-z0-9\s.,;:!?\'\"()-]', '', text)
    # Replace any multiple spaces, newlines, or tabs with a single space
    text = re.sub(r'\s+', ' ', text)   
    return text

def barcode_type(string):
    length= len(string)
    if length == 13 or length == 8:
        return "EAN"
    elif  length == 12 or length == 11:
        return "UPC"
    elif length == 14:
        return "GTIN"
