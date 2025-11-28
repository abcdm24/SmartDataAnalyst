import json
import re

async def repair_json(text:str):
    """
    Attempts to repair a malformed JSON returned by LLMs.
    Returns (data, fixed_json_string).
    Raises ValueError is not repairable.
    """
    print(f"Attempting to repair JSON from text:\n{text}")

    # 1. Extract the first json object from the text
    # json_match = re.search(r'({.*}|\[.*\])', text, re.DOTALL)
    json_str, explanation = extract_json_block(text)

    if json_str is None:
        raise ValueError("No JSON object found in the text.")
    
    
    print(f"Extracted raw JSON:\n{json_str}")
    print(f"Explanation text:\n{explanation}")
    
    # Try direct parsing
    try:
        return json.loads(json_str), text
    except Exception as e:
        print(f"Direct parsing failed, attempting to repair JSON. Error: {e}")
        pass

    raw = json_str
    # 2. Remove trailing commas
    fixed = re.sub(r',(\s*[}\]])', r'\1', raw)

    # 3. Quote unquoted keys (simple heuristic)
    fixed = re.sub(r'(\{|,)\s*([A-Za-z0-9_]+)\s*:', r'\1 "\2":', fixed)

    # 4. Replace single quotes with double quotes
    fixed = fixed.replace("'",'"')

    # print(f"Repaired JSON string:\n{fixed}")

    # 5. Try parsing again
    try:
        return json.loads(fixed), fixed
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON repair failed: {e}\nOriginal: {text}")
    

def extract_json_block(text:str):
    """
    Extract the first ful JSON object (supports multiline and nested braces).
    Returns (json_str, rest_text)
    """

    start = text.find('{')
    if start == -1:
        return None, text
    
    brace_count = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        char = text[i]

        # Handle escaped quotes \" inside strings
        if char == "\\" and not escaped:
            escaped = True
            continue

        # Toggle in-string state
        if char == '"' and not escaped:
            in_string = not in_string

        # Count braces only when NOT inside a string
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            
            # Closing brace for whole object found
            if brace_count == 0:
                json_str = text[start:i+1]
                rest = text[i+1:].strip()
                return json_str, rest
        
        escaped = False  # Reset escaped state after processing a character

    return None, text  