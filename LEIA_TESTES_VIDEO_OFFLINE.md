# Ashley 1.0 — homologação offline da geração de vídeo

O arquivo `test_video_offline.py` testa a classe `GeminiService` sem chamar Gemini/Veo e sem usar chave de API. A dependência Google é substituída por um objeto simulado antes da importação.

## Como executar no Windows

1. Extraia `test_video_offline.py` na raiz da pasta `Ashley Oficial final`.
2. Abra o PowerShell nessa pasta e execute:

```powershell
python test_video_offline.py
```

Esperado: `Ran 3 tests` e `OK`.

## Casos cobertos

1. Simulação de sucesso: parâmetros `prompt`, `aspect_ratio=16:9`, `resolution=720p`, modelo retornado, arquivo `.mp4` criado com bytes simulados.
2. Resposta sem vídeo: erro HTTP 502 esperado.
3. Erro de cota 429: comportamento **atual** da aplicação é converter em HTTP 502. O teste documenta esse comportamento, não o aprova como tratamento ideal.

## Limites

O `.mp4` é apenas um arquivo fictício de teste, **não é um vídeo reproduzível**. Os testes não cobrem o serviço externo real, reprodução, autenticação FastAPI, endpoint HTTP, logs, armazenamento persistente, fila de operações nem o comportamento do SDK real. Nenhuma alteração no backend é feita pelo pacote.

Recomendações: mapear `429 RESOURCE_EXHAUSTED` para um erro de cota claro; limitar novas tentativas; validar bytes de vídeo e arquivo final; adicionar testes do endpoint com `TestClient` e autenticação simulada.
