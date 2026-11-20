"""Idiomas disponíveis na conversa e na síntese de voz."""
import re
from typing import Literal

IDIOMAS = {
    "pt-BR": ("português brasileiro", "Francisca", "Antonio"),
    "en-US": ("inglês americano", "Jenny", "Guy"),
    "es-ES": ("espanhol", "Elvira", "Alvaro"),
    "zh-CN": ("chinês mandarim em caracteres simplificados", "Xiaoxiao", "Yunxi"),
    "ar-SA": ("árabe", "Zariyah", "Hamed"),
    "de-DE": ('alemão', 'Katja', 'Conrad'),
    "fr-FR": ('francês', 'Denise', 'Henri'),
    "ja-JP": ('japonês', 'Nanami', 'Keita'),
    "ru-RU": ('russo', 'Svetlana', 'Dmitry'),
    "pl-PL": ('polonês', 'Zofia', 'Marek'),
    "fa-IR": ('persa', 'Dilara', 'Farid'),
    "hi-IN": ('hindi', 'Swara', 'Madhur'),
    "bn-IN": ('bengali', 'Tanishaa', 'Bashkar'),
    "id-ID": ('indonésio', 'Gadis', 'Ardi'),
    "ko-KR": ('coreano', 'SunHi', 'InJoon'),
    "tr-TR": ('turco', 'Emel', 'Ahmet'),
    "it-IT": ('italiano', 'Elsa', 'Diego'),
    "nl-NL": ('Nederlands (Nederland)', 'Colette', 'Maarten'),
    "sv-SE": ('sueco (Suécia)', 'Sofie', 'Mattias'),
    "sw-KE": ('suaíli (Quênia)', 'Zuri', 'Rafiki'),
    "nb-NO": ("norueguês bokmål", "Pernille", "Finn"),
    "da-DK": ("dinamarquês", "Christel", "Jeppe"),
    "he-IL": ("hebraico moderno de Israel", "Hila", "Avri"),
    "ro-RO": ("romeno", "Alina", "Emil"),
    "uk-UA": ("ucraniano", "Polina", "Ostap"),
    "fil-PH": ("filipino das Filipinas", "Blessica", "Angelo"),
    "vi-VN": ("vietnamita", "HoaiMy", "NamMinh"),
    "ur-PK": ("urdu do Paquistão", "Uzma", "Asad"),
    "am-ET": ("amárico da Etiópia", "Mekdes", "Ameha"),
    "th-TH": ("tailandês", "Premwadee", "Niwat"),
    "zh-HK": ("cantonês de Hong Kong, escrito em chinês tradicional com vocabulário cantonês", "HiuMaan", "WanLung"),
    "ta-IN": ("tâmil da Índia", "Pallavi", "Valluvar"),
    "te-IN": ("telugo", "Shruti", "Mohan"),
    "mr-IN": ("marata", "Aarohi", "Manohar"),
    "gu-IN": ("guzerate", "Dhwani", "Niranjan"),
}

Idioma = Literal[
    "auto", "pt-BR", "en-US", "es-ES", "zh-CN", "ar-SA", "de-DE", "fr-FR", "ja-JP",
    "ru-RU", "pl-PL", "fa-IR", "hi-IN", "bn-IN", "id-ID", "ko-KR", "tr-TR", "it-IT",
    "nl-NL", "sv-SE", "sw-KE",
    "nb-NO", "da-DK", "he-IL", "ro-RO", "uk-UA", "fil-PH", "vi-VN",
    "ur-PK", "am-ET", "th-TH", "zh-HK", "ta-IN", "te-IN", "mr-IN",
    "gu-IN",
]

ALIASES = {
    "mandarim": "zh-CN", "mandarin": "zh-CN", "chinês": "zh-CN", "chinese": "zh-CN",
    "árabe": "ar-SA", "arabic": "ar-SA", "inglês": "en-US", "english": "en-US",
    "espanhol": "es-ES", "spanish": "es-ES", "português": "pt-BR", "portuguese": "pt-BR",
    "neerlandês": "nl-NL", "holandês": "nl-NL", "dutch": "nl-NL",
    "sueco": "sv-SE", "swedish": "sv-SE",
    "suaíli": "sw-KE", "kiswahili": "sw-KE", "swahili": "sw-KE",
    "norueguês": "nb-NO", "norwegian": "nb-NO", "bokmål": "nb-NO",
    "dinamarquês": "da-DK", "danish": "da-DK",
    "hebraico": "he-IL", "hebrew": "he-IL",
    "romeno": "ro-RO", "romanian": "ro-RO",
    "ucraniano": "uk-UA", "ukrainian": "uk-UA",
    "filipino": "fil-PH", "tagalo": "fil-PH", "tagalog": "fil-PH",
    "vietnamita": "vi-VN", "vietnamese": "vi-VN",
    "urdu": "ur-PK",
    "amárico": "am-ET", "amharic": "am-ET",
    "tailandês": "th-TH", "thai": "th-TH",
    "cantonês": "zh-HK", "cantonese": "zh-HK",
    "tâmil": "ta-IN", "tamil": "ta-IN",
    "telugo": "te-IN", "telugu": "te-IN",
    "marata": "mr-IN", "marathi": "mr-IN",
    "guzerate": "gu-IN", "gujarati": "gu-IN",
}
PEDIDO_IDIOMA = re.compile(
    r"\b(?:em|in)\s+(" + "|".join(map(re.escape, ALIASES)) + r")\b", re.I
)



def idioma_conversa(preferencia: str, mensagem: str) -> str:
    if preferencia in IDIOMAS:
        return preferencia
    pedido = PEDIDO_IDIOMA.search(mensagem)
    if pedido:
        return ALIASES[pedido[1].lower()]
    if re.search(r"[\u05d0-\u05ea]", mensagem):
        return "he-IL"
    if re.search(r"[\u4e00-\u9fff]", mensagem):
        return "zh-CN"
    if re.search(r"[\u0621-\u064a]", mensagem):
        return "ar-SA"
    return "auto"


def resposta_no_idioma(texto: str, idioma: str) -> bool:
    if idioma in {"zh-CN", "zh-HK"}:
        return bool(re.search(r"[\u4e00-\u9fff]", texto))
    if idioma == "he-IL":
        return bool(re.search(r"[\u05d0-\u05ea]", texto))
    if idioma == "ur-PK":
        return bool(re.search(r"[\u0621-\u06d3]", texto))
    if idioma == "ar-SA":
        return bool(re.search(r"[\u0621-\u064a]", texto))
    return True


def voz_edge(idioma: str, persona: str) -> str:
    _, feminina, masculina = IDIOMAS[idioma]
    return f"{idioma}-{feminina if persona == 'Ashley' else masculina}Neural"

SAUDACOES_SIMPLES = {
    "oi": "pt-BR", "olá": "pt-BR", "ola": "pt-BR",
    "hi": "en-US", "hello": "en-US",
    "hola": "es-ES", "你好": "zh-CN", "您好": "zh-CN",
    "مرحبا": "ar-SA", "مرحبًا": "ar-SA",
    "hallo": "nl-NL", "hej": "sv-SE", "habari": "sw-KE",
    "hei": "nb-NO",
    "שלום": "he-IL",
    "salut": "ro-RO",
    "привіт": "uk-UA",
    "kumusta": "fil-PH",
    "xin chào": "vi-VN",
    "آداب": "ur-PK",
    "ሰላም": "am-ET",
    "สวัสดี": "th-TH",
    "你好呀": "zh-HK",
    "வணக்கம்": "ta-IN",
    "నమస్కారం": "te-IN",
    "नमस्कार": "mr-IN",
    "નમસ્તે": "gu-IN",
}

RESPOSTAS_SAUDACAO = {
    "pt-BR": "Olá! Como posso te ajudar?",
    "en-US": "Hello! How can I help you?",
    "es-ES": "¡Hola! ¿En qué puedo ayudarte?",
    "zh-CN": "你好！有什么我可以帮你的吗？",
    "ar-SA": "مرحبًا! كيف يمكنني مساعدتك؟",
    "de-DE": "Hallo! Wie kann ich helfen?",
    "fr-FR": "Bonjour ! Comment puis-je vous aider ?",
    "ja-JP": "こんにちは！何をお手伝いしましょうか？",
    "ru-RU": "Здравствуйте! Чем могу помочь?",
    "pl-PL": "Cześć! W czym mogę pomóc?",
    "fa-IR": "سلام! چطور می‌توانم کمک کنم؟",
    "hi-IN": "नमस्ते! मैं आपकी कैसे मदद कर सकती हूँ?",
    "bn-IN": "নমস্কার! কীভাবে সাহায্য করতে পারি?",
    "id-ID": "Halo! Ada yang bisa saya bantu?",
    "ko-KR": "안녕하세요! 무엇을 도와드릴까요?",
    "tr-TR": "Merhaba! Nasıl yardımcı olabilirim?",
    "it-IT": "Ciao! Come posso aiutarti?",
    "nl-NL": "Hallo! Hoe kan ik je helpen?",
    "sv-SE": "Hej! Hur kan jag hjälpa dig?",
    "sw-KE": "Habari! Ninaweza kukusaidiaje?",
    "nb-NO": "Hei! Hvordan kan jeg hjelpe deg?",
    "da-DK": "Hej! Hvordan kan jeg hjælpe dig?",
    "he-IL": "שלום! איך אפשר לעזור?",
    "ro-RO": "Salut! Cu ce te pot ajuta?",
    "uk-UA": "Привіт! Чим можу допомогти?",
    "fil-PH": "Kumusta! Paano kita matutulungan?",
    "vi-VN": "Xin chào! Tôi có thể giúp gì cho bạn?",
    "ur-PK": "آداب۔ میں آپ کی کیا مدد کر سکوں؟",
    "am-ET": "ሰላም። እንዴት ልርዳዎት?",
    "th-TH": "สวัสดี มีอะไรให้ช่วยไหม?",
    "zh-HK": "你好呀！有咩可以幫你？",
    "ta-IN": "வணக்கம்! நான் எப்படி உதவலாம்?",
    "te-IN": "నమస్కారం! నేను మీకు ఎలా సహాయం చేయగలను?",
    "mr-IN": "नमस्कार! तुमची कशी मदत करू?",
    "gu-IN": "નમસ્તે! હું તમને કેવી રીતે મદદ કરી શકું?",
}


def resposta_saudacao(mensagem: str, idioma: str) -> tuple[str, str] | None:
    saudacao = mensagem.strip().casefold().strip("!！¡.。?？ ")
    idioma_entrada = SAUDACOES_SIMPLES.get(saudacao)
    if idioma_entrada is None:
        return None
    idioma_resposta = idioma_entrada if idioma == "auto" else idioma
    return RESPOSTAS_SAUDACAO[idioma_resposta], idioma_resposta
