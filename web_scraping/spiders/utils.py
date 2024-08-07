import json
import re
import pdb
def sanitize_json(data):
    if data:
        return re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', data)
    return ''

def safe_load_json(data):
    try:
        return json.loads(sanitize_json(data))
    except json.JSONDecodeError as e:
        pdb.set_trace()
        return []
    
def clean_text(text):
    if isinstance(text, list):
        text = ' '.join(text)
    text = text.replace('&nbsp;"', '')
    text = text.strip('/"').strip()
    text = text.replace('\\"', '')
    return text

def barcode_type(string):
    length= len(string)
    if length == 13 or length == 8:
        return "EAN"
    elif  length == 12 or length == 11:
        return "UPC"
    elif length == 14:
        return "gtin"
