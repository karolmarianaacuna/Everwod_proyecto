import re
import logging
import emoji
from app.core.config import settings

logger = logging.getLogger(__name__)

USELESS_MESSAGES = {
    "hola", "holi", "buenas", "buen día", "buen dia",
    "buenas tardes", "buenas noches",
    "gracias", "muchas gracias", "mil gracias",
    "ok", "okay", "listo", "perfecto",
    "si", "sí", "claro", "vale"
}

def is_useless_message(text: str) -> bool:
    if not text:
        return True

    text = text.lower().strip()

    if text in USELESS_MESSAGES:
        return True

    if len(text.split()) < settings.min_text_length:
        return True

    if re.match(r"^\d{1,2}(:\d{2})?\s?(am|pm)?$", text):
        return True

    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        return True

    return False

# Abreviaciones comunes
ABBREVIATIONS = {

    #español
    "x q":   "porque",
    "x fa":  "por favor",
    "xq":    "porque",
    "xfa":   "por favor",
    "ntp":   "no te preocupes",
    "pf":    "por favor",
    "tmb":   "tambien",
    "msj":   "mensaje",
    "wsp":   "whatsapp",
    "cel":   "celular",
    "kiero": "quiero",
    "kien":  "quien",
    "tb":    "tambien",
    "bn":    "bien",
    "ht":    "hasta",
    "ok":    "bien",
    "xo":    "pero",
    "pa":    "para",
    "xa":    "para",
    "ke":    "que",
    "q":     "que",
    "k":     "que",
    "d":     "de",

    # Inglés
    "pls": "please",
    "plz": "please",
    "u": "you",
    "ur": "your",
    "msg": "message"
}


# Se reemplazan para no guardar info privada y se incluye lo de nombres para evitar que se guarde info personal
SENSITIVE_DATA = {
    "url":         (re.compile(r'https?://\S+|www\.\S+'),         "[URL]"),
    "email":       (re.compile(r'\b\S+@\S+\.\S+\b'),             "[EMAIL]"),
    "credit_card": (re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),   "[CARD]"),
    "phone":       (re.compile(r'(?<!\d)\d{7,10}(?!\d)'),        "[PHONE]"),
    "spanish_name": (re.compile( r"\b(me llamo|mi nombre es|soy|habla con|contactar a|pregunta por | hablas con )\s+[a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+){0,3}", re.IGNORECASE), "[NAME]"),
    "english_name": (re.compile(r"\b(my name is|i am|i'm|contact|ask for)\s+[a-z]+(?:\s+[a-z]+){0,3}",re.IGNORECASE), "[NAME]")
}



# Palabras de ruido comunes
def normalize(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = emoji.replace_emoji(text, replace="")
    for data_type, (regex, placeholder) in SENSITIVE_DATA.items():
        text = regex.sub(placeholder, text)
    for short, full in ABBREVIATIONS.items():
        text = re.sub(rf'\b{re.escape(short)}\b', full, text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


#saca de una cadena de texto emojis, urls, emails, numeros de telefono, tarjetas de credito y nombres propios para evitar guardar info personal y mejorar la calidad del texto para el modelo
def clean_text(text):
    if not text:
        return ""

    normalized = normalize(text)

    if is_useless_message(normalized):
        return ""

    return normalized