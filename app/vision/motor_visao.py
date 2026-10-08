from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class MotorVisaoAshley:
    """
    Motor de Visão da Ashley.

    Responsabilidades:
    - receber imagens;
    - validar a entrada visual;
    - preparar a imagem para análise multimodal;
    - devolver uma percepção visual estruturada;
    - manter a visão desacoplada do Orquestrador.
    """

    def __init__(self):
        self.ativo = True
        self.ultima_percepcao: Optional[Dict[str, Any]] = None

    def estado(self) -> Dict[str, Any]:
        return {
            "motor": "Motor de Visão Ashley",
            "ativo": self.ativo,
            "ultima_percepcao": self.ultima_percepcao,
        }

    def validar_imagem(self, caminho_imagem: str) -> Path:
        caminho = Path(caminho_imagem)

        if not caminho.exists():
            raise FileNotFoundError(
                f"Imagem não encontrada: {caminho_imagem}"
            )

        extensoes_permitidas = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        if caminho.suffix.lower() not in extensoes_permitidas:
            raise ValueError(
                "Formato não suportado. "
                "Use JPG, JPEG, PNG ou WEBP."
            )

        return caminho

    def perceber(
        self,
        caminho_imagem: str,
        pergunta: str = "Descreva o que está vendo."
    ) -> Dict[str, Any]:

        caminho = self.validar_imagem(caminho_imagem)

        percepcao = {
            "sucesso": True,
            "timestamp": datetime.now().isoformat(),
            "origem": str(caminho),
            "pergunta": pergunta,
            "tipo": "imagem",
            "status": "imagem_validada",
            "descricao": None,
            "objetos": [],
            "textos_detectados": [],
            "observacoes": [],
        }

        self.ultima_percepcao = percepcao

        return percepcao