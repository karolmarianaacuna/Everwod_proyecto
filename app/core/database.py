import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings


def get_connection():
    try:
        connection = psycopg2.connect(
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            port=settings.db_port,
        )

        return connection

    except psycopg2.OperationalError as e:
        print("Error al conectar a la base de datos: ", e)
        raise