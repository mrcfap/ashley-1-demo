import os
from unittest.mock import patch
import pytest
import numpy as np
from app.services.navegacao_segura import validar_url
from app.vision.perfil_persistente import PerfilFacialPersistente


def test_browser_rejects_unapproved_and_internal():
    with patch.dict(os.environ, {"ASHLEY_BROWSER_ALLOWED_DOMAINS": "example.com"}):
        for url in ["http://example.com", "https://localhost", "https://127.0.0.1", "https://evil.com", "https://user:password@example.com"]:
            with pytest.raises(ValueError):
                validar_url(url)


def test_browser_allows_public_domain_with_dns_mock():
    with patch.dict(os.environ, {"ASHLEY_BROWSER_ALLOWED_DOMAINS": "example.com"}):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, '', ('93.184.215.14', 443))]):
            assert validar_url("https://example.com/path") == "https://example.com/path"


def test_face_store_requires_explicit_configuration():
    with patch.dict(os.environ, {}, clear=True):
        store = PerfilFacialPersistente()
        assert not store.ativo
        assert store.carregar(1) is None
        with pytest.raises(RuntimeError):
            store.salvar(1, np.ones((1,128),dtype=np.float32))
