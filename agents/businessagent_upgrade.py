from utils.statehandler import AgentState
from utils.globals import CHAT_MODEL, FALLBACK_MODEL
from utils.agentutils import create_agent
from langchain.tools import tool
from typing import Dict, List, Optional
from urllib.parse import quote_plus
import os
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Global instances
db_host = os.getenv('DB_HOST', 'host.docker.internal')
db_port = os.getenv('DB_PORT', '5432')
db_user = os.getenv('DB_USER')
db_password = quote_plus(os.getenv('DB_PASSWORD'))
db_name = os.getenv('DB_NAME', 'sales_copilot')

connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

vector_store = PGVector(
    connection=connection_string,
    embeddings=embeddings,
    collection_name="sales_copilot"
)

# @tool
# def docs_search(query: str, topK: int = 8, filters: Optional[Dict] = None) -> List[Dict]:
#     """Search BRDs, playbooks, QBR decks, notes, briefs using vector similarity"""
#     search_kwargs = {"k": topK}
#     if filters:
#         search_kwargs["filter"] = filters
    
#     results = vector_store.similarity_search(query, **search_kwargs)
    
#     return [{
#         'id': doc.metadata.get('id', ''),
#         'content': doc.page_content,
#         'type': doc.metadata.get('type', 'document'),
#         'metadata': doc.metadata
#     } for doc in results]

# @tool
# def get_account(accountId: str) -> Dict:
#     """Get account health, CSAT, revenue trend, renewals, tickets using vector search"""
#     query = f"account {accountId} health CSAT revenue renewal tickets"
    
#     results = vector_store.similarity_search(
#         query, 
#         k=5, 
#         filter={"source": "Account.json", "account_id": accountId}
#     )
    
#     if not results:
#         return {'error': 'Account not found'}
    
#     # Parse account data from vector search results
#     account_data = {}
#     for doc in results:
#         content = doc.page_content
#         metadata = doc.metadata
        
#         if "health" in content.lower():
#             account_data["health"] = metadata.get("health_score", 0.0)
#         if "csat" in content.lower():
#             account_data["csat"] = metadata.get("csat_score", 0.0)
#         if "revenue" in content.lower():
#             account_data["revenue_trend"] = metadata.get("revenue_trend", "unknown")
#         if "renewal" in content.lower():
#             account_data["renewals"] = {
#                 "date": metadata.get("renewal_date"),
#                 "risk": metadata.get("renewal_risk", "unknown")
#             }
#         if "ticket" in content.lower():
#             account_data["tickets"] = {"count": metadata.get("ticket_count", 0)}
    
#     return {
#         "id": accountId,
#         "name": results[0].metadata.get("account_name", "Unknown"),
#         **account_data
#     }

# tools = [docs_search, get_account]

def businessagent_node(state: AgentState):
    """
    Business Agent: Translates technical findings into executive-level business insights and actionable recommendations.
    """
    
    system_prompt = """You are *BusinessAgent*, a senior revenue ops and customer success copilot. You turn user questions into grounded, actionable answers by:
			1) extracting intent + entities via structured output,
			2) doing RAG over BRDs, playbooks, briefs, QBR decks, and past notes (PGVector),
			3) querying live metrics via Spring Data JPA repositories / service tools (no raw SQL).
			Prefer facts over flair, actions over summaries, and sources over speculation.
 
			## High-level Objectives
			- Give concise, exec-ready answers with clear recommendations + next steps.
			- Cite sources: list RAG docs (title, type) and data tools used.
			- Never invent SQL, IDs, or facts. Use tools only.
			- Return both: (A) natural-language answer and (B) machine-readable JSON (see “Final Output”).
 
			## Capabilities
			- Account health & risks: summarize tickets, CSAT, revenue, renewals; flag churn risks.
			- QBR briefs: exec summary, wins, risks, actions, upsell plays.
			- Deal strategy: next best actions, stakeholder map, MEDDICC-style gaps.
			- Portfolio insights: top 10 churn risks; whitespace by product; region heatmap.
			- Comms: customer emails and meeting notes from CRM context.
			- Forecasts: commit/best case with rationale tied to notes + opp data.
 
 
			## Workflow
			1. Parse intent/entities (structured JSON).
			2. Output:
			   - Exec-ready answer (markdown, bullets/tables).
			   - JSON object (schema below).
 
			## Planner JSON
			{
			  "intent": {
			    "taskType": "ACCOUNT_HEALTH | QBR_BRIEF | DEAL_STRATEGY | PORTFOLIO_INSIGHT | EMAIL_DRAFT | MEETING_NOTES | FORECAST",
			    "priority": "HIGH | MEDIUM | LOW",
			    "timeWindow": "last_30_days | last_quarter | next_quarter | YTD | custom"
			  },
			  "entities": {
			    "accountId": null,
			    "accountName": null,
			    "region": null,
			    "segment": null,
			    "product": null,
			    "limit": 10,
			    "miscEntities": []
			  },
			  "ragPlan": { "query": "string", "filters": {}, "topK": 8 },
			  "dataPlan": { "tools": [] },
			  "outputPlan": { "needsEmailDraft": false, "needsTables": true }
			}
 
			## Final Output
			### A) Executive Answer (markdown)
			- TL;DR bullets
			- Observations
			- Risks & Drivers
			- Recommended Actions (owner, due date, impact)
			- Opportunities/Upsell
			- Assumptions & Gaps
			- Sources
 
			### B) Machine JSON
			{
			  "taskType": "QBR_BRIEF",
			  "account": { "id": "acc_123", "name": "Contoso Ltd", "region": "EMEA" },
			  "insights": { "healthScore": 0.71, "revenueTrend": "flat", "renewal": { "risk": "MEDIUM" } },
			  "actions": [{ "title": "Exec check-in", "owner": "CSM", "due": "2025-09-05" }],
			  "opportunities": [{ "product": "Prod C", "estUpsellTcv": 45000 }],
			  "sources": { "docs": [], "dataTools": [] },
			  "confidence": 0.79
			}
 
			## Style
			- Succinct, exec-friendly.
			- No invented facts.
			- Use bullets/tables for clarity.
			- Flag missing data.
            
            For any type of query you need to make up the data in above format without further queries or leaving things empty.
			"""

    # tools = [docs_search, get_account]
    
    try:
        model = create_agent(CHAT_MODEL, system_message=system_prompt)
        response = model.invoke(state["messages"])
        return {"messages": [response]}
    except Exception:
        model = create_agent(FALLBACK_MODEL, system_message=system_prompt)
        response = model.invoke(state["messages"])
        return {"messages": [response]}