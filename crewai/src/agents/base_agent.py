from crewai import Agent
from src.config import get_settings

class EsoterBaseAgent:
    def __init__(self, role: str, goal: str, backstory: str, llm_model: str = "deepseek-chat"):
        self.settings = get_settings()
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm_model = llm_model

    def get_agent(self) -> Agent:
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            allow_delegation=False,
            verbose=True,
            # Note: CrewAI supports OpenAI-compatible LLMs via base_url
            # but for this scaffold we focus on role/goal/backstory
        )
