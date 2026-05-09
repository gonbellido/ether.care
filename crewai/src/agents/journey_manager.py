"""
Journey Manager - Gestiona el estado de la sesión y la transición entre pasos.
Basado en los 10 Agentes del cerebro dinámico.
"""
import json
import logging
import aiomysql
from typing import Optional, Dict, Any
from src.config import get_settings

logger = logging.getLogger(__name__)

STEPS = {
    1: "Acogida & Encuadre",
    2: "Triaje MC (Motivo de Consulta)",
    3: "Validación CB (Código Biológico)",
    4: "Búsqueda Hachazo (MCb)",
    5: "Búsqueda Hachazo (MCn)",
    6: "Inmersión SEPe (Sentimientos, Emociones, Pensamientos)",
    7: "Profundización Miedos (Triple Pregunta)",
    8: "Vulnerabilidad & Amenaza",
    9: "Desvalorización Nuclear",
    10: "Proyección & Perfilado",
}

class JourneyManager:
    def __init__(self):
        self.settings = get_settings()

    async def _get_conn(self):
        return await aiomysql.connect(
            host=self.settings.mysql_host,
            port=self.settings.mysql_port,
            user=self.settings.mysql_user,
            password=self.settings.mysql_password,
            db=self.settings.mysql_database,
        )

    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Recupera el estado actual de la sesión."""
        conn = await self._get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT current_step, status FROM sessions WHERE session_id = %s",
                (session_id,)
            )
            session = await cur.fetchone()

            if not session:
                return {"step": 1, "status": "new", "data": {}}

            await cur.execute(
                "SELECT data_json FROM session_state WHERE session_id = %s",
                (session_id,)
            )
            state_data = await cur.fetchone()
            data = json.loads(state_data['data_json']) if state_data else {}

            return {
                "step": session['current_step'],
                "status": session['status'],
                "data": data
            }
        conn.close()

    async def update_session_state(self, session_id: str, user_id: str, step: int, data: Dict[str, Any], status: str = "active"):
        """Actualiza el paso y los datos de la sesión."""
        conn = await self._get_conn()
        async with conn.cursor() as cur:
            # Upsert session
            await cur.execute(
                "INSERT INTO sessions (session_id, user_id, current_step, status) "
                "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                "current_step = VALUES(current_step), status = VALUES(status)",
                (session_id, user_id, step, status)
            )

            # Upsert state
            await cur.execute(
                "INSERT INTO session_state (session_id, data_json) "
                "VALUES (%s, %s) ON DUPLICATE KEY UPDATE "
                "data_json = VALUES(data_json)",
                (session_id, json.dumps(data))
            )
            await conn.commit()
        conn.close()

    def get_next_step(self, current_step: int, session_data: Dict[str, Any]) -> int:
        """Lógica de transición de pasos."""
        if current_step == 2:
            mc_type = session_data.get("mc_type")
            if mc_type == "MCb":
                return 3
            else:
                return 5 # Salta a Hachazo MCn si no es biológico

        if current_step == 3:
            return 4 # Después de CB va Hachazo MCb

        if current_step == 4 or current_step == 5:
            return 6 # Ambos hachazos van a SEPe

        if current_step >= 10:
            return 10 # Fin del flujo guiado

        return current_step + 1
