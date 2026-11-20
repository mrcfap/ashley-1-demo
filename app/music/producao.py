"""V28: produção de canções com provedor externo configurável.

Contrato do provedor (POST JSON):
  entrada: {title, lyrics, style, prompt, vocal, duration_seconds, bpm, key}
  resposta: {audio_url: 'https://...'} OU {audio_base64: '...', format: 'mp3'|'wav'}
Também aceita {status:'processing', status_url:'https://...'} para consultar por GET.
Nunca declara sucesso se não houver áudio real.
"""
from __future__ import annotations
import base64
import binascii
import ipaddress
import os
from pathlib import Path
import socket
from urllib.parse import urlparse
import uuid
import httpx

class ErroProducaoMusical(RuntimeError):
    pass

def _url_publica(url: str) -> bool:
    u = urlparse(url)
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        return False
    try:
        infos = socket.getaddrinfo(u.hostname, None)
        return bool(infos) and all(ipaddress.ip_address(i[4][0]).is_global for i in infos)
    except (OSError, ValueError):
        return False

def _validar_audio(dados: bytes) -> str:
    if dados.startswith(b'ID3') or (len(dados)>4 and dados[0] == 0xff and dados[1] & 0xe0 == 0xe0):
        return 'mp3'
    if dados[:4] == b'RIFF' and dados[8:12] == b'WAVE':
        return 'wav'
    raise ErroProducaoMusical('O provedor não retornou um arquivo MP3 ou WAV válido.')

class ProducaoMusicalV28:
    def __init__(self, endpoint=None, api_key=None, pasta_saida='data/generated/music'):
        self.endpoint = endpoint or os.getenv('ASHLEY_MUSIC_API_URL', '')
        self.api_key = api_key or os.getenv('ASHLEY_MUSIC_API_KEY', '')
        self.pasta_saida = Path(pasta_saida)

    def gerar(self, *, titulo, letra, estilo='rock', voz='masculina', duracao_segundos=180, bpm=100, tom='Am', prompt_extra=''):
        if not self.endpoint or not self.api_key:
            raise ErroProducaoMusical('Configure ASHLEY_MUSIC_API_URL e ASHLEY_MUSIC_API_KEY para gerar música cantada.')
        if not _url_publica(self.endpoint):
            raise ErroProducaoMusical('O endpoint musical deve ser HTTPS público e seguro.')
        if not 30 <= int(duracao_segundos) <= 600:
            raise ValueError('Duração deve ser de 30 a 600 segundos.')
        if not 40 <= int(bpm) <= 220:
            raise ValueError('BPM deve ficar entre 40 e 220.')
        if not str(letra).strip():
            raise ValueError('A letra da música é obrigatória.')
        payload = {
            'title': str(titulo)[:150], 'lyrics': str(letra)[:10000],
            'style': str(estilo)[:160], 'vocal': str(voz)[:80],
            'duration_seconds': int(duracao_segundos), 'bpm': int(bpm),
            'key': str(tom)[:16],
            'prompt': f'Canção original completa, com voz cantada, instrumentos, mixagem e masterização. {prompt_extra}'[:1500],
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}
        with httpx.Client(timeout=120, follow_redirects=False) as cliente:
            try:
                resp = cliente.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                resultado = resp.json()
                if not isinstance(resultado, dict):
                    raise ErroProducaoMusical('Resposta inesperada do provedor musical.')
                # Alguns provedores entregam a geração por tarefa assíncrona.
                for _ in range(20):
                    if resultado.get('audio_url') or resultado.get('audio_base64'):
                        break
                    status_url = resultado.get('status_url')
                    if not status_url:
                        break
                    if not _url_publica(status_url):
                        raise ErroProducaoMusical('URL de acompanhamento inválida.')
                    import time
                    time.sleep(3)
                    r = cliente.get(status_url, headers=headers)
                    r.raise_for_status()
                    resultado = r.json()
                    if resultado.get('status') in ('failed','error','cancelled'):
                        raise ErroProducaoMusical('O provedor informou falha na geração musical.')
                if resultado.get('audio_base64'):
                    dados = base64.b64decode(resultado['audio_base64'], validate=True)
                elif resultado.get('audio_url'):
                    url = resultado['audio_url']
                    if not _url_publica(url):
                        raise ErroProducaoMusical('URL do áudio inválida.')
                    r = cliente.get(url)
                    r.raise_for_status()
                    dados = r.content
                else:
                    raise ErroProducaoMusical('O provedor ainda não entregou áudio final. Consulte a tarefa no provedor.')
            except (httpx.HTTPError, ValueError, binascii.Error) as exc:
                raise ErroProducaoMusical(f'Falha na produção musical: {type(exc).__name__}') from exc
        if len(dados) > 50 * 1024 * 1024:
            raise ErroProducaoMusical('Áudio excede 50 MB.')
        extensao = _validar_audio(dados)
        self.pasta_saida.mkdir(parents=True, exist_ok=True)
        caminho = self.pasta_saida / f'v28_{uuid.uuid4().hex}.{extensao}'
        caminho.write_bytes(dados)
        return {'status':'concluido', 'audio_gerado':True, 'arquivo':str(caminho), 'formato':extensao, 'bytes':len(dados), 'titulo':str(titulo)[:150]}
