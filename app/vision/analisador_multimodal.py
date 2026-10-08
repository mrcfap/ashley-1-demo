import os
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from google import genai
from google.genai import types


class AnalisadorMultimodalAshley:
    """
    Camada de interpretação visual da Ashley.

    Usa os modelos configurados em GEMINI_CHAT_MODELS para
    compreender imagens e possui fallback entre modelos.
    """

    def __init__(self, timeout_ms: int = 30000):

        load_dotenv()

        self.api_key = os.getenv("GEMINI_API_KEY")

        self.modelo_principal = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        modelos_configurados = os.getenv(
            "GEMINI_CHAT_MODELS",
            self.modelo_principal
        )

        self.modelos = self._montar_lista_modelos(
            modelos_configurados
        )

        self.timeout_ms = timeout_ms
        self.provedor = "google_gemini"
        self.ativo = bool(self.api_key)

        self.cliente = None

        if self.api_key:
            self.cliente = genai.Client(
                api_key=self.api_key
            )

    # =====================================================
    # CONFIGURAÇÃO
    # =====================================================

    def _montar_lista_modelos(
        self,
        modelos: str
    ) -> List[str]:

        lista = []

        for modelo in modelos.split(","):

            modelo = modelo.strip()

            if modelo and modelo not in lista:
                lista.append(modelo)

        if self.modelo_principal not in lista:
            lista.insert(0, self.modelo_principal)

        return lista

    # =====================================================
    # ESTADO
    # =====================================================

    def estado(self) -> Dict[str, Any]:

        return {
            "motor": "Analisador Multimodal Ashley",
            "ativo": self.ativo,
            "provedor": self.provedor,
            "modelo_principal": self.modelo_principal,
            "modelos_disponiveis": self.modelos,
            "timeout_ms": self.timeout_ms,
        }

    # =====================================================
    # IMAGEM
    # =====================================================

    def carregar_imagem(
        self,
        caminho: str
    ) -> bytes:

        arquivo = Path(caminho)

        if not arquivo.exists():

            raise FileNotFoundError(
                f"Imagem não encontrada: {caminho}"
            )

        return arquivo.read_bytes()

    # =====================================================
    # MIME TYPE
    # =====================================================

    def identificar_mime_type(
        self,
        arquivo: Path
    ) -> str:

        extensoes = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }

        return extensoes.get(
            arquivo.suffix.lower(),
            "image/jpeg"
        )

    # =====================================================
    # ANÁLISE COM UM MODELO
    # =====================================================

    def _analisar_com_modelo(
        self,
        modelo: str,
        imagem: bytes,
        mime_type: str,
        pergunta: str
    ) -> str:

        resposta = self.cliente.models.generate_content(

            model=modelo,

            contents=[
                types.Part.from_bytes(
                    data=imagem,
                    mime_type=mime_type,
                ),
                pergunta,
            ],

            config=types.GenerateContentConfig(
                automatic_function_calling={
                    "disable": True
                }
            ),
        )

        if not resposta.text:
            raise RuntimeError(
                "O modelo retornou uma resposta vazia."
            )

        return resposta.text.strip()

    # =====================================================
    # ANÁLISE VISUAL
    # =====================================================

    def analisar(
        self,
        caminho: str,
        pergunta: str = (
            "Descreva detalhadamente o que está vendo."
        )
    ) -> Dict[str, Any]:

        if not self.cliente:

            return {
                "sucesso": False,
                "erro": "GEMINI_API_KEY não configurada.",
                "status": "sem_autenticacao",
            }

        arquivo = Path(caminho)

        if not arquivo.exists():

            return {
                "sucesso": False,
                "erro": f"Imagem não encontrada: {caminho}",
                "status": "arquivo_inexistente",
            }

        try:

            imagem = self.carregar_imagem(caminho)

            mime_type = self.identificar_mime_type(
                arquivo
            )

            print(
                f"[VISÃO] Imagem: {arquivo.name}"
            )

            print(
                f"[VISÃO] Tamanho: {len(imagem)} bytes"
            )

            print(
                f"[VISÃO] Modelos disponíveis: {self.modelos}"
            )

            erros = []

            # ---------------------------------------------
            # TENTATIVA COM FALLBACK
            # ---------------------------------------------

            for modelo in self.modelos:

                print(
                    f"[VISÃO] Tentando modelo: {modelo}"
                )

                try:

                    descricao = self._analisar_com_modelo(
                        modelo=modelo,
                        imagem=imagem,
                        mime_type=mime_type,
                        pergunta=pergunta,
                    )

                    print(
                        f"[VISÃO] Sucesso com: {modelo}"
                    )

                    return {

                        "sucesso": True,

                        "imagem": str(arquivo),

                        "pergunta": pergunta,

                        "modelo": modelo,

                        "descricao": descricao,

                        "objetos": [],

                        "textos_detectados": [],

                        "observacoes": [],

                        "tentativas": len(erros) + 1,

                        "erros_anteriores": erros,

                        "status": (
                            "analise_visual_concluida"
                        ),
                    }

                except Exception as erro:

                    mensagem = str(erro)

                    erros.append({
                        "modelo": modelo,
                        "erro": mensagem,
                    })

                    print(
                        f"[VISÃO] Falha em {modelo}: "
                        f"{mensagem}"
                    )

                    continue

            # ---------------------------------------------
            # TODOS OS MODELOS FALHARAM
            # ---------------------------------------------

            print(
                "[VISÃO] Todos os modelos falharam."
            )

            return {

                "sucesso": False,

                "imagem": str(arquivo),

                "pergunta": pergunta,

                "modelo": None,

                "erros": erros,

                "status": (
                    "todos_modelos_indisponiveis"
                ),
            }

        except KeyboardInterrupt:

            return {

                "sucesso": False,

                "imagem": str(arquivo),

                "pergunta": pergunta,

                "erro": (
                    "Análise interrompida pelo usuário."
                ),

                "status": "interrompido",
            }

        except Exception as erro:

            return {

                "sucesso": False,

                "imagem": str(arquivo),

                "pergunta": pergunta,

                "erro": str(erro),

                "status": (
                    "erro_analise_visual"
                ),
            }


# =========================================================
# TESTE ISOLADO
# =========================================================

if __name__ == "__main__":

    analisador = AnalisadorMultimodalAshley()

    print(
        "=== ANALISADOR MULTIMODAL ASHLEY ==="
    )

    print("\nEstado:")

    print(
        analisador.estado()
    )

    print(
        "\nIniciando análise visual...\n"
    )

    resultado = analisador.analisar(

        "teste_visao.jpeg",

        (
            "Descreva detalhadamente o que você "
            "está vendo nesta imagem. "
            "Identifique objetos, ambiente, "
            "pessoas e qualquer texto visível."
        )
    )

    print("\nResultado:")

    print(resultado)