import logging

from app.core.database import get_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


#Obtener datos de FAQs existentes para un workspace
def get_existing_faqs(workspace_id: int, limit: int = 1000) -> list:

    query = """
        SELECT 
            w.id AS workspace_id,
            w.name AS workspace_name,
            af.question

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



#Guarda una nueva FAQ en la base de datos
def save_faq(workspace_id: int, question: str, agent_id: int, metadata: dict = None) -> int:
    """
    Args:
        workspace_id: ID del workspace
        question: Pregunta de la FAQ
        agent_id: ID del agent
        metadata: Datos adicionales (cluster_id, keywords, confidence, etc)
        
    Returns:
        ID de la FAQ guardada, o None si hay error
    """
    conn = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            INSERT INTO agent_faqs (agent_id, question, metadata, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
        """
        
        cur.execute(query, (agent_id, question, metadata))
        faq_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        
        logger.info(f"✅ FAQ guardada: {faq_id}")
        return faq_id
        
    except Exception as e:
        logger.error(f"Error guardando FAQ: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return None
        
    finally:
        if conn:
            conn.close()

#Verifica si existe una FAQ similar en el workspace
def faq_exists(workspace_id: int, question: str) -> bool:
    """
    Args:
        workspace_id: ID del workspace
        question: Pregunta a verificar
        
    Returns:
        True si existe, False si no
    """
    conn = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT COUNT(*) FROM agent_faqs af
            INNER JOIN agents a ON af.agent_id = a.id
            WHERE a.workspace_id = %s 
            AND af.deleted_at IS NULL
            AND LOWER(af.question) = LOWER(%s)
        """
        
        cur.execute(query, (workspace_id, question))
        count = cur.fetchone()[0]
        cur.close()
        
        return count > 0
        
    except Exception as e:
        logger.error(f"Error verificando FAQ: {e}", exc_info=True)
        return False
        
    finally:
        if conn:
            conn.close()

#Obtiene todos los workspaces del sistema
def get_all_workspaces() -> list:
    
    conn = None
    
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT id, name, logo, category, active FROM workspaces"
        cur.execute(query)
        
        rows = cur.fetchall()
        cur.close()
        
        logger.info(f"✅ {len(rows)} workspaces encontrados")
        return rows
        
    except Exception as e:
        logger.error(f"Error obteniendo workspaces: {e}", exc_info=True)
        return []
        
    finally:
        if conn:
            conn.close()

#  Trae la información de una sola empresa.
def get_workspace_context(workspace_id: int) -> dict:
    
    conn = None
    
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, name, created_at 
            FROM workspaces 
            WHERE id = %s AND deleted_at IS NULL
        """
        
        cur.execute(query, (workspace_id,))
        workspace = cur.fetchone()
        cur.close()
        
        if workspace:
            logger.info(f"✅ Workspace encontrado: {workspace['name']}")
            return dict(workspace)
        else:
            logger.warning(f"⚠️ Workspace {workspace_id} no encontrado")
            return None
            
    except Exception as e:
        logger.error(f"Error obteniendo contexto del workspace: {e}", exc_info=True)
        return None
        
    finally:
        if conn:
            conn.close()


def get_first_agent_id(workspace_id: int) -> int:
    """
    Obtiene el primer agent ID de un workspace
    
    Args:
        workspace_id: ID del workspace
        
    Returns:
        ID del agent, o None si no existe
    """
    conn = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT id FROM agents 
            WHERE workspace_id = %s AND deleted_at IS NULL 
            ORDER BY created_at ASC 
            LIMIT 1
        """
        
        cur.execute(query, (workspace_id,))
        result = cur.fetchone()
        cur.close()
        
        if result:
            agent_id = result[0]
            logger.info(f"✅ Agent encontrado: {agent_id}")
            return agent_id
        else:
            logger.warning(f"⚠️ No se encontró agent para workspace {workspace_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error obteniendo agent ID: {e}", exc_info=True)
        return None
        
    finally:
        if conn:
            conn.close()


def get_messages_by_workspace_id(workspace_id: int, limit: int = 1000) -> list:
   
    query = """
        SELECT 
            w.id,
            w.name,
            COALESCE(cm.message->>'content', cm.message->>'text', cm.message::text) as message,
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
        
        logger.info(f"✅ {len(rows)} mensajes obtenidos para workspace {workspace_id}")
        return rows
        
    except Exception as e:
        logger.error(f"Error obteniendo mensajes por workspace: {e}", exc_info=True)
        return []
        
    finally:
        if conn:
            conn.close()
            
            
            
def get_existing_faqs_answers(workspace_id: int, limit: int = 1000) -> list:
    """
    Obtiene las respuestas de FAQs existentes del workspace.
    Se usa como contexto para el LLM y para deduplicación.
    """
    query = """
        SELECT 
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

        logger.error(f"Error obteniendo respuestas de FAQs: {e}", exc_info=True)

        return []

    finally:

        if conn:
            conn.close()


def get_agent_texts(workspace_id: int) -> list:
    """
    Obtiene los textos del agente del workspace.
    Se usa como contexto adicional para el LLM.
    """
    query = """
        SELECT 
            at.text

        FROM agent_texts at

        INNER JOIN agents a
            ON at.agent_id = a.id

        INNER JOIN workspaces w
            ON a.workspace_id = w.id

        WHERE w.id = %s
            AND a.deleted_at IS NULL

        ORDER BY at.created_at DESC
    """

    conn = None

    try:

        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(query, (workspace_id,))

        rows = cur.fetchall()

        cur.close()

        return rows

    except Exception as e:

        logger.error(f"Error obteniendo textos del agente: {e}", exc_info=True)

        return []

    finally:

        if conn:
            conn.close()