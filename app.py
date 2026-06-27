from flask import Flask, jsonify, render_template, request
import os
import sqlite3


app = Flask(__name__)
DB_PATH = os.path.join(app.root_path, "banco_tcc.django")


def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_tabelas(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            turma TEXT NOT NULL,
            objetivo TEXT NOT NULL DEFAULT 'Organizar a rotina de estudos'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            disciplina TEXT NOT NULL,
            especialidade TEXT NOT NULL DEFAULT 'Microlearning inclusivo'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            professor_id INTEGER NOT NULL,
            FOREIGN KEY (professor_id) REFERENCES professores(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS micro_aulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curso_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            duracao_minutos INTEGER NOT NULL,
            conteudo TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            micro_aula_id INTEGER NOT NULL,
            enunciado TEXT NOT NULL,
            tipo TEXT NOT NULL,
            resposta TEXT NOT NULL,
            FOREIGN KEY (micro_aula_id) REFERENCES micro_aulas(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progresso_alunos (
            aluno_id INTEGER NOT NULL,
            atividade_id INTEGER NOT NULL,
            concluida INTEGER NOT NULL DEFAULT 0 CHECK (concluida IN (0, 1)),
            atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (aluno_id, atividade_id),
            FOREIGN KEY (aluno_id) REFERENCES alunos(id),
            FOREIGN KEY (atividade_id) REFERENCES atividades(id)
        )
    """)


def garantir_coluna(cursor, tabela, coluna, definicao):
    colunas = [row["name"] for row in cursor.execute(f"PRAGMA table_info({tabela})")]
    if coluna not in colunas:
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def popular_exemplos(cursor):
    alunos = [
        ("Ana Clara Souza", "ana.aluna@neurod.com", "1o ano A", "Melhorar foco e revisao diaria"),
        ("Lucas Pereira", "lucas.aluno@neurod.com", "2o ano B", "Estudar em blocos curtos"),
        ("Mariana Lima", "mariana.aluna@neurod.com", "3o ano C", "Preparacao para apresentacoes"),
    ]
    professores = [
        ("Prof. Carla Mendes", "carla.prof@neurod.com", "Biologia", "Aprendizagem ativa"),
        ("Prof. Ricardo Alves", "ricardo.prof@neurod.com", "Matematica", "Atividades objetivas"),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO alunos (nome, email, turma, objetivo)
        VALUES (?, ?, ?, ?)
        """,
        alunos,
    )
    cursor.executemany(
        """
        INSERT OR IGNORE INTO professores (nome, email, disciplina, especialidade)
        VALUES (?, ?, ?, ?)
        """,
        professores,
    )

    carla_id = cursor.execute(
        "SELECT id FROM professores WHERE email = ?", ("carla.prof@neurod.com",)
    ).fetchone()["id"]
    ricardo_id = cursor.execute(
        "SELECT id FROM professores WHERE email = ?", ("ricardo.prof@neurod.com",)
    ).fetchone()["id"]

    cursos = [
        (1, "Neurodiversidade e Rotina de Estudos", "Trilhas curtas para foco, revisao e autonomia.", carla_id),
        (2, "Matematica em Microdesafios", "Exercicios rapidos com feedback direto.", ricardo_id),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO cursos (id, titulo, descricao, professor_id)
        VALUES (?, ?, ?, ?)
        """,
        cursos,
    )

    micro_aulas = [
        (1, 1, "Saudacao e combinados do dia", 2, "Escolha um local tranquilo, separe o material e defina uma meta pequena.", 1),
        (2, 1, "Microlearning na pratica", 4, "Estude um conceito por vez, com pausas curtas e uma atividade objetiva.", 2),
        (3, 1, "Revisao ativa", 3, "Explique em uma frase o que aprendeu e marque o que ainda precisa rever.", 3),
        (4, 2, "Porcentagem no cotidiano", 5, "Transforme porcentagens em fracoes simples antes de resolver.", 1),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO micro_aulas (id, curso_id, titulo, duracao_minutos, conteudo, ordem)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        micro_aulas,
    )

    atividades = [
        (1, 1, "Marque quando sua meta curta de hoje estiver definida.", "checklist", "Meta definida"),
        (2, 2, "Qual e a principal ideia do microlearning?", "pergunta", "Aprender em partes curtas"),
        (3, 3, "Escreva uma frase de revisao sobre o conteudo estudado.", "reflexao", "Revisao ativa"),
        (4, 4, "Quanto e 10% de 80?", "pergunta", "8"),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO atividades (id, micro_aula_id, enunciado, tipo, resposta)
        VALUES (?, ?, ?, ?, ?)
        """,
        atividades,
    )

    ana_id = cursor.execute(
        "SELECT id FROM alunos WHERE email = ?", ("ana.aluna@neurod.com",)
    ).fetchone()["id"]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO progresso_alunos (aluno_id, atividade_id, concluida)
        VALUES (?, ?, ?)
        """,
        [(ana_id, 1, 1), (ana_id, 2, 0), (ana_id, 3, 0)],
    )


def init_db():
    conn = conectar_banco()
    try:
        cursor = conn.cursor()
        criar_tabelas(cursor)
        garantir_coluna(cursor, "alunos", "objetivo", "TEXT NOT NULL DEFAULT 'Organizar a rotina de estudos'")
        garantir_coluna(cursor, "professores", "especialidade", "TEXT NOT NULL DEFAULT 'Microlearning inclusivo'")
        popular_exemplos(cursor)
        conn.commit()
    finally:
        conn.close()


def validar_campos(dados, campos):
    faltando = [campo for campo in campos if not str(dados.get(campo, "")).strip()]
    if faltando:
        return f"Campos obrigatorios: {', '.join(faltando)}"
    return None


def row_to_dict(row):
    return dict(row) if row else None


@app.route("/")
def index():
    return render_template("app.html")


@app.route("/api/alunos", methods=["GET"])
def get_alunos():
    with conectar_banco() as conn:
        rows = conn.execute(
            "SELECT id, nome, email, turma, objetivo FROM alunos ORDER BY nome"
        ).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/alunos", methods=["POST"])
def post_aluno():
    dados = request.get_json(silent=True) or request.form
    erro = validar_campos(dados, ["nome", "email", "turma"])
    if erro:
        return jsonify({"erro": erro}), 400

    objetivo = dados.get("objetivo") or "Organizar a rotina de estudos"
    try:
        with conectar_banco() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alunos (nome, email, turma, objetivo)
                VALUES (?, ?, ?, ?)
                """,
                (dados["nome"].strip(), dados["email"].strip(), dados["turma"].strip(), objetivo.strip()),
            )
            aluno_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Ja existe um aluno com esse e-mail."}), 409

    return jsonify({"id": aluno_id, "nome": dados["nome"], "email": dados["email"], "turma": dados["turma"], "objetivo": objetivo}), 201


@app.route("/api/professores", methods=["GET"])
def get_professores():
    with conectar_banco() as conn:
        rows = conn.execute(
            "SELECT id, nome, email, disciplina, especialidade FROM professores ORDER BY nome"
        ).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/professores", methods=["POST"])
def post_professor():
    dados = request.get_json(silent=True) or request.form
    erro = validar_campos(dados, ["nome", "email", "disciplina"])
    if erro:
        return jsonify({"erro": erro}), 400

    especialidade = dados.get("especialidade") or "Microlearning inclusivo"
    try:
        with conectar_banco() as conn:
            cursor = conn.execute(
                """
                INSERT INTO professores (nome, email, disciplina, especialidade)
                VALUES (?, ?, ?, ?)
                """,
                (
                    dados["nome"].strip(),
                    dados["email"].strip(),
                    dados["disciplina"].strip(),
                    especialidade.strip(),
                ),
            )
            professor_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Ja existe um professor com esse e-mail."}), 409

    return jsonify({
        "id": professor_id,
        "nome": dados["nome"],
        "email": dados["email"],
        "disciplina": dados["disciplina"],
        "especialidade": especialidade,
    }), 201


@app.route("/api/microlearning/aluno/<int:aluno_id>", methods=["GET"])
def microlearning_aluno(aluno_id):
    with conectar_banco() as conn:
        aluno = conn.execute(
            "SELECT id, nome, email, turma, objetivo FROM alunos WHERE id = ?", (aluno_id,)
        ).fetchone()
        if not aluno:
            return jsonify({"erro": "Aluno nao encontrado."}), 404

        atividades = conn.execute("""
            SELECT
                a.id,
                a.enunciado,
                a.tipo,
                a.resposta,
                ma.titulo AS micro_aula,
                ma.conteudo,
                ma.duracao_minutos,
                c.titulo AS curso,
                COALESCE(pa.concluida, 0) AS concluida
            FROM atividades a
            JOIN micro_aulas ma ON ma.id = a.micro_aula_id
            JOIN cursos c ON c.id = ma.curso_id
            LEFT JOIN progresso_alunos pa
                ON pa.atividade_id = a.id AND pa.aluno_id = ?
            ORDER BY c.id, ma.ordem, a.id
        """, (aluno_id,)).fetchall()

    return jsonify({
        "perfil": "aluno",
        "saudacao": f"Ola, {aluno['nome']}! Sua trilha de microlearning ja esta pronta.",
        "pessoa": row_to_dict(aluno),
        "atividades": [row_to_dict(row) for row in atividades],
    })


@app.route("/api/microlearning/professor/<int:professor_id>", methods=["GET"])
def microlearning_professor(professor_id):
    with conectar_banco() as conn:
        professor = conn.execute(
            """
            SELECT id, nome, email, disciplina, especialidade
            FROM professores
            WHERE id = ?
            """,
            (professor_id,),
        ).fetchone()
        if not professor:
            return jsonify({"erro": "Professor nao encontrado."}), 404

        aulas = conn.execute("""
            SELECT
                c.titulo AS curso,
                c.descricao,
                ma.titulo AS micro_aula,
                ma.duracao_minutos,
                ma.conteudo,
                COUNT(a.id) AS atividades
            FROM cursos c
            JOIN micro_aulas ma ON ma.curso_id = c.id
            LEFT JOIN atividades a ON a.micro_aula_id = ma.id
            WHERE c.professor_id = ?
            GROUP BY c.id, ma.id
            ORDER BY c.id, ma.ordem
        """, (professor_id,)).fetchall()

        turma = conn.execute("""
            SELECT
                COUNT(DISTINCT al.id) AS alunos,
                COUNT(pa.atividade_id) AS entregas,
                SUM(CASE WHEN pa.concluida = 1 THEN 1 ELSE 0 END) AS concluidas
            FROM alunos al
            LEFT JOIN progresso_alunos pa ON pa.aluno_id = al.id
        """).fetchone()

    return jsonify({
        "perfil": "professor",
        "saudacao": f"Ola, {professor['nome']}! Aqui estao suas aulas curtas para aplicar hoje.",
        "pessoa": row_to_dict(professor),
        "resumo_turma": row_to_dict(turma),
        "aulas": [row_to_dict(row) for row in aulas],
    })


@app.route("/api/progresso", methods=["POST"])
def salvar_progresso():
    dados = request.get_json(silent=True) or {}
    erro = validar_campos(dados, ["aluno_id", "atividade_id"])
    if erro:
        return jsonify({"erro": erro}), 400

    concluida = 1 if dados.get("concluida") else 0
    with conectar_banco() as conn:
        conn.execute(
            """
            INSERT INTO progresso_alunos (aluno_id, atividade_id, concluida, atualizado_em)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(aluno_id, atividade_id)
            DO UPDATE SET concluida = excluded.concluida, atualizado_em = CURRENT_TIMESTAMP
            """,
            (dados["aluno_id"], dados["atividade_id"], concluida),
        )
    return jsonify({"ok": True, "concluida": bool(concluida)})


@app.route("/api/banco/resumo", methods=["GET"])
def resumo_banco():
    tabelas = ["alunos", "professores", "cursos", "micro_aulas", "atividades", "progresso_alunos"]
    with conectar_banco() as conn:
        resumo = {
            tabela: conn.execute(f"SELECT COUNT(*) AS total FROM {tabela}").fetchone()["total"]
            for tabela in tabelas
        }
    return jsonify({"arquivo": DB_PATH, "tabelas": resumo})


init_db()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
