from .base_agent import EsoterBaseAgent

class KnowledgeCuratorAgent(EsoterBaseAgent):
    def __init__(self):
        super().__init__(
            role="Curador y Mantenedor de la Base de Conocimiento Esotérico",
            goal="Mantener actualizada y de alta calidad la base de conocimiento RAG, incorporando nuevo contenido y corrigiendo interpretaciones.",
            backstory="Eres el guardián de la sabiduría del sistema. Analizas cada documento, audio o vídeo para asegurar que los chunks sean de alta calidad, detectas gaps de conocimiento y clasificas el contenido motivacional con precisión quirúrgica.",
            llm_model="deepseek-chat"
        )
