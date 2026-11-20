from app.services.texto_voz import limpar_resposta_modelo, preparar_texto_voz

def test_oculta_raciocinio():
    assert limpar_resposta_modelo("<think>English planning</think>你好！") == "你好！"
    assert limpar_resposta_modelo("<think>unfinished") == ""
    assert limpar_resposta_modelo("<analysis>draft</analysis><final>你好！</final>") == "你好！"

def test_tts_sem_raciocinio():
    assert preparar_texto_voz("<think>I will translate</think>你好，世界！") == "你好，世界！"
