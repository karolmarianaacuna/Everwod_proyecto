import logging

from app.core.database import get_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def get_existing_faqs(workspace_id: int, limit: int = 1000) -> list:

    query = """
        SELECT 
            w.id AS workspace_id,
            w.name AS workspace_name,
            af.question,
            af.answer

        FROM agent_faqs af

        INNER JOIN agents a
            ON af.agent_id = a.id

        INNER JOIN workspaces w
            ON a.workspace_id = w.id

        WHERE w.id = %s
            AND af.deleted_at IS NULL

        ORDER BY af.created_at DESC
        LIMIT %s
    """

    conn = None

    try:

        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(query, (workspace_id, limit))

        rows = cur.fetchall()

        
        cur.close()

        return rows

    except Exception as e:

        logger.error(f"Error obteniendo FAQs: {e}", exc_info=True)

        return []

    finally:

        if conn:
            conn.close()