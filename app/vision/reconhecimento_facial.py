import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from app.vision.perfil_persistente import PerfilFacialPersistente
from typing import Any, Dict, List, Optional

import cv2
import numpy as np


class ReconhecimentoFacialAshley:
    """
    Motor local de percepção e reconhecimento facial da Ashley.

    Capacidades:
    - detecção facial com YuNet;
    - pontos faciais;
    - alinhamento facial;
    - assinatura biométrica com SFace;
    - cadastro local com múltiplas amostras;
    - carregamento de perfis cadastrados;
    - comparação biométrica;
    - classificação: conhecido, incerto ou desconhecido.

    Todo o reconhecimento é executado localmente.
    """

    def __init__(self):
        self._model_lock = RLock()
        base_dir = Path(__file__).resolve().parent
        models_dir = base_dir / "models"

        # =========================================================
        # YUNET - DETECÇÃO
        # =========================================================

        self.modelo_detector = (
            models_dir / "face_detection_yunet_2023mar.onnx"
        )

        if not self.modelo_detector.exists():
            raise FileNotFoundError(
                f"Modelo YuNet não encontrado: {self.modelo_detector}"
            )

        self.detector = cv2.FaceDetectorYN.create(
            str(self.modelo_detector),
            "",
            (320, 320),
            0.9,
            0.3,
            5000,
        )

        # =========================================================
        # SFACE - RECONHECIMENTO
        # =========================================================

        self.modelo_reconhecedor = (
            models_dir / "face_recognition_sface_2021dec.onnx"
        )

        if not self.modelo_reconhecedor.exists():
            raise FileNotFoundError(
                f"Modelo SFace não encontrado: "
                f"{self.modelo_reconhecedor}"
            )

        self.reconhecedor = cv2.FaceRecognizerSF.create(
            str(self.modelo_reconhecedor),
            "",
        )

        # =========================================================
        # PERFIS BIOMÉTRICOS
        # =========================================================

        self.persistencia = PerfilFacialPersistente()
        self.pasta_perfis = base_dir / "perfis_faciais"
        self.pasta_perfis.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =============================================================
    # DETECÇÃO RAW
    # =============================================================

    def _detectar_faces_raw(
        self,
        imagem: np.ndarray,
    ) -> Optional[np.ndarray]:

        altura, largura = imagem.shape[:2]

        with self._model_lock:
            self.detector.setInputSize((largura, altura))
            _, faces = self.detector.detect(imagem)

        return faces

    def _avaliar_luz(self, imagem: np.ndarray) -> str:
        pequena = cv2.resize(imagem, (160, 120), interpolation=cv2.INTER_AREA)
        cinza = cv2.cvtColor(pequena, cv2.COLOR_BGR2GRAY)
        centro = cinza[30:95, 52:108]
        if float(np.percentile(cinza, 90)) < 42:
            return "quadro_escuro"
        if float(np.median(centro)) < 47 and float(np.percentile(cinza, 90)) > 130:
            return "possivel_contraluz"
        return "normal"

    # =============================================================
    # DETECÇÃO FACIAL
    # =============================================================

    def detectar(
        self,
        caminho_imagem: str,
    ) -> Dict[str, Any]:

        caminho = Path(caminho_imagem)

        if not caminho.exists():
            return {
                "sucesso": False,
                "status": "imagem_nao_encontrada",
                "arquivo": str(caminho),
                "quantidade_rostos": 0,
                "rostos": [],
            }

        imagem = cv2.imread(str(caminho))

        if imagem is None:
            return {
                "sucesso": False,
                "status": "imagem_invalida",
                "arquivo": str(caminho),
                "quantidade_rostos": 0,
                "rostos": [],
            }

        altura, largura = imagem.shape[:2]

        faces = self._detectar_faces_raw(imagem)

        rostos: List[Dict[str, Any]] = []

        if faces is not None:

            for indice, face in enumerate(
                faces,
                start=1,
            ):

                x = int(face[0])
                y = int(face[1])
                w = int(face[2])
                h = int(face[3])

                confianca = float(face[-1])

                pontos = {
                    "olho_direito": [
                        float(face[4]),
                        float(face[5]),
                    ],
                    "olho_esquerdo": [
                        float(face[6]),
                        float(face[7]),
                    ],
                    "nariz": [
                        float(face[8]),
                        float(face[9]),
                    ],
                    "boca_direita": [
                        float(face[10]),
                        float(face[11]),
                    ],
                    "boca_esquerda": [
                        float(face[12]),
                        float(face[13]),
                    ],
                }

                rostos.append(
                    {
                        "indice": indice,
                        "x": x,
                        "y": y,
                        "largura": w,
                        "altura": h,
                        "confianca_deteccao": round(
                            confianca,
                            4,
                        ),
                        "pontos_faciais": pontos,
                    }
                )

        return {
            "sucesso": True,
            "status": (
                "rostos_detectados"
                if rostos
                else "nenhum_rosto_detectado"
            ),
            "arquivo": str(caminho),
            "largura_imagem": largura,
            "altura_imagem": altura,
            "quantidade_rostos": len(rostos),
            "iluminacao": self._avaliar_luz(imagem),
            "rostos": rostos,
        }

    # =============================================================
    # EXTRAÇÃO DE ASSINATURA
    # =============================================================

    def extrair_assinatura(
        self,
        caminho_imagem: str,
    ) -> Dict[str, Any]:

        caminho = Path(caminho_imagem)

        if not caminho.exists():
            return {
                "sucesso": False,
                "status": "imagem_nao_encontrada",
                "arquivo": str(caminho),
            }

        imagem = cv2.imread(str(caminho))

        if imagem is None:
            return {
                "sucesso": False,
                "status": "imagem_invalida",
                "arquivo": str(caminho),
            }

        faces = self._detectar_faces_raw(imagem)

        if faces is None or len(faces) == 0:
            return {
                "sucesso": False,
                "status": "nenhum_rosto_detectado",
                "arquivo": str(caminho),
            }

        if len(faces) != 1:
            return {
                "sucesso": False,
                "status": "multiplos_rostos_detectados",
                "arquivo": str(caminho),
                "quantidade_rostos": int(len(faces)),
            }

        face = faces[0]

        rosto_alinhado = self.reconhecedor.alignCrop(
            imagem,
            face,
        )

        assinatura = self.reconhecedor.feature(
            rosto_alinhado
        )

        if assinatura is None:
            return {
                "sucesso": False,
                "status": "falha_ao_gerar_assinatura",
                "arquivo": str(caminho),
            }

        assinatura = np.asarray(
            assinatura,
            dtype=np.float32,
        ).flatten()

        return {
            "sucesso": True,
            "status": "assinatura_gerada",
            "arquivo": str(caminho),
            "confianca_deteccao": round(
                float(face[-1]),
                4,
            ),
            "dimensoes_assinatura": int(
                assinatura.size
            ),
            "_assinatura": assinatura,
        }

    def _arquivo_conta(self, user_id: int) -> Path:
        return self.pasta_perfis / "contas" / f"{int(user_id)}.npz"

    def _assinaturas_arquivo(self, arquivo: Path) -> Optional[np.ndarray]:
        try:
            with np.load(arquivo, allow_pickle=False) as dados:
                matriz = np.asarray(dados["assinaturas"], dtype=np.float32)
                if matriz.ndim == 2 and matriz.shape[1] == 128 and len(matriz) and np.isfinite(matriz).all():
                    if np.all(np.linalg.norm(matriz, axis=1) > 0):
                        return matriz
        except (OSError, ValueError, KeyError):
            pass
        return None

    def _assinatura_conta(self, caminho: str) -> tuple[str, Optional[np.ndarray]]:
        imagem = cv2.imread(caminho)
        if imagem is None:
            return "imagem_invalida", None
        faces = self._detectar_faces_raw(imagem)
        if faces is None or len(faces) == 0:
            return "nenhum_rosto_detectado", None
        if len(faces) != 1:
            return "multiplos_rostos_detectados", None
        face = faces[0]
        x, y, w, h = map(int, face[:4])
        regiao = imagem[max(0, y):y + h, max(0, x):x + w]
        if min(w, h) < 72 or regiao.size == 0:
            return "rosto_pequeno", None
        if float(np.median(cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY))) < 45:
            return "rosto_pouco_iluminado", None
        with self._model_lock:
            alinhado = self.reconhecedor.alignCrop(imagem, face)
            assinatura = self.reconhecedor.feature(alinhado)
        vetor = np.asarray(assinatura, dtype=np.float32).reshape(-1)
        if vetor.size != 128 or not np.isfinite(vetor).all() or not np.any(vetor):
            return "falha_assinatura", None
        return "assinatura_gerada", vetor

    def _pontuacao_conta(self, assinatura: np.ndarray, amostras: np.ndarray) -> float:
        with self._model_lock:
            return max(self.comparar_assinaturas(assinatura, amostra) for amostra in amostras)

    def _amostras_conta(self, user_id: int) -> Optional[np.ndarray]:
        matriz = self.persistencia.carregar(user_id)
        if matriz is not None:
            return matriz
        legado = self._assinaturas_arquivo(self._arquivo_conta(user_id))
        if legado is not None and self.persistencia.ativo:
            self.persistencia.salvar(user_id, legado)
            self._arquivo_conta(user_id).unlink(missing_ok=True)
        return legado

    def tem_perfil_conta(self, user_id: int) -> bool:
        return self._amostras_conta(user_id) is not None

    def identificar_conta(self, caminho: str, user_id: int, nome: str) -> Dict[str, Any]:
        amostras = self._amostras_conta(user_id)
        if amostras is None:
            return {"sucesso": False, "status": "perfil_facial_ausente"}
        status, assinatura = self._assinatura_conta(caminho)
        if assinatura is None:
            return {"sucesso": False, "status": status}
        pontuacao = self._pontuacao_conta(assinatura, amostras)
        classificacao = "conhecido" if pontuacao >= 0.65 else "incerto" if pontuacao >= 0.50 else "desconhecido"
        return {
            "sucesso": True,
            "status": "comparacao_local_concluida",
            "classificacao": classificacao,
            "identidade": nome if classificacao == "conhecido" else None,
            "similaridade": round(pontuacao, 4),
            "quantidade_rostos": 1,
        }

    def cadastrar_conta(self, caminho: str, user_id: int, nome_legado: Optional[str] = None) -> str:
        status, assinatura = self._assinatura_conta(caminho)
        if assinatura is None:
            return status
        amostras = assinatura.reshape(1, -1)
        if nome_legado is not None:
            chave = "".join(c for c in nome_legado.casefold() if c.isalnum() or c in "_-")
            anterior = self._assinaturas_arquivo(self.pasta_perfis / f"{chave}.npz")
            if anterior is None:
                return "perfil_legado_ausente"
            if self._pontuacao_conta(assinatura, anterior) < 0.65:
                return "perfil_legado_nao_confirmado"
            amostras = anterior
        if self.persistencia.ativo:
            self.persistencia.salvar(user_id, amostras)
            self._arquivo_conta(user_id).unlink(missing_ok=True)
            return "perfil_vinculado" if nome_legado is not None else "perfil_cadastrado"
        if os.getenv("RENDER") or os.getenv("ASHLEY_REQUIRE_PERSISTENT_FACE") == "1":
            return "persistencia_facial_nao_configurada"
        destino = self._arquivo_conta(user_id)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=destino.parent, suffix=".npz", delete=False) as tmp:
            temporario = Path(tmp.name)
            try:
                np.savez_compressed(tmp, assinaturas=amostras)
                tmp.flush()
            except BaseException:
                tmp.close()
                temporario.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporario, destino)
        finally:
            temporario.unlink(missing_ok=True)
        return "perfil_vinculado" if nome_legado is not None else "perfil_cadastrado"

    def remover_conta(self, user_id: int) -> None:
        if self.persistencia.ativo:
            self.persistencia.remover(user_id)
        self._arquivo_conta(user_id).unlink(missing_ok=True)

    # =============================================================
    # CADASTRO
    # =============================================================

    def cadastrar_pessoa(
        self,
        nome: str,
        caminhos_imagens: List[str],
    ) -> Dict[str, Any]:

        nome = nome.strip()

        if not nome:
            return {
                "sucesso": False,
                "status": "nome_invalido",
            }

        if not caminhos_imagens:
            return {
                "sucesso": False,
                "status": "nenhuma_imagem_informada",
            }

        assinaturas: List[np.ndarray] = []

        for caminho in caminhos_imagens:

            resultado = self.extrair_assinatura(
                caminho
            )

            if not resultado.get("sucesso"):
                return {
                    "sucesso": False,
                    "status": "falha_em_uma_das_amostras",
                    "arquivo": caminho,
                    "detalhes": resultado,
                }

            assinatura = resultado.get(
                "_assinatura"
            )

            if assinatura is None:
                return {
                    "sucesso": False,
                    "status": "assinatura_ausente",
                    "arquivo": caminho,
                }

            assinaturas.append(
                assinatura
            )

        matriz = np.vstack(
            assinaturas
        ).astype(np.float32)

        nome_seguro = "".join(
            caractere
            for caractere in nome.lower()
            if caractere.isalnum()
            or caractere in ("_", "-")
        )

        if not nome_seguro:
            return {
                "sucesso": False,
                "status": "nome_invalido_para_arquivo",
            }

        arquivo_perfil = (
            self.pasta_perfis
            / f"{nome_seguro}.npz"
        )

        np.savez_compressed(
            arquivo_perfil,
            nome=nome,
            assinaturas=matriz,
        )

        return {
            "sucesso": True,
            "status": "pessoa_cadastrada",
            "nome": nome,
            "quantidade_amostras": int(
                matriz.shape[0]
            ),
            "dimensoes_assinatura": int(
                matriz.shape[1]
            ),
            "arquivo_perfil": str(
                arquivo_perfil
            ),
        }

    # =============================================================
    # CARREGAMENTO DOS PERFIS
    # =============================================================

    def carregar_perfis(
        self,
    ) -> List[Dict[str, Any]]:

        perfis: List[Dict[str, Any]] = []

        for arquivo in self.pasta_perfis.glob(
            "*.npz"
        ):

            try:
                dados = np.load(
                    arquivo,
                    allow_pickle=False,
                )

                nome = str(
                    dados["nome"].item()
                )

                assinaturas = np.asarray(
                    dados["assinaturas"],
                    dtype=np.float32,
                )

                if assinaturas.ndim != 2:
                    continue

                if assinaturas.shape[1] != 128:
                    continue

                perfis.append(
                    {
                        "nome": nome,
                        "arquivo": str(arquivo),
                        "assinaturas": assinaturas,
                    }
                )

            except Exception:
                continue

        return perfis

    # =============================================================
    # COMPARAÇÃO ENTRE DUAS ASSINATURAS
    # =============================================================

    def comparar_assinaturas(
        self,
        assinatura_a: np.ndarray,
        assinatura_b: np.ndarray,
    ) -> float:

        assinatura_a = np.asarray(
            assinatura_a,
            dtype=np.float32,
        ).reshape(1, -1)

        assinatura_b = np.asarray(
            assinatura_b,
            dtype=np.float32,
        ).reshape(1, -1)

        similaridade = self.reconhecedor.match(
            assinatura_a,
            assinatura_b,
            cv2.FaceRecognizerSF_FR_COSINE,
        )

        return float(similaridade)

    # =============================================================
    # RECONHECIMENTO DE PESSOA
    # =============================================================

    def reconhecer_pessoa(
        self,
        caminho_imagem: str,
        limiar_conhecido: float = 0.65,
        limiar_incerto: float = 0.50,
    ) -> Dict[str, Any]:
        """
        Compara uma nova fotografia contra todos os perfis locais.

        Estados:
        - conhecido
        - incerto
        - desconhecido

        Os limiares são parâmetros iniciais.
        Devem ser calibrados com testes reais antes de uso definitivo.
        """

        resultado = self.extrair_assinatura(
            caminho_imagem
        )

        if not resultado.get("sucesso"):
            return {
                "sucesso": False,
                "status": resultado.get(
                    "status",
                    "falha_assinatura",
                ),
                "detalhes": resultado,
            }

        assinatura_teste = resultado[
            "_assinatura"
        ]

        perfis = self.carregar_perfis()

        if not perfis:
            return {
                "sucesso": False,
                "status": "nenhum_perfil_cadastrado",
            }

        melhor_nome = None
        melhor_pontuacao = -1.0
        melhor_amostra = None

        resultados_perfis = []

        for perfil in perfis:

            pontuacoes = []

            for indice, assinatura_cadastrada in enumerate(
                perfil["assinaturas"],
                start=1,
            ):

                pontuacao = self.comparar_assinaturas(
                    assinatura_teste,
                    assinatura_cadastrada,
                )

                pontuacoes.append(
                    pontuacao
                )

                if pontuacao > melhor_pontuacao:
                    melhor_pontuacao = pontuacao
                    melhor_nome = perfil["nome"]
                    melhor_amostra = indice

            resultados_perfis.append(
                {
                    "nome": perfil["nome"],
                    "melhor_pontuacao": round(
                        max(pontuacoes),
                        4,
                    ),
                    "media_pontuacao": round(
                        float(np.mean(pontuacoes)),
                        4,
                    ),
                    "quantidade_amostras": len(
                        pontuacoes
                    ),
                }
            )

        # ---------------------------------------------------------
        # CLASSIFICAÇÃO
        # ---------------------------------------------------------

        if melhor_pontuacao >= limiar_conhecido:

            classificacao = "conhecido"
            identidade = melhor_nome

        elif melhor_pontuacao >= limiar_incerto:

            classificacao = "incerto"
            identidade = None

        else:

            classificacao = "desconhecido"
            identidade = None

        return {
            "sucesso": True,
            "status": "reconhecimento_concluido",
            "classificacao": classificacao,
            "identidade": identidade,
            "melhor_candidato": melhor_nome,
            "similaridade": round(
                melhor_pontuacao,
                4,
            ),
            "amostra_mais_proxima": melhor_amostra,
            "confianca_deteccao": resultado.get(
                "confianca_deteccao"
            ),
            "limiares": {
                "conhecido": limiar_conhecido,
                "incerto": limiar_incerto,
            },
            "comparacoes": resultados_perfis,
        }