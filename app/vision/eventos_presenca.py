"""Eventos de presença para câmera consentida. Não identifica desconhecidos."""
from dataclasses import dataclass, field
from time import monotonic
from typing import Callable

@dataclass
class EstadoPresenca:
    presente: bool = False
    vistos: int = 0
    ausentes: int = 0
    ultimo_convite: float = float('-inf')

class EventosPresenca:
    def __init__(self, quadros_confirmacao=2, quadros_saida=3, intervalo_convite=300, relogio: Callable[[],float]=monotonic):
        if min(quadros_confirmacao, quadros_saida) < 1 or intervalo_convite < 0:
            raise ValueError('Parâmetros inválidos')
        self.confirmacao=quadros_confirmacao
        self.saida=quadros_saida
        self.intervalo=intervalo_convite
        self.relogio=relogio
        self.sessoes: dict[str, EstadoPresenca] = {}

    def observar(self, sessao: str, quantidade_pessoas: int, camera_autorizada: bool, interacao_espontanea: bool=False) -> list[dict]:
        if not camera_autorizada:
            self.sessoes.pop(sessao, None)
            return []
        if quantidade_pessoas < 0:
            raise ValueError('Quantidade de pessoas inválida')
        estado=self.sessoes.setdefault(sessao, EstadoPresenca())
        eventos=[]
        if quantidade_pessoas:
            estado.vistos+=1
            estado.ausentes=0
            if not estado.presente and estado.vistos >= self.confirmacao:
                estado.presente=True
                eventos.append({'tipo':'presenca_detectada','quantidade':quantidade_pessoas})
                agora=self.relogio()
                if interacao_espontanea and agora-estado.ultimo_convite >= self.intervalo:
                    estado.ultimo_convite=agora
                    eventos.append({'tipo':'convite_conversa','texto':'Olá! Posso conversar com você?'})
        else:
            estado.ausentes+=1
            estado.vistos=0
            if estado.presente and estado.ausentes >= self.saida:
                estado.presente=False
                eventos.append({'tipo':'ambiente_sem_pessoas'})
        return eventos

    def encerrar(self, sessao: str):
        self.sessoes.pop(sessao, None)
