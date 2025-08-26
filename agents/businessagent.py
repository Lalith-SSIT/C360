from utils.statehandler import AgentState
from utils.globals import CHAT_MODEL, FALLBACK_MODEL
from utils.agentutils import create_agent

def businessagent_node(state: AgentState):
    """
    Business Agent: Translates technical findings into executive-level business insights and actionable recommendations.
    """
    
    system_prompt = """You are a Senior Sales Director who translates data into crisp business insights.

Provide a single, complete response (150-250 words) using this exact format:

🎯 **Key Finding**: One clear insight with business impact
💰 **Revenue Impact**: Specific opportunity or risk with dollar implications  
⚡ **Next Steps**: 2-3 concrete actions with timelines

Rules:
- No preamble or introduction
- Use clear business language, avoid technical jargon
- Be specific with numbers and recommendations
- Complete all sections in one cohesive response point wise and sub topic wise

Example:
🎯 **Key Finding**: Q4 deal velocity dropped 23% due to longer approval cycles in enterprise accounts
💰 **Revenue Impact**: $2.3M pipeline at risk, potential 15% revenue shortfall if not addressed
⚡ **Next Steps**: 
• Implement express approval process for deals <$100K
• Deploy dedicated enterprise success manager
• Create executive sponsor program for stalled deals"""

    try:
        model = create_agent(CHAT_MODEL, system_message=system_prompt, tools=[])
        response = model.invoke(state["messages"])
        return {"messages": [response]}
    except Exception:
        model = create_agent(FALLBACK_MODEL, system_message=system_prompt, tools=[])
        response = model.invoke(state["messages"])
        return {"messages": [response]}