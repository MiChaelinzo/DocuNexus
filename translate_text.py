import translate

def translate_text(text, target_language):
    translator = translate.Translator(to_lang=target_language)
    translation = translator.translate(text)
    return translation
