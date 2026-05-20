import re
import logging
import emoji
from app.core.config import settings

logger = logging.getLogger(__name__)



NOISE_WORDS = {
    "hola", "holi", "hey", "buenas", "buenas tardes", "buenos dias",
    "buenos días", "buenas noches", "gracias", "muchas gracias",
    "mil gracias", "porfa", "xfa", "pls", "plis", "ok", "okey",
    "listo", "bueno", "holaaa", "mmm", "eh", "este", "pues",
    "osea", "o sea", "chao", "bye", "adios", "hasta luego",
    "nos vemos", "noches", "tardes", "dias", "días"
}

KEY_WORDS = {
    "ayuda", "soporte", "problema", "error", "falla",
    "costo", "valor", "precio", "tarifa",
    "pagar", "pago", "reembolso", "devolucion", "devolución",
    "factura", "cobro", "transferencia", "tarjeta",
    "registro", "usuario", "contraseña", "acceso",
    "bloqueo", "activar", "desactivar",
    "cita", "reserva", "turno", "agenda",
    "clase", "curso", "matricula", "inscripcion", "inscripción",
    "correo", "email", "mensaje", "whatsapp", "telefono", "teléfono",
    "direccion", "dirección", "ubicacion", "ubicación", "sede", "lugar",
    "horario", "hora", "tiempo", "abren", "cierran",
    "cancelar", "cambio", "modificar", "actualizar",
    "solicitar", "reportar", "consultar", "querer",
}

SHORT_KEYWORDS = {"no", "si", "sí", "ya", "ir", "da", "va", "am", "pm"}

ABBREVIATIONS = {
    "x q":   "porque",
    "x fa":  "por favor",
    "xq":    "porque",
    "xfa":   "por favor",
    "ntp":   "no te preocupes",
    "pls":   "por favor",
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
}

SENSITIVE_DATA = {
    "url":         (re.compile(r'https?://\S+|www\.\S+'),         "[URL]"),
    "email":       (re.compile(r'\b\S+@\S+\.\S+\b'),             "[EMAIL]"),
    "credit_card": (re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),   "[CARD]"),
    "phone":       (re.compile(r'(?<!\d)\d{7,10}(?!\d)'),        "[PHONE]"),
}


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


def tokenize(text):
    text = re.sub(
        r'[^a-záéíóúüñ0-9\s]',
        ' ',
        text
    )
    words = text.split()
    return words


def filter_tokens(words):
    result = []
    for word in words:
        if word in NOISE_WORDS:
            continue
        if word in KEY_WORDS:
            result.append(word)
            continue
        if word in SHORT_KEYWORDS:
            result.append(word)
            continue
        if len(word) >= settings.min_text_length:
            result.append(word)
    return result


def find_keywords(text):
    words = tokenize(text.lower())
    found = []
    for word in words:
        if word in KEY_WORDS:
            found.append(word)
    return found


def clean_text(text):
    if not text:
        return ""
    normalized = normalize(text)
    tokens = tokenize(normalized)
    filtered = filter_tokens(tokens)
    return " ".join(filtered)
    