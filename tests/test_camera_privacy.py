import base64
import pytest

from app.vision.camera import CameraAshley


def test_camera_rejects_invalid_base64(tmp_path):
    camera = CameraAshley(tmp_path)
    with pytest.raises(ValueError):
        camera.salvar_base64("not-base64!!!!")


def test_camera_rejects_non_image_payload(tmp_path):
    camera = CameraAshley(tmp_path)
    payload = base64.b64encode(b"plain text").decode("ascii")
    with pytest.raises(ValueError):
        camera.salvar_base64(payload)


def test_camera_accepts_bounded_jpeg_payload(tmp_path):
    camera = CameraAshley(tmp_path)
    payload = base64.b64encode(b"\xff\xd8\xff" + b"0" * 100).decode("ascii")
    result = camera.salvar_base64(payload)
    assert result["sucesso"] is True
    assert result["tamanho_bytes"] == 103
