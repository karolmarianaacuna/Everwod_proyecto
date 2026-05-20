#funcion que trae los mensajes de la base de datos por workspace_id

import logging

from app.core.database import get_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_messages_by_workspace_id(workspace_id: int, limit: int = 1000):

    query = """
        SELECT 
            w.id,
            w.name,
            cm.message,
            cm.created_at
        FROM chat_messages AS cm
        INNER JOIN agent_chats AS ac 
            ON cm.agent_chat_id = ac.id
        INNER JOIN workspaces AS w 
            ON ac.workspace_id = w.id
        WHERE 
            cm.message IS NOT NULL
            AND cm.message->>'role' = 'user'
            AND w.id = %s
        ORDER BY cm.created_at DESC
        LIMIT %s
        
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query, (workspace_id, limit))

        rows = cursor.fetchall()
        cursor.close()

        return rows
    except Exception as e:
        logger.error(f"Error consulta de mensajes por workspace BD: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()
