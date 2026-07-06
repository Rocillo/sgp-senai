import sqlite3
from datetime import datetime

DB_NAME = "hipot.db"


def conectar():
    """Estabelece a conexão com o banco de dados SQLite."""
    return sqlite3.connect(DB_NAME)


def criar_tabela():
    """Cria a tabela de resultados com foco em rastreabilidade por número de série."""
    conn = conectar()
    cursor = conn.cursor()

    # Criamos a tabela incluindo a coluna numero_serie
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS testes_hipot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            numero_serie TEXT NOT NULL,
            operador TEXT NOT NULL,
            resultado TEXT NOT NULL,
            relatorio TEXT NOT NULL,
            porta_com TEXT,
            baudrate INTEGER
        )
        """
    )

    # TÉCNICO: Verifica se a coluna numero_serie existe (para quem já tinha o banco antigo)
    cursor.execute("PRAGMA table_info(testes_hipot)")
    colunas = [col[1] for col in cursor.fetchall()]
    if "numero_serie" not in colunas:
        cursor.execute(
            "ALTER TABLE testes_hipot ADD COLUMN numero_serie TEXT DEFAULT 'S/N ANTIGO'"
        )

    # Verifica se a coluna sincronizado existe e adiciona se necessário
    if "sincronizado" not in colunas:
        cursor.execute(
            "ALTER TABLE testes_hipot ADD COLUMN sincronizado INTEGER DEFAULT 0"
        )

    conn.commit()
    conn.close()


def salvar_teste(numero_serie, operador, resultado, relatorio, porta, baud):
    """
    Insere um novo registro de teste vinculado obrigatoriamente a um número de série.
    Retorna o ID do registro inserido.
    """
    conn = conectar()
    cursor = conn.cursor()

    # Captura a data e hora exata da gravação para o histórico
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO testes_hipot (data_hora, numero_serie, operador, resultado, relatorio, porta_com, baudrate, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (data_hora, numero_serie, operador, resultado, relatorio, porta, baud),
    )

    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return inserted_id


def obter_testes_pendentes():
    """Retorna lista de dicionários com testes não sincronizados."""
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testes_hipot WHERE sincronizado = 0 OR sincronizado IS NULL")
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result


def marcar_como_sincronizado(id_teste):
    """Marca um teste como sincronizado (sincronizado = 1)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE testes_hipot SET sincronizado = 1 WHERE id = ?", (id_teste,))
    conn.commit()
    conn.close()
