"""Inventário conservador de capacidades: presença não equivale a funcionamento."""
from pathlib import Path
from importlib.util import find_spec
import os

ROOT = Path(__file__).resolve().parents[2]
CAPACIDADES = {
 'conversa': ('app.services.gemini_service', '/chat', 'Conversa com modelo de linguagem'),
 'memoria_longa': ('app.memory.memoria_longa', '/memoria/buscar/{user_id}', 'Memória de longo prazo'),
 'memoria_relacional': ('app.relationship.memoria_relacional', None, 'Memória relacional'),
 'visao': ('app.vision.analisador_multimodal', '/vision/capture', 'Análise visual'),
 'arquivos': ('app.services.gemini_service', '/arquivo/analisar', 'Análise de arquivos'),
 'imagens': ('app.services.gemini_service', '/imagem/gerar', 'Geração de imagens'),
 'videos': ('app.services.gemini_service', '/video/gerar', 'Geração de vídeos'),
 'voz_neural': ('app.services.gemini_service', '/tts', 'Síntese de voz neural'),
 'planejamento': ('app.agents.planner', None, 'Planejamento'),
 'critica': ('app.agents.critic', None, 'Crítica e validação'),
 'casos': ('app.cases.motor_casos', None, 'Acompanhamento de casos'),
 'v22': ('app.tasks.motor_execucao_v22', None, 'Execução autônoma V22'),
 'autoevolucao': ('app.evolution.motor_autoevolucao', None, 'Autoevolução supervisionada'),
 'v23_v26': ('app.integracao_v26', '/chat', 'Motores V23-V26: integração multimodal e autoevolução supervisionada'),
 'v27_v30': ('app.future_engines', '/motores/v27-v30/status', 'Motores V27-V30: iniciativa, música MIDI, inovação e cenários condicionais'),
 'v31_maci': ('app.cognitive_v31_v35', '/motores/v31-v35/status', 'V31 MACI: classificação heurística de intenção'),
 'v32_meca': ('app.cognitive_v31_v35', '/motores/v31-v35/status', 'V32 MECA: contraponto crítico contextual'),
 'v33_memo': ('app.cognitive_v31_v35', '/motores/v31-v35/status', 'V33 MEMO: política conservadora de retenção de memória'),
 'v34_qdea': ('app.cognitive_v31_v35', '/motores/v31-v35/status', 'V34 QDEA: seleção de modo operacional'),
 'v36_transit': ('app.advanced_v36_v38', '/motores/v36-v38/status', 'V36 TRANSIT: cenários condicionais não preditivos'),
 'v37_genesis': ('app.advanced_v36_v38', '/motores/v36-v38/status', 'V37 GENESIS: inspeção e propostas sem automodificação executada'),
 'v38_sentinel': ('app.advanced_v36_v38', '/motores/v36-v38/status', 'V38 SENTINEL: registro de risco e aprovação humana'),
 'v39_sentir': ('app.relational_v39_v42', '/motores/v39-v42/status', 'V39 SENTIR: sensibilidade contextual sem inferência emocional definitiva'),
 'v40_presenca': ('app.relational_v39_v42', '/motores/v39-v42/status', 'V40 PRESENÇA: expressão e ritmo do avatar, animação aproximada'),
 'v41_continuum': ('app.relational_v39_v42', '/motores/v39-v42/status', 'V41 CONTINUUM: retomada contextual baseada em histórico disponível'),
 'v43_ecos': ('app.ecos_v43', '/motores/v43/status', 'V43 ECOS: coordenação de orientações com prioridade para segurança e consentimento'),
 'v42_horizonte': ('app.relational_v39_v42', '/motores/v39-v42/status', 'V42 HORIZONTE: iniciativa consentida e limites relacionais'),
 'v35_evidencias': ('app.cognitive_v31_v35', '/motores/v31-v35/status', 'V35: evidências e governança de ações'),
}

def inventario(rotas=None, testes=None):
    testes = testes or {}
    rotas=set(rotas or [])
    saida={}
    for chave,(modulo,rota,descricao) in CAPACIDADES.items():
        try: instalado=find_spec(modulo) is not None
        except (ImportError,ModuleNotFoundError,AttributeError): instalado=False
        exposto=(rota in rotas) if rota else None
        configuracao='chave_configurada' if os.getenv('GEMINI_API_KEY') else 'chave_ausente'
        # Sem execução real, não inferir disponibilidade só porque existe arquivo ou endpoint.
        estado='nao_encontrado' if not instalado else ('integrado_sem_teste' if exposto else 'instalado_sem_verificacao')
        evidencia = testes.get(chave)
        teste_bem_sucedido = bool(evidencia and evidencia.get('resultado') == 'sucesso')
        if instalado and exposto is not False and evidencia:
            estado = 'teste_real_bem_sucedido' if teste_bem_sucedido else 'teste_real_sem_sucesso'
        saida[chave]={'descricao':descricao,'estado':estado,'modulo_instalado':instalado,'rota_exposta':exposto,'requer_teste_real':estado != 'teste_real_bem_sucedido','ultimo_teste':evidencia}
        if chave in ('conversa','arquivos','imagens','videos','voz_neural'):
            saida[chave]['provedor']=configuracao
    return saida

def contexto_capacidades(inventario_atual):
    linhas=['INVENTÁRIO DO SOFTWARE ASHLEY 1.0 (gerado pelo backend, não pela imaginação do modelo):']
    for item in inventario_atual.values():
        linhas.append('- '+item['descricao']+': '+item['estado'] + ((' (evidência: '+item['ultimo_teste']['detalhe']+')') if item.get('ultimo_teste') else ''))
    linhas.append('IMPORTANTE: instalado ou rota exposta NÃO significa operacional. Não diga que a interface não possui voz, visão, imagens ou vídeos se constarem no inventário. Diga que há integração prevista/presente, mas funcionamento requer teste real. Nunca afirme execução ou disponibilidade sem evidência. Diferencie claramente recurso da interface, recurso do backend e recurso executado nesta conversa. Não apresente estados internos como fatos confirmados sem teste. Ao responder oralmente, use português natural, sem Markdown, asteriscos, hashtags ou listas numeradas extensas.')
    return '\n'.join(linhas)
