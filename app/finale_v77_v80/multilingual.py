"""V79 multilingual routing: honest capabilities, explicit locale, provider injection.
No claims of universal language detection or speech support without providers.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable

LANGUAGES = {"pt":"Português", "en":"English", "es":"Español", "fr":"Français", "de":"Deutsch", "it":"Italiano", "ar":"العربية", "ja":"日本語", "zh":"中文", "ko":"한국어", "ru":"Русский", "hi":"हिन्दी"}
ALIASES = {"portugues":"pt", "português":"pt", "english":"en", "ingles":"en", "inglês":"en", "espanol":"es", "español":"es", "espanhol":"es", "french":"fr", "frances":"fr", "francês":"fr", "german":"de", "alemao":"de", "alemão":"de", "italiano":"it", "arabic":"ar", "arabe":"ar", "árabe":"ar", "japanese":"ja", "japones":"ja", "japonês":"ja", "chinese":"zh", "chines":"zh", "chinês":"zh", "korean":"ko", "coreano":"ko", "russian":"ru", "russo":"ru", "hindi":"hi"}

def normalize_language(value: str) -> str:
    if not isinstance(value,str): raise ValueError("Idioma inválido")
    s=value.strip().lower().replace("_","-")
    if s=="auto": return "auto"
    s=ALIASES.get(s,s)
    base=s.split("-")[0]
    if base not in LANGUAGES: raise ValueError("Idioma não suportado pelo catálogo V79: "+value)
    return base

def detect_script(text: str) -> str | None:
    """Only high-confidence script hints; Latin-script language requires an external detector."""
    for pattern,code in [(r"[\u3040-\u30ff]","ja"),(r"[\uac00-\ud7af]","ko"),(r"[\u0600-\u06ff]","ar"),(r"[\u0400-\u04ff]","ru"),(r"[\u0900-\u097f]","hi"),(r"[\u4e00-\u9fff]","zh")]:
        if re.search(pattern,text): return code
    return None

@dataclass(frozen=True)
class LanguagePlan:
    requested_language: str
    detected_language: str | None
    response_language: str | None
    detection_method: str
    needs_provider: bool
    instruction: str

class MultilingualV79:
    def __init__(self, detector: Callable[[str],str|None]|None=None, translator: Callable[[str,str,str],str]|None=None):
        self.detector=detector
        self.translator=translator

    def prepare(self,text:str,preferred_language:str="auto",fallback_language:str="pt") -> LanguagePlan:
        if not isinstance(text,str) or not text.strip(): raise ValueError("Texto vazio")
        preferred=normalize_language(preferred_language)
        fallback=normalize_language(fallback_language)
        if fallback=="auto": raise ValueError("Idioma de fallback precisa ser explícito")
        detected=detect_script(text)
        method="script_hint" if detected else "unavailable"
        if self.detector:
            result=self.detector(text)
            if result:
                detected=normalize_language(result)
                if detected=="auto": detected=None
                method="external_detector" if detected else method
        target=preferred if preferred!="auto" else (detected or fallback)
        return LanguagePlan(preferred,detected,target,method,not bool(self.detector),
          f"Responda no idioma {LANGUAGES[target]} ({target}), preservando o significado e o contexto. "
          "Não afirme ter ouvido, traduzido ou detectado automaticamente o idioma se isso não ocorreu.")

    def translate(self,text:str,source:str,target:str)->dict:
        src=normalize_language(source); dst=normalize_language(target)
        if src=="auto" or dst=="auto": raise ValueError("Tradução exige idiomas explícitos")
        if src==dst: return {"text":text,"translated":False,"provider_used":False}
        if self.translator is None: return {"text":None,"translated":False,"provider_used":False,"error":"translation_provider_not_configured"}
        translated=self.translator(text,src,dst)
        if not isinstance(translated,str) or not translated.strip(): raise RuntimeError("Provedor retornou tradução vazia")
        return {"text":translated,"translated":True,"provider_used":True,"source_language":src,"target_language":dst}
