"""Regressões locais de geração de imagem e música pelo SDK Google."""

import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from google.genai import errors, types

from app.services.gemini_service import GeminiService


@pytest.fixture
def service_client(tmp_path, monkeypatch):
    service = GeminiService(tmp_path, tmp_path / "gerados")
    client = Mock()
    client.aio.aclose = AsyncMock()
    client.aio.models.generate_content = AsyncMock()
    client.aio.interactions.create = AsyncMock()
    monkeypatch.setattr(service, "_client", lambda: client)
    return service, client


@pytest.mark.asyncio
async def test_image_uses_fallback_on_missing_model_and_preserves_jpeg(service_client):
    service, client = service_client
    service.image_models = ["indisponivel", "alternativo"]
    raw = b"\xff\xd8\xffimagem-de-teste"
    client.aio.models.generate_content.side_effect = [
        errors.ClientError(404, {"error": {"message": "Modelo ausente"}}),
        types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(parts=[
            types.Part(text="Legenda"),
            types.Part.from_bytes(data=raw, mime_type="image/jpeg"),
        ]))]),
    ]

    path, model = await service.gerar_imagem("Paisagem azul", "4:3")

    assert model == "alternativo"
    assert path.suffix == ".jpg" and path.read_bytes() == raw
    assert client.aio.models.generate_content.call_args.kwargs["config"].image_config.aspect_ratio == "4:3"


@pytest.mark.asyncio
async def test_music_decodes_lyria_mp3(service_client):
    service, client = service_client
    service.music_model = "lyria-3.5"
    raw = b"ID3audio-de-teste"
    client.aio.interactions.create.return_value = SimpleNamespace(
        output_audio=SimpleNamespace(data=base64.b64encode(raw).decode("ascii")),
    )

    path, model = await service.gerar_musica("Rock instrumental")

    assert model == "lyria-3.5"
    assert path.suffix == ".mp3" and path.read_bytes() == raw
    client.aio.interactions.create.assert_awaited_once_with(model=model, input="Rock instrumental")


@pytest.mark.asyncio
async def test_music_does_not_publish_non_audio_response(service_client):
    service, client = service_client
    client.aio.interactions.create.return_value = SimpleNamespace(output_audio=None)

    with pytest.raises(HTTPException, match="MP3 válido") as caught:
        await service.gerar_musica("Rock instrumental")

    assert caught.value.status_code == 502
    assert list(service.generated_dir.iterdir()) == []
