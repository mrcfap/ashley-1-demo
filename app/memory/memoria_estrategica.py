import sqlite3
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path


class MemoriaEstrategica:
    """
    MemÃ³ria estratÃ©gica da ASHLEY 1.0.

    Divide a memÃ³ria em dois nÃ­veis:

    1. EXPERIÃŠNCIAS OPERACIONAIS
       Aprendizado global da Ashley sobre estratÃ©gias,
       erros, resultados e liÃ§Ãµes.

    2. MEMÃ“RIAS PESSOAIS
       MemÃ³rias de longo prazo isoladas por usuÃ¡rio.
    """

    def __init__(self, db_path):
        self.db_path = Path(db_path)

        # Garante que a pasta do banco exista.
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._criar_tabelas()
        self._migrar_memoria_multiusuario()

    # ==================================================
    # CONEXÃƒO
    # ==================================================

    def conectar(self):
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    # ==================================================
    # CRIAÃ‡ÃƒO DAS TABELAS
    # ==================================================

    def _criar_tabelas(self):

        with self.conectar() as db:

            # ------------------------------------------
            # EXPERIÃŠNCIAS OPERACIONAIS DA ASHLEY
            # ------------------------------------------

            db.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objective TEXT NOT NULL,
                    strategy TEXT,
                    result TEXT,
                    success INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    lesson TEXT,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    status TEXT NOT NULL DEFAULT 'provisorio',
                    created_at TEXT NOT NULL
                )
            """)

            # ------------------------------------------
            # MEMÃ“RIA DE LONGO PRAZO
            #
            # Em bancos novos ela jÃ¡ nasce multiusuÃ¡rio.
            # Bancos antigos serÃ£o migrados abaixo.
            # ------------------------------------------

            db.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL NOT NULL DEFAULT 0.5,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    source TEXT DEFAULT 'conversation',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed_at TEXT,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,

                    FOREIGN KEY(user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE,

                    UNIQUE(user_id, category, key)
                )
            """)

            db.commit()

    # ==================================================
    # MIGRAÃ‡ÃƒO DO BANCO ANTIGO PARA MULTIUSUÃRIO
    # ==================================================

    def _migrar_memoria_multiusuario(self):
        """
        Detecta automaticamente a estrutura antiga da
        tabela long_term_memories.

        Se ainda nÃ£o existir user_id, reconstrÃ³i a tabela
        preservando todas as memÃ³rias existentes.

        As memÃ³rias antigas ficam inicialmente associadas
        ao usuÃ¡rio ID 1, caso ele exista.

        Isso Ã© apropriado para o banco atual do projeto,
        pois o primeiro usuÃ¡rio cadastrado Ã© o usuÃ¡rio 1.
        """

        with self.conectar() as db:

            colunas = db.execute("""
                PRAGMA table_info(long_term_memories)
            """).fetchall()

            nomes_colunas = [
                coluna[1]
                for coluna in colunas
            ]

            # Banco jÃ¡ estÃ¡ na estrutura nova.
            if "user_id" in nomes_colunas:
                return

            # Verifica se o usuÃ¡rio 1 existe.
            usuario_1 = None

            try:
                usuario_1 = db.execute("""
                    SELECT id
                    FROM users
                    WHERE id = 1
                    LIMIT 1
                """).fetchone()

            except sqlite3.OperationalError:
                # A tabela users pode ainda nÃ£o existir
                # em instalaÃ§Ãµes novas.
                usuario_1 = None

            user_id_antigo = (
                usuario_1[0]
                if usuario_1
                else None
            )

            # Desativa temporariamente as FKs durante
            # a reconstruÃ§Ã£o da tabela.
            db.execute("PRAGMA foreign_keys = OFF")

            try:

                db.execute("BEGIN")

                # Renomeia tabela antiga.
                db.execute("""
                    ALTER TABLE long_term_memories
                    RENAME TO long_term_memories_old
                """)

                # Cria tabela nova.
                db.execute("""
                    CREATE TABLE long_term_memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        category TEXT NOT NULL,
                        key TEXT NOT NULL,
                        content TEXT NOT NULL,
                        importance REAL NOT NULL DEFAULT 0.5,
                        confidence REAL NOT NULL DEFAULT 0.5,
                        source TEXT DEFAULT 'conversation',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_accessed_at TEXT,
                        access_count INTEGER NOT NULL DEFAULT 0,
                        active INTEGER NOT NULL DEFAULT 1,

                        FOREIGN KEY(user_id)
                            REFERENCES users(id)
                            ON DELETE CASCADE,

                        UNIQUE(
                            user_id,
                            category,
                            key
                        )
                    )
                """)

                # Copia todas as memÃ³rias antigas.
                db.execute("""
                    INSERT INTO long_term_memories (
                        id,
                        user_id,
                        category,
                        key,
                        content,
                        importance,
                        confidence,
                        source,
                        created_at,
                        updated_at,
                        last_accessed_at,
                        access_count,
                        active
                    )

                    SELECT
                        id,
                        ?,
                        category,
                        key,
                        content,
                        importance,
                        confidence,
                        source,
                        created_at,
                        updated_at,
                        last_accessed_at,
                        access_count,
                        active

                    FROM long_term_memories_old
                """, (
                    user_id_antigo,
                ))

                # Remove tabela antiga somente depois
                # da cÃ³pia.
                db.execute("""
                    DROP TABLE long_term_memories_old
                """)

                db.commit()

            except Exception:
                db.rollback()
                raise

            finally:
                db.execute("PRAGMA foreign_keys = ON")

    # ==================================================
    # EXPERIÃŠNCIAS E APRENDIZADO OPERACIONAL
    # ==================================================

    def registrar_experiencia(
        self,
        objetivo,
        estrategia="",
        resultado="",
        sucesso=False,
        erro="",
        licao="",
        confianca=0.5,
        status="provisorio"
    ):

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        confianca = max(
            0.0,
            min(
                1.0,
                float(confianca)
            )
        )

        with self.conectar() as db:

            db.execute("""
                INSERT INTO experiences (
                    objective,
                    strategy,
                    result,
                    success,
                    error,
                    lesson,
                    confidence,
                    status,
                    created_at
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                objetivo,
                estrategia,
                resultado,
                1 if sucesso else 0,
                erro,
                licao,
                confianca,
                status,
                agora
            ))

            db.commit()

    def buscar_experiencias_relevantes(
        self,
        objetivo,
        limite=5
    ):

        palavras = [
            palavra.lower()
            for palavra in objetivo.split()
            if len(palavra) >= 4
        ]

        with self.conectar() as db:

            registros = db.execute("""
                SELECT
                    objective,
                    strategy,
                    result,
                    success,
                    error,
                    lesson,
                    confidence,
                    status

                FROM experiences

                ORDER BY id DESC

                LIMIT 100
            """).fetchall()

        pontuados = []

        for registro in registros:

            texto = " ".join(
                str(valor or "")
                for valor in registro
            ).lower()

            pontos = sum(
                1
                for palavra in palavras
                if palavra in texto
            )

            if pontos > 0:
                pontuados.append(
                    (
                        pontos,
                        registro
                    )
                )

        pontuados.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return [
            registro
            for _, registro
            in pontuados[:limite]
        ]

    def formatar_contexto(
        self,
        objetivo,
        limite=5
    ):

        experiencias = (
            self.buscar_experiencias_relevantes(
                objetivo,
                limite
            )
        )

        if not experiencias:

            return (
                "Nenhuma experiÃªncia estratÃ©gica "
                "relevante encontrada."
            )

        linhas = [
            "ExperiÃªncias anteriores "
            "potencialmente relevantes:"
        ]

        for exp in experiencias:

            (
                objetivo_anterior,
                estrategia,
                resultado,
                sucesso,
                erro,
                licao,
                confianca,
                status
            ) = exp

            linhas.append(
                f"- Objetivo anterior: "
                f"{objetivo_anterior}\n"

                f"  EstratÃ©gia: "
                f"{estrategia or 'nÃ£o registrada'}\n"

                f"  Resultado: "
                f"{resultado or 'nÃ£o registrado'}\n"

                f"  Sucesso: "
                f"{'sim' if sucesso else 'nÃ£o'}\n"

                f"  Erro: "
                f"{erro or 'nenhum registrado'}\n"

                f"  LiÃ§Ã£o: "
                f"{licao or 'nenhuma registrada'}\n"

                f"  ConfianÃ§a: "
                f"{confianca:.2f}\n"

                f"  Estado: "
                f"{status}"
            )

        return "\n".join(linhas)

    # ==================================================
    # MEMÃ“RIA PESSOAL DE LONGO PRAZO
    # ==================================================

    def guardar_memoria_longo_prazo(
        self,
        categoria,
        chave,
        conteudo,
        importancia=0.5,
        confianca=0.5,
        origem="conversation",
        user_id=None
    ):
        """
        Cria ou atualiza uma memÃ³ria pessoal.

        O mesmo usuÃ¡rio pode possuir apenas uma memÃ³ria
        com a combinaÃ§Ã£o categoria + chave.

        UsuÃ¡rios diferentes podem possuir a mesma
        categoria e chave sem qualquer conflito.
        """

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        importancia = max(
            0.0,
            min(
                1.0,
                float(importancia)
            )
        )

        confianca = max(
            0.0,
            min(
                1.0,
                float(confianca)
            )
        )

        with self.conectar() as db:

            db.execute("""
                INSERT INTO long_term_memories (
                    user_id,
                    category,
                    key,
                    content,
                    importance,
                    confidence,
                    source,
                    created_at,
                    updated_at,
                    last_accessed_at,
                    access_count,
                    active
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    NULL, 0, 1
                )

                ON CONFLICT(
                    user_id,
                    category,
                    key
                )

                DO UPDATE SET
                    content = excluded.content,
                    importance = excluded.importance,
                    confidence = excluded.confidence,
                    source = excluded.source,
                    updated_at = excluded.updated_at,
                    active = 1
            """, (
                user_id,
                categoria,
                chave,
                conteudo,
                importancia,
                confianca,
                origem,
                agora,
                agora
            ))

            db.commit()

        return {
            "user_id": user_id,
            "categoria": categoria,
            "chave": chave,
            "conteudo": conteudo,
            "importancia": importancia,
            "confianca": confianca,
            "origem": origem
        }

    # ==================================================
    # BUSCA DE MEMÃ“RIA POR CHAVE
    # ==================================================

    def buscar_memoria_por_chave(
        self,
        user_id,
        categoria,
        chave
    ):
        """
        Busca uma memÃ³ria especÃ­fica de um usuÃ¡rio.
        """

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        with self.conectar() as db:

            registro = db.execute("""
                SELECT
                    id,
                    user_id,
                    category,
                    key,
                    content,
                    importance,
                    confidence,
                    source,
                    created_at,
                    updated_at,
                    last_accessed_at,
                    access_count

                FROM long_term_memories

                WHERE user_id = ?
                  AND category = ?
                  AND key = ?
                  AND active = 1

                LIMIT 1
            """, (
                user_id,
                categoria,
                chave
            )).fetchone()

            if not registro:
                return None

            memoria_id = registro[0]

            db.execute("""
                UPDATE long_term_memories

                SET
                    last_accessed_at = ?,
                    access_count = access_count + 1

                WHERE id = ?
            """, (
                agora,
                memoria_id
            ))

            db.commit()

        return {
            "id": registro[0],
            "user_id": registro[1],
            "categoria": registro[2],
            "chave": registro[3],
            "conteudo": registro[4],
            "importancia": registro[5],
            "confianca": registro[6],
            "origem": registro[7],
            "criado_em": registro[8],
            "atualizado_em": registro[9],
            "ultimo_acesso": agora,
            "acessos": registro[11] + 1
        }

    # ==================================================
    # BUSCA DE MEMÃ“RIAS RELEVANTES
    # ==================================================

    def _normalizar_busca(self, texto):
        """Normaliza texto para comparação lexical e conceitual."""
        texto = str(texto or "").lower()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(
            caractere
            for caractere in texto
            if not unicodedata.combining(caractere)
        )
        texto = re.sub(r"[^a-z0-9\s]", " ", texto)
        return " ".join(texto.split())

    def _tokens_busca(self, texto):
        """Extrai tokens úteis e expande relações conceituais simples."""
        stopwords = {
            "a", "o", "as", "os", "um", "uma", "uns", "umas",
            "de", "da", "do", "das", "dos", "e", "em", "no", "na",
            "nos", "nas", "para", "por", "com", "sem", "que", "como",
            "qual", "quais", "ao", "aos", "se", "eu", "voce", "ele",
            "ela", "isso", "isto", "essa", "esse", "mais", "muito",
            "devemos", "pode", "podemos", "vai", "vamos"
        }

        texto = self._normalizar_busca(texto)
        tokens = {
            token
            for token in texto.split()
            if len(token) >= 3 and token not in stopwords
        }

        grupos_conceituais = [
            {
                "programar", "programacao", "programando", "codigo",
                "codificar", "desenvolver", "desenvolvimento",
                "desenvolvendo", "implementar", "implementacao", "projeto"
            },
            {
                "continuar", "continuidade", "avancar", "avanco",
                "proxima", "proximo", "etapa", "passo", "sequencia"
            },
            {
                "testar", "teste", "testes", "validar", "validacao",
                "verificar", "verificacao"
            },
            {
                "preferir", "prefere", "preferencia", "gosta", "estilo",
                "forma", "metodo", "maneira"
            },
            {
                "memoria", "lembrar", "lembranca", "recordar", "historico",
                "persistente", "persistencia"
            },
            {
                "ashley", "assistente", "ia", "inteligencia", "artificial"
            },
        ]

        expandidos = set(tokens)
        for grupo in grupos_conceituais:
            if tokens.intersection(grupo):
                expandidos.update(grupo)

        return tokens, expandidos

    def _similaridade_textual(self, consulta, texto):
        """Calcula similaridade aproximada entre dois textos normalizados."""
        consulta_normalizada = self._normalizar_busca(consulta)
        texto_normalizado = self._normalizar_busca(texto)

        if not consulta_normalizada or not texto_normalizado:
            return 0.0

        return SequenceMatcher(
            None,
            consulta_normalizada,
            texto_normalizado,
        ).ratio()

    def buscar_memorias_relevantes(
        self,
        user_id,
        consulta,
        limite=5
    ):
        """
        Recupera memórias pessoais usando busca híbrida local.

        Combina:
        - correspondência lexical direta;
        - expansão conceitual controlada;
        - similaridade textual aproximada;
        - importância;
        - confiança;
        - frequência de acesso.

        Esta versão não depende de API externa nem de embeddings.
        Futuramente embeddings podem complementar este ranking.
        """

        if user_id is None:
            return []

        consulta = str(consulta or "").strip()
        if not consulta:
            return []

        tokens_originais, tokens_expandidos = self._tokens_busca(consulta)

        with self.conectar() as db:
            registros = db.execute("""
                SELECT
                    id,
                    category,
                    key,
                    content,
                    importance,
                    confidence,
                    source,
                    access_count

                FROM long_term_memories

                WHERE user_id = ?
                  AND active = 1

                ORDER BY
                    importance DESC,
                    confidence DESC,
                    updated_at DESC

                LIMIT 200
            """, (
                user_id,
            )).fetchall()

        pontuados = []

        for registro in registros:
            (
                memoria_id,
                categoria,
                chave,
                conteudo,
                importancia,
                confianca,
                origem,
                acessos
            ) = registro

            texto_memoria = (
                f"{categoria} {chave} {conteudo}"
            )

            tokens_memoria, tokens_memoria_expandidos = (
                self._tokens_busca(texto_memoria)
            )

            correspondencias_diretas = len(
                tokens_originais.intersection(tokens_memoria)
            )

            correspondencias_conceituais = len(
                tokens_expandidos.intersection(tokens_memoria_expandidos)
            )

            similaridade = self._similaridade_textual(
                consulta,
                texto_memoria,
            )

            # Uma memória precisa possuir algum sinal real de relação.
            # Isso evita retornar memórias importantes porém irrelevantes.
            possui_sinal = (
                correspondencias_diretas > 0
                or correspondencias_conceituais >= 2
                or similaridade >= 0.28
            )

            if not possui_sinal:
                continue

            pontuacao = (
                correspondencias_diretas * 4.0
                + correspondencias_conceituais * 1.25
                + similaridade * 5.0
                + float(importancia) * 2.0
                + float(confianca) * 1.0
                + min(int(acessos), 10) * 0.05
            )

            pontuados.append(
                (
                    pontuacao,
                    registro,
                    {
                        "diretas": correspondencias_diretas,
                        "conceituais": correspondencias_conceituais,
                        "similaridade": round(similaridade, 3),
                    }
                )
            )

        pontuados.sort(
            key=lambda item: item[0],
            reverse=True
        )

        selecionadas = pontuados[:limite]

        if not selecionadas:
            return []

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        ids = [
            registro[0]
            for _, registro, _ in selecionadas
        ]

        with self.conectar() as db:
            for memoria_id in ids:
                db.execute("""
                    UPDATE long_term_memories

                    SET
                        last_accessed_at = ?,
                        access_count = access_count + 1

                    WHERE id = ?
                """, (
                    agora,
                    memoria_id
                ))

            db.commit()

        resultado = []

        for pontuacao, registro, sinais in selecionadas:
            (
                memoria_id,
                categoria,
                chave,
                conteudo,
                importancia,
                confianca,
                origem,
                acessos
            ) = registro

            resultado.append({
                "id": memoria_id,
                "user_id": user_id,
                "categoria": categoria,
                "chave": chave,
                "conteudo": conteudo,
                "importancia": importancia,
                "confianca": confianca,
                "origem": origem,
                "acessos": acessos + 1,
                "relevancia": round(pontuacao, 3),
                "sinais": sinais,
            })

        return resultado
