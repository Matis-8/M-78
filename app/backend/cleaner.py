import re
import language_tool_python

# Initialize the language tool
# Note: LanguageTool might start a local Java server on the first call
try:
    tool = language_tool_python.LanguageTool('en-US')
except Exception as e:
    print(f"Warning: Could not initialize LanguageTool: {e}")
    tool = None

FILLER_WORDS = [
    r'\bum\b', r'\buh\b', r'\buuuh\b', r'\buh-huh\b',
    r'\blike\b', r'\byou know\b', r'\bactually\b',
    r'\bbasically\b', r'\b-um\b', r'\b-uh\b'
]

def remove_fillers(text):
    for filler in FILLER_WORDS:
        text = re.sub(filler, '', text, flags=re.IGNORECASE)
    return text

def fix_spacing(text):
    # Remove double spaces
    text = re.sub(r'\s+', ' ', text)
    # Fix spacing before punctuation
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    return text.strip()

def clean_text(raw_text: str):
    if not raw_text:
        return ""

    # 1. Basic Cleaning (Regex)
    text = remove_fillers(raw_text)
    text = fix_spacing(text)
    
    if not text:
        return ""

    # 2. Grammar and Capitalization via LanguageTool
    if tool:
        try:
            matches = tool.check(text)
            text = language_tool_python.utils.correct(text, matches)
        except Exception as e:
            print(f"LanguageTool error during check: {e}")
            # Fallback to simple capitalization
            text = text[0].upper() + text[1:] if text else text
    else:
        # Fallback if tool didn't initialize
        text = text[0].upper() + text[1:] if text else text

    return text
