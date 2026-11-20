"""Detecção de rostos em quadros consentidos, sem retenção da imagem.
Não identifica pessoas e não executa pesquisa na internet.
"""
import base64
import binascii
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Optional

from pydantic import BaseModel, Field
from app.vision.eventos_presenca import EventosPresenca

class PresencaInput(BaseModel):
    user_id: int = Field(gt=0)
    image: str = Field(min_length=20, max_length=3_000_000)
    camera_autorizada: bool = False
    interacao_espontanea: bool = False

class PresencaAoVivo:
    def __init__(self, detector=None, relogio=monotonic):
        self._detector = detector
        self._lock = RLock()
        self._eventos = EventosPresenca(quadros_confirmacao=2, quadros_saida=3, intervalo_convite=300, relogio=relogio)
        self._ultima = {}
        self._relogio = relogio

    def _contar(self, image):
        if self._detector is not None:
            return int(self._detector(image))
        import cv2
        import numpy as np
        from pathlib import Path
        from app.vision.reconhecimento_facial import ReconhecimentoFacialAshley
        raw=image.split(',',1)[-1]
        try: dados=base64.b64decode(raw,validate=True)
        except (binascii.Error, ValueError): raise ValueError('Base64 inválido')
        if len(dados)>2_000_000: raise ValueError('Quadro excede 2 MB')
        frame=cv2.imdecode(np.frombuffer(dados,dtype=np.uint8),cv2.IMREAD_COLOR)
        if frame is None: raise ValueError('Imagem inválida')
        h,w=frame.shape[:2]
        if h*w>1920*1080: raise ValueError('Resolução excessiva')
        # detector de rostos apenas; não acessa os perfis biométricos
        modelo=Path(__file__).resolve().parent/'models/face_detection_yunet_2023mar.onnx'
        if not modelo.exists(): raise ValueError('Modelo YuNet não encontrado')
        detector=cv2.FaceDetectorYN.create(str(modelo),'',(w,h),0.75,0.3,5000)
        _,faces=detector.detect(frame)
        return 0 if faces is None else len(faces)

    def processar(self, data: PresencaInput):
        key=str(data.user_id)
        with self._lock:
            if not data.camera_autorizada:
                self.encerrar(data.user_id)
                return {'sucesso':True,'camera_ativa':False,'eventos':[]}
            quantidade=self._contar(data.image)
            eventos=self._eventos.observar(key,quantidade,True,data.interacao_espontanea)
            self._ultima[key]={'quantidade_rostos':quantidade,'atualizado_em_monotonic':self._relogio()}
            return {'sucesso':True,'camera_ativa':True,'quantidade_rostos':quantidade,'eventos':eventos,'aviso':'Detecção de rostos não garante contagem de todas as pessoas'}

    def status(self,user_id):
        with self._lock:
            dado=self._ultima.get(str(user_id))
            return {'ativo':bool(dado),'quantidade_rostos':dado['quantidade_rostos'] if dado else None}

    def encerrar(self,user_id):
        with self._lock:
            self._eventos.encerrar(str(user_id))
            self._ultima.pop(str(user_id),None)
