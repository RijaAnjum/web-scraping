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
    
def clean_text(self, text):
        if isinstance(text, list):
            text = ' '.join(text)
        text = text.replace('&nbsp;"', '')
        text = text.strip('/"').strip()
        text = text.replace('\\"', '')
        return text