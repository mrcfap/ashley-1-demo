from app.services.idioma import detectar_idioma_texto_tts


def test_urdu_texto_auto():
    assert detectar_idioma_texto_tts("شروع کرنے کی ہمت ہر کامیابی کا بیج ہے۔") == "ur-PK"


def test_selecao_explicita_tem_precedencia():
    assert detectar_idioma_texto_tts("Olá", "en-US") == "en-US"


def test_scripts_nao_latinos():
    assert detectar_idioma_texto_tts("שלום") == "he-IL"
    assert detectar_idioma_texto_tts("こんにちは") == "ja-JP"
    assert detectar_idioma_texto_tts("வணக்கம்") == "ta-IN"


def test_portugues_padrao():
    assert detectar_idioma_texto_tts("Bom dia") == "pt-BR"
