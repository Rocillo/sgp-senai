import sqlite3
from sqlalchemy import create_engine, text

SRC_DB = r"C:\SGP\instance\pneumark.db"

DST_DB = "postgresql+psycopg://sgp_db_5sbe_user:MFUJjANGWAaXemUNX9o4XlZl5fMJhOrs@dpg-d6k9r27tskes73eaic40-a.oregon-postgres.render.com/sgp_db_5sbe"

print("Conectando banco local...")

src = sqlite3.connect(SRC_DB)
src.row_factory = sqlite3.Row

rows = src.execute("SELECT * FROM pecas").fetchall()

print("Peças local =", len(rows))

engine = create_engine(DST_DB)

with engine.begin() as conn:

    before = conn.execute(text("SELECT COUNT(*) FROM pecas")).scalar()
    print("Peças remoto antes =", before)

    if before != 0:
        raise SystemExit("ABORTADO: banco remoto nao esta vazio")

    cols = list(rows[0].keys())

    sql = text(
        f"INSERT INTO pecas ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})"
    )

    conn.execute(sql, [dict(r) for r in rows])

    after = conn.execute(text("SELECT COUNT(*) FROM pecas")).scalar()

    print("Peças remoto depois =", after)

print("MIGRACAO CONCLUIDA")
