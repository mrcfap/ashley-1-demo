import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MemoriaEstrategica:
    """
    Memória estratégica da ASHLEY 1.0.

    Divide a memória em dois níveis:

    1. EXPERIÊNCIAS OPERACIONAIS
       Aprendizado global da Ashley sobre estratégias,
       erros, resultados e lições.

    2. MEMÓRIAS PESSOAIS
       Memórias de longo prazo isoladas por usuário.
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
    # CONEXÃO
    # ==================================================

    def conectar(self):
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    # ==================================================
    # CRIAÇÃO DAS TABELAS
    # ==================================================

    def _criar_tabelas(self):

        with self.conectar() as db:

            # ------------------------------------------
            # EXPERIÊNCIAS OPERACIONAIS DA ASHLEY
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
            # MEMÓRIA DE LONGO PRAZO
            #
            # Em bancos novos ela já nasce multiusuário.
            # Bancos antigos serão migrados abaixo.
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
    # MIGRAÇÃO DO BANCO ANTIGO PARA MULTIUSUÁRIO
    # ==================================================

    def _migrar_memoria_multiusuario(self):
        """
        Detecta automaticamente a estrutura antiga da
        tabela long_term_memories.

        Se ainda não existir user_id, reconstrói a tabela
        preservando todas as memórias existentes.

        As memórias antigas ficam inicialmente associadas
        ao usuário ID 1, caso ele exista.

        Isso é apropriado para o banco atual do projeto,
        pois o primeiro usuário cadastrado é o usuário 1.
        """

        with self.conectar() as db:

            colunas = db.execute("""
                PRAGMA table_info(long_term_memories)
            """).fetchall()

            nomes_colunas = [
                coluna[1]
                for coluna in colunas
            ]

            # Banco já está na estrutura nova.
            if "user_id" in nomes_colunas:
                return

            # Verifica se o usuário 1 existe.
            usuario_1 = None

            try:
                usuario_1 = db.execute("""
                    SELECT id
                    FROM users
                    WHERE id = 1
                    LIMIT 1
                """).fetchone()

            except sqlite3.OperationalError:
                # A tabela users pode ainda não existir
                # em instalações novas.
                usuario_1 = None

            user_id_antigo = (
                usuario_1[0]
                if usuario_1
                else None
            )

            # Desativa temporariamente as FKs durante
            # a reconstrução da tabela.
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

                # Copia todas as memórias antigas.
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
                # da cópia.
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
    # EXPERIÊNCIAS E APRENDIZADO OPERACIONAL
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
                "Nenhuma experiência estratégica "
                "relevante encontrada."
            )

        linhas = [
            "Experiências anteriores "
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

                f"  Estratégia: "
                f"{estrategia or 'não registrada'}\n"

                f"  Resultado: "
                f"{resultado or 'não registrado'}\n"

                f"  Sucesso: "
                f"{'sim' if sucesso else 'não'}\n"

                f"  Erro: "
                f"{erro or 'nenhum registrado'}\n"

                f"  Lição: "
                f"{licao or 'nenhuma registrada'}\n"

                f"  Confiança: "
                f"{confianca:.2f}\n"

                f"  Estado: "
                f"{status}"
            )

        return "\n".join(linhas)

    # ==================================================
    # MEMÓRIA PESSOAL DE LONGO PRAZO
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
        Cria ou atualiza uma memória pessoal.

        O mesmo usuário pode possuir apenas uma memória
        com a combinação categoria + chave.

        Usuários diferentes podem possuir a mesma
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
    # BUSCA DE MEMÓRIA POR CHAVE
    # ==================================================

    def buscar_memoria_por_chave(
        self,
        user_id,
        categoria,
        chave
    ):
        """
        Busca uma memória específica de um usuário.
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
    # BUSCA DE MEMÓRIAS RELEVANTES
    # ==================================================

    def buscar_memorias_relevantes(
        self,
        user_id,
        consulta,
        limite=5
    ):
        """
        Recuperação inicial de memórias relevantes.

        Nesta fase utiliza palavras da consulta,
        importância, confiança e frequência de acesso.

        Posteriormente este mecanismo poderá receber
        embeddings e busca semântica.
        """

        palavras = [
            palavra.lower()
            for palavra in consulta.split()
            if len(palavra) >= 3
        ]

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

            texto = (
                f"{categoria} "
                f"{chave} "
                f"{conteudo}"
            ).lower()

            correspondencias = sum(
                1
                for palavra in palavras
                if palavra in texto
            )

            if correspondencias == 0:
                continue

            # Pontuação híbrida simples.
            pontuacao = (
                correspondencias * 3
                + importancia * 2
                + confianca
                + min(acessos, 10) * 0.05
            )

            pontuados.append(
                (
                    pontuacao,
                    registro
                )
            )

        pontuados.sort(
            key=lambda item: item[0],
            reverse=True
        )

        selecionadas = (
            pontuados[:limite]
        )

        if not selecionadas:
            return []

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        ids = [
            registro[0]
            for _, registro
            in selecionadas
        ]

        with self.conectar() as db:

            for memoria_id in ids:

                db.execute("""
                    UPDATE long_term_memories

                    SET
                        last_accessed_at = ?,
                        access_count =
                            access_count + 1

                    WHERE id = ?
                """, (
                    agora,
                    memoria_id
                ))

            db.commit()

        resultado = []

        for pontuacao, registro in selecionadas:

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
                "relevancia": round(
                    pontuacao,
                    3
                )
            })

        return resultado