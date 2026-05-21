def extract_message_text(message):
    if not isinstance(message, dict):
        return str(message) if message else ""

    content = message.get("content")
    
    if isinstance(content, list):
        texts = []

        for item in content:
            try:
                value = item.get("text", {}).get("value")
                if value:
                    texts.append(value)
            except Exception:
                continue

        return " ".join(texts)

    return ""

#traer las faqs de la base de datos
def extract_faq_text(faq):
    question = faq.get("question", "")
    return question.strip()