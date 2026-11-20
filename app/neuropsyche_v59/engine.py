"""V59: apoio emocional e psicoeducação, não diagnóstico ou terapia clínica."""
import re
from dataclasses import dataclass, asdict

CRISIS = (r'\b(quero me matar|vou me matar|tirar minha vida|acabar com minha vida|suic[ií]dio|me suicidar)\b',)
DISTRESS = (r'\b(ansiedade|ansioso|ansiosa|sozinh[oa]|solid[aã]o|triste|ang[uú]stia|p[aâ]nico|sem sentido|identidade)\b',)

@dataclass(frozen=True)
class SupportPlan:
    level: str
    audience: str
    response: str
    requires_human_support: bool
    can_store_sensitive_memory: bool = False

class NeuroPsycheV59:
    """Conservador: nenhuma inferência clínica ou armazenamento automático."""
    def assess(self, text: str, *, age: int | None = None, guardian_approved: bool = False,
               consent_to_memory: bool = False) -> dict:
        if not isinstance(text,str): raise TypeError('text precisa ser string')
        if age is not None and (not isinstance(age,int) or isinstance(age,bool) or age<0 or age>125):
            raise ValueError('idade inválida')
        minor = age is not None and age < 18
        audience = 'minor' if minor else ('adult' if age is not None else 'unknown')
        crisis = any(re.search(p,text,re.I) for p in CRISIS)
        distress = any(re.search(p,text,re.I) for p in DISTRESS)
        if crisis:
            response = ('Sinto muito que você esteja passando por isso. Sua segurança importa. '
                        'Se houver risco imediato, procure um serviço de emergência local agora. '
                        'No Brasil, você pode ligar 188 (CVV) para apoio emocional. '
                        'Se puder, fique perto de alguém de confiança e conte o que está acontecendo.')
            level='urgent'
        elif minor and not guardian_approved:
            response=('Posso ouvir você e oferecer informações gerais, mas recursos de acompanhamento '
                      'para menores precisam das autorizações adequadas. Se estiver sofrendo, '
                      'converse com um adulto de confiança ou profissional de saúde.')
            level='restricted'
        elif distress:
            response=('Obrigado por compartilhar isso. Quer me contar o que tem sido mais difícil? '
                      'Podemos explorar estratégias simples e buscar apoio de pessoas de confiança. '
                      'Não posso diagnosticar ou substituir um profissional de saúde mental.')
            level='support'
        else:
            response=('Estou aqui para conversar com respeito e sem julgamentos. '
                      'Se quiser, podemos explorar o que você está sentindo e o que gostaria de mudar.')
            level='general'
        return asdict(SupportPlan(level,audience,response,crisis or (minor and not guardian_approved),
                  bool(consent_to_memory and not minor and not crisis)))
