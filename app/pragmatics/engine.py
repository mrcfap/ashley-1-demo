"""Interpretação pragmática efêmera; não classifica emoções nem armazena texto."""
import re
import unicodedata


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto or '').casefold())
    return ''.join(c for c in texto if not unicodedata.combining(c))[:5000]


class PragmaticaHumana:
    @staticmethod
    def analisar(texto, historico=None):
        t = normalizar(texto)
        patterns = {
            'humor_ou_brincadeira': r'\b(k{2,}|rsrs+|haha+|hehe+|brincadeira|to zoando|estou zoando|so uma metafora)\b',
            'linguagem_nao_literal': r'\b(metafora|metaforicamente|modo de dizer|figura de linguagem|forca de expressao)\b',
            'possivel_ironia': r'\b(ironiz\w*|sarcasmo|ironia|ironico)\b',
            'comentario_sem_pedido_de_aula': r'\b(so comentando|foi um comentario|nao precisa explicar|ja sei disso|eu sei disso)\b',
            'reparo_de_entendimento': r'\b(nao foi isso|voce entendeu errado|nao era isso|quis dizer|na verdade eu quis|voce levou ao pe da letra)\b',
            'incerteza_expressa': r'\b(acho que|talvez|pode ser|quem sabe)\b',
            'pedido_de_escuta': r'\b(so quero desabafar|so me escuta|so queria conversar|nao quero conselho)\b',
            'pedido_de_objetividade': r'\b(vai direto ao ponto|sem enrolacao|resposta curta|seja objetivo)\b',
            'pedido_de_analise': r'\b(analise tecnicamente|quero uma analise|explique em detalhes|quero os dados)\b',
            'pedido_de_confirmacao': r'\b(antes de fazer, confirme|pergunte antes de agir|nao faca sem perguntar)\b',
        }
        pistas = [nome for nome, pattern in patterns.items() if re.search(pattern, t)]
        return {'pistas': pistas, 'confianca': 'baixa' if pistas else 'indeterminada'}

    @staticmethod
    def instrucoes(analise):
        pistas = set(analise.get('pistas', []))
        if not pistas:
            return ''
        regras = [
            'PRAGMÁTICA HUMANA — contrato de conversa contextual (pistas incertas):',
            'Interprete a intenção à luz do contexto; não tome brincadeiras automaticamente como pedidos técnicos.',
            'Não infira sentimentos internos com certeza; demonstre atenção sem alegar emoções vividas ou consciência.',
            'Não substitua pedidos explícitos, fatos, políticas de segurança ou consentimento por estas pistas.',
            'Se o contexto for ambíguo e a consequência importante, pergunte de forma breve antes de agir.',
        ]
        if pistas & {'humor_ou_brincadeira', 'linguagem_nao_literal', 'possivel_ironia'}:
            regras.append('Pode acompanhar humor e metáforas com leveza, sem corrigir uma brincadeira como se fosse erro factual.')
        if 'comentario_sem_pedido_de_aula' in pistas:
            regras.append('Não transforme um comentário casual em explicação extensa ou sermão.')
        if 'reparo_de_entendimento' in pistas:
            regras.append('Reconheça o ajuste de sentido sem defensividade, reformule o entendimento e não repita a correção.')
        if 'incerteza_expressa' in pistas:
            regras.append('Não transforme hipótese ou possibilidade em certeza.')
        if 'pedido_de_escuta' in pistas:
            regras.append('Priorize escuta acolhedora e perguntas discretas; não dê conselhos não solicitados.')
        if 'pedido_de_objetividade' in pistas:
            regras.append('Seja breve e objetivo, preservando informações essenciais.')
        if 'pedido_de_analise' in pistas:
            regras.append('Forneça análise fundamentada e detalhe limitações e incertezas.')
        if 'pedido_de_confirmacao' in pistas:
            regras.append('Peça confirmação antes de ações externas ou alterações persistentes.')
        return '\n'.join(regras)
