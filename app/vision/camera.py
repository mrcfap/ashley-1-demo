import base64
import binascii
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class CameraAshley:
    """
    Interface inicial da câmera da Ashley.

    Esta camada recebe uma imagem capturada pelo navegador
    em formato Base64 e transforma em arquivo local.

    A câmera permanece independente do Orquestrador.
    """

    def __init__(self, diretorio="data/vision"):
        self.diretorio = Path(diretorio)
        self.diretorio.mkdir(parents=True, exist_ok=True)

        self.ativa = False
        self.ultima_captura = None

    def estado(self):
        return {
            "motor": "Camera Ashley",
            "ativa": self.ativa,
            "ultima_captura": self.ultima_captura,
            "diretorio": str(self.diretorio),
        }

    def ativar(self):
        self.ativa = True
        return self.estado()

    def desativar(self):
        self.ativa = False
        return self.estado()

    def salvar_base64(self, imagem_base64: str):
        """
        Recebe uma imagem Base64 enviada pelo navegador.
        """

        if not isinstance(imagem_base64, str) or not imagem_base64:
            raise ValueError("Imagem vazia ou inválida.")

        if len(imagem_base64) > 3_000_000:
            raise ValueError("Imagem excede o limite de entrada.")

        if "," in imagem_base64:
            imagem_base64 = imagem_base64.split(",", 1)[1]

        try:
            dados = base64.b64decode(imagem_base64, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Imagem Base64 inválida.")

        if not dados or len(dados) > 2_000_000:
            raise ValueError("Imagem excede o limite de 2 MB.")

        if dados.startswith(b"\xff\xd8\xff"):
            extensao = "jpg"
        elif dados.startswith(b"\x89PNG\r\n\x1a\n"):
            extensao = "png"
        elif len(dados) >= 12 and dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
            extensao = "webp"
        else:
            raise ValueError("Formato de imagem não permitido.")

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        arquivo = (
            self.diretorio
            / f"captura_{timestamp}_{uuid4().hex}.{extensao}"
        )

        arquivo.write_bytes(dados)

        self.ultima_captura = str(arquivo)

        return {
            "sucesso": True,
            "arquivo": str(arquivo),
            "tamanho_bytes": len(dados),
            "timestamp": timestamp,
        }


if __name__ == "__main__":

    camera = CameraAshley()

    print("=== CAMERA ASHLEY ===")
    print(camera.estado())

    print("\nAtivando câmera lógica...")

    print(camera.ativar())