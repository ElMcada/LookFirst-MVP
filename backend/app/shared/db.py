"""Conexión a PostgreSQL. Cada bounded context tiene su propio esquema (iam, catalogo, consulta)."""
from sqlalchemy import Enum, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

ESQUEMAS = ("iam", "catalogo", "consulta")


class Base(DeclarativeBase):
    pass


def enum_columna(enum_cls, nombre: str, esquema: str):
    """Tipo ENUM nativo de PostgreSQL (en el esquema del BC) que guarda el *valor* ('activa'), no el nombre."""
    return Enum(enum_cls, name=nombre, schema=esquema,
                values_callable=lambda e: [m.value for m in e], validate_strings=True)


def crear_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        # Solo para pruebas automáticas: SQLite no tiene esquemas, se aplanan.
        engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

        @event.listens_for(engine, "connect")
        def _fk(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        return engine.execution_options(schema_translate_map={s: None for s in ESQUEMAS})
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)


def asegurar_base_datos(url: str) -> None:
    """Si la base (p. ej. 'lookfirst') no existe en PostgreSQL, la crea conectándose a 'postgres'."""
    if not url.startswith("postgresql"):
        return
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import OperationalError

    destino = make_url(url)
    try:
        create_engine(destino).connect().close()
        return
    except OperationalError as e:
        if "does not exist" not in str(e) and "no existe" not in str(e):
            raise
    admin = create_engine(destino.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{destino.database}" ENCODING \'UTF8\''))
    admin.dispose()
    print(f"[LookFirst] Base de datos '{destino.database}' creada")


def inicializar_esquema(engine: Engine) -> None:
    # Importa los modelos ORM para registrarlos en Base.metadata
    from app.catalogo.infrastructure import orm as _c  # noqa: F401
    from app.consulta.infrastructure import orm as _q  # noqa: F401
    from app.iam.infrastructure import orm as _i  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            for esquema in ESQUEMAS:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {esquema}"))
    Base.metadata.create_all(engine)


def crear_fabrica_sesiones(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)
