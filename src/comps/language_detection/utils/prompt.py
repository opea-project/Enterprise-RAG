# Dictionary mapping language codes to their full language names.
# This dictionary is used with the ftlangdetect package to identify languages based on their ISO 639-1 language codes. 
language_dict = {
    'ar': 'Arabic',
    'cs': 'Czech',
    'da': 'Danish',
    'en': 'English',
    'et': 'Estonian',
    'fi': 'Finnish',
    'fr': 'French',
    'de': 'German',
    'el': 'Greek',
    'he': 'Hebrew',
    'hu': 'Hungarian',
    'it': 'Italian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'no': 'Norwegian',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sk': 'Slovak',
    'es': 'Spanish',
    'sv': 'Swedish',
    'zh': 'Chinese',
}

def set_prompt(query_lang: str, answer_lang: str, answer: str) -> str:
    prompt_template = """
            Translate this from {source_lang} to {target_lang}:
            {source_lang}:
            {answer}

            {target_lang}:            
        """
    return prompt_template.format(source_lang=language_dict[answer_lang], target_lang=language_dict[query_lang], answer=answer)
