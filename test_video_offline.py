"""Regressões da migração de vídeo para a Interactions API."""

import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from google.genai import errors

from app.services.gemini_service import GeminiService, OMNI_VIDEO_MODEL


@pytest.fixture
def video_service(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_VIDEO_MODELS", "veo-3.1-generate-preview")
    service = GeminiService(tmp_path, tmp_path / "gerados")
    client = Mock()
    client.aio.aclose = AsyncMock()
    client.aio.interactions.create = AsyncMock()
    monkeypatch.setattr(service, "_client", lambda **kwargs: client)
    return service, client


def test_video_migrates_retired_env_models_and_keeps_custom_settings(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "GEMINI_VIDEO_MODELS",
        "models/veo-3.1-generate-preview,veo-3.1-fast-generate-preview,"
        "veo-3.1-lite-generate-preview,gemini-omni-1.1-flash",
    )
    service = GeminiService(tmp_path, tmp_path / "gerados")
    assert service.modelos_publicos()["video"] == [OMNI_VIDEO_MODEL, "gemini-omni-1.1-flash"]


@pytest.mark.asyncio
async def test_video_decodes_inline_mp4_and_sends_omni_parameters(video_service):
    service, client = video_service
    raw = b"\x00\x00\x00\x18ftypmp42offline-test"
    client.aio.interactions.create.return_value = SimpleNamespace(
        output_video=SimpleNamespace(data=base64.b64encode(raw).decode()),
    )

    path, model = await service.gerar_video("Uma paisagem", "9:16", "1080p")

    assert path.suffix == ".mp4"
    assert path.read_bytes() == raw
    assert model == OMNI_VIDEO_MODEL
    client.aio.interactions.create.assert_awaited_once_with(
        model=OMNI_VIDEO_MODEL, input="Uma paisagem",
        response_format={"type": "video", "aspect_ratio": "9:16", "resolution": "1080p", "duration": "8s"},
    )
    client.aio.aclose.assert_awaited_once()


@pytest.mark.parametrize("data, expected", [
    (None, "não retornou vídeo"),
    ("!!!!", "MP4 válido"),
    ("dGV4dG8=", "MP4 válido"),
])
@pytest.mark.asyncio
async def test_video_does_not_publish_missing_or_invalid_output(video_service, data, expected):
    service, client = video_service
    client.aio.interactions.create.return_value = SimpleNamespace(
        output_video=SimpleNamespace(data=data) if data is not None else None,
    )
    with pytest.raises(HTTPException, match=expected) as caught:
        await service.gerar_video("Uma paisagem")
    assert caught.value.status_code == 502
    assert not list(service.generated_dir.iterdir())


@pytest.mark.asyncio
async def test_video_quota_is_reported_without_provider_payload(video_service):
    service, client = video_service
    client.aio.interactions.create.side_effect = errors.ClientError(
        429, {"error": {"message": "mensagem bruta de teste"}},
    )
    with pytest.raises(HTTPException) as caught:
        await service.gerar_video("Uma paisagem")
    assert caught.value.status_code == 429
    assert "mensagem bruta" not in caught.value.detail
