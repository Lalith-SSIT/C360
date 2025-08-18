from nemoguardrails import LLMRails, RailsConfig
from utils.statehandler import AgentState
import os

# Initialize guardrails
config = RailsConfig.from_path("guardrails")
rails = LLMRails(config)

def guardrails_check(state: AgentState):
    """
    Check if query should be handled by guardrails (greetings, help, etc.)
    Returns response if handled, None if should proceed to agents.
    """
    latest_message = state["messages"][-1].content
    
    # Simple pattern matching for fast response
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    help_requests = ["help", "what can you do", "how to use", "guide me"]
    
    message_lower = latest_message.lower()
    
    # Handle greetings
    if any(greeting in message_lower for greeting in greetings):
        return {
            "messages": [{
                "role": "assistant", 
                "content": "Hello! I'm your C360 Customer Intelligence Assistant. I can help you with customer data, opportunities, accounts, products, and support tickets. What would you like to know?"
            }],
            "next": "END"
        }
    
    # Handle help requests
    if any(help_req in message_lower for help_req in help_requests):
        return {
            "messages": [{
                "role": "assistant",
                "content": """I can help you with:
• Customer account information
• Opportunity analysis  
• Product data queries
• Support ticket insights
• Pipeline analysis

Just ask me questions like 'Show me top 5 accounts' or 'What opportunities are in the pipeline?'"""
            }],
            "next": "END"
        }
    
    # Let other agents handle the query
    return None