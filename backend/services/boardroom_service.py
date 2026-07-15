"""
Boardroom service - handles multi-agent debate system using LangGraph.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, AsyncIterator, Union
from datetime import datetime, timezone
from config import get_settings
from models import BoardroomDebateResponse, AgentMessage
from services.hybrid_retrieval_service import HybridRetrievalService

settings = get_settings()


def _extract_llm_text(content: Union[str, list, Any]) -> str:
    """Normalize Gemini/LangChain response content to a plain string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return str(content).strip()


class DebateState(TypedDict):
    """State definition for the debate graph."""
    idea: str
    data_requirements: List[str]
    graph_context: str
    messages: List[Dict[str, Any]]
    final_verdict: str
    round_count: int
    max_rounds: int


class BoardroomService:
    """Service for running multi-agent debates using LangGraph."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.temperature
        )
        
        self.graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        
        # Build the debate graph
        self.debate_graph = self._build_debate_graph()
        self.hybrid_retrieval = HybridRetrievalService()
    
    def _build_debate_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for multi-agent debate.
        
        Flow:
        START -> Supervisor -> Retrieval -> Strategist -> Risk Analyst
        Risk Analyst -> (loop back to Strategist OR continue to Synthesizer)
        Synthesizer -> END
        """
        workflow = StateGraph(DebateState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("strategist", self._strategist_node)
        workflow.add_node("risk_analyst", self._risk_analyst_node)
        workflow.add_node("synthesizer", self._synthesizer_node)
        
        # Define edges
        workflow.set_entry_point("supervisor")
        workflow.add_edge("supervisor", "retrieval")
        workflow.add_edge("retrieval", "strategist")
        workflow.add_edge("strategist", "risk_analyst")
        
        # Conditional edge: loop or end
        workflow.add_conditional_edges(
            "risk_analyst",
            self._should_continue_debate,
            {
                "continue": "strategist",
                "end": "synthesizer"
            }
        )
        
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    def _supervisor_node(self, state: DebateState) -> DebateState:
        """
        Supervisor analyzes the idea and determines data requirements.
        """
        prompt = f"""
        You are the Supervisor of a debate system. Analyze the following idea and determine 
        what specific data points from our company Knowledge Graph are needed to debate this effectively.
        
        The Knowledge Graph contains:
        - Employees (with roles, departments)
        - Projects (with status, descriptions)
        - Departments (with budgets)
        - Clients (with industries)
        - OKRs (objectives and key results)
        - Budgets (allocations)
        
        Idea: {state['idea']}
        
        List 3-5 specific data requirements as questions that need to be answered from the graph.
        Format as a numbered list.
        """
        
        response = self.llm.invoke(prompt)
        raw_text = _extract_llm_text(response.content)
        requirements = [r.strip() for r in raw_text.split("\n") if r.strip()]
        
        state['data_requirements'] = requirements
        state['messages'].append({
            "agent": "Supervisor",
            "message": f"Data requirements identified:\n" + "\n".join(requirements),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return state
    
    def _retrieval_node(self, state: DebateState) -> DebateState:
        """
        Retrieval node: hybrid vector + graph expansion, supplemented by requirement-specific search.
        """
        context_parts = []

        try:
            hybrid = self.hybrid_retrieval.retrieve(state["idea"], top_k=5)
            if hybrid["vector_context"]:
                context_parts.append("=== Semantic document matches ===")
                context_parts.append(hybrid["vector_context"])
            if hybrid["graph_context"]:
                context_parts.append("=== Entities linked to documents ===")
                context_parts.append(hybrid["graph_context"])
        except Exception as e:
            context_parts.append(f"Hybrid retrieval error: {str(e)}")

        for requirement in state["data_requirements"][:3]:
            try:
                req_hybrid = self.hybrid_retrieval.retrieve(requirement, top_k=3)
                snippet = req_hybrid["vector_context"][:800]
                if snippet:
                    context_parts.append(f"=== Requirement: {requirement[:80]} ===")
                    context_parts.append(snippet)
            except Exception:
                pass

        state["graph_context"] = "\n\n".join(context_parts)
        state["messages"].append({
            "agent": "Retrieval",
            "message": (
                f"Retrieved hybrid context: "
                f"{len(context_parts)} sections from vector search and graph expansion"
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return state
    
    def _strategist_node(self, state: DebateState) -> DebateState:
        """
        Strategist argues IN FAVOR of the idea.
        """
        # Get previous messages for context
        previous_messages = "\n".join([
            f"{msg['agent']}: {msg['message']}" 
            for msg in state['messages'][-3:] if msg['agent'] in ['Risk Analyst', 'Strategist']
        ])
        
        prompt = f"""
        You are the Strategist. Your goal is to argue IN FAVOR of the following idea.
        You MUST base your arguments strictly on the retrieved graph context.
        
        Idea: {state['idea']}
        
        Graph Context:
        {state['graph_context']}
        
        Previous Discussion:
        {previous_messages if previous_messages else 'This is the first round.'}
        
        Provide a compelling argument FOR this idea. Find synergies, opportunities, and paths to success.
        If the Risk Analyst raised concerns, address them directly.
        Keep your response concise (3-4 paragraphs).
        """
        
        response = self.llm.invoke(prompt)
        message = _extract_llm_text(response.content)
        
        state['messages'].append({
            "agent": "Strategist",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return state
    
    def _risk_analyst_node(self, state: DebateState) -> DebateState:
        """
        Risk Analyst argues AGAINST the idea.
        """
        # Get previous messages for context
        previous_messages = "\n".join([
            f"{msg['agent']}: {msg['message']}" 
            for msg in state['messages'][-3:] if msg['agent'] in ['Risk Analyst', 'Strategist']
        ])
        
        prompt = f"""
        You are the Risk Analyst. Your goal is to argue AGAINST the following idea.
        You MUST base your arguments strictly on the retrieved graph context.
        
        Idea: {state['idea']}
        
        Graph Context:
        {state['graph_context']}
        
        Previous Discussion:
        {previous_messages if previous_messages else 'This is the first round.'}
        
        Identify risks, constraints, and potential failures. Critique the Strategist's optimism.
        Point out resource constraints, historical failures, or bottlenecks from the data.
        Keep your response concise (3-4 paragraphs).
        """
        
        response = self.llm.invoke(prompt)
        message = _extract_llm_text(response.content)
        
        state['messages'].append({
            "agent": "Risk Analyst",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        state['round_count'] += 1
        
        return state
    
    def _synthesizer_node(self, state: DebateState) -> DebateState:
        """
        Synthesizer creates the final executive summary.
        """
        debate_transcript = "\n\n".join([
            f"**{msg['agent']}:**\n{msg['message']}" 
            for msg in state['messages'] if msg['agent'] in ['Strategist', 'Risk Analyst']
        ])
        
        prompt = f"""
        You are the Executive Synthesizer. Review the debate transcript and produce a clean executive summary.
        
        Original Idea: {state['idea']}
        
        Debate Transcript:
        {debate_transcript}
        
        Provide:
        1. **Strongest Arguments FOR** (2-3 points with specific data references)
        2. **Most Critical Risks** (2-3 points with specific data references)
        3. **Final Recommendation** (Go/No-Go with conditions)
        
        Be specific and cite the Neo4j data points that support each argument.
        """
        
        response = self.llm.invoke(prompt)
        verdict = _extract_llm_text(response.content)
        
        state['final_verdict'] = verdict
        state['messages'].append({
            "agent": "Synthesizer",
            "message": verdict,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return state
    
    def _should_continue_debate(self, state: DebateState) -> str:
        """
        Determine if the debate should continue or end.
        """
        if state['round_count'] >= state['max_rounds']:
            return "end"
        return "continue"
    
    async def run_debate(self, idea: str, rounds: int = 3) -> BoardroomDebateResponse:
        """
        Run a complete debate on the given idea.
        
        Args:
            idea: The user's idea to debate
            rounds: Number of debate rounds
            
        Returns:
            BoardroomDebateResponse with full transcript and verdict
        """
        initial_state: DebateState = {
            "idea": idea,
            "data_requirements": [],
            "graph_context": "",
            "messages": [],
            "final_verdict": "",
            "round_count": 0,
            "max_rounds": rounds
        }
        
        # Run the graph
        final_state = self.debate_graph.invoke(initial_state)
        
        # Convert messages to AgentMessage models
        agent_messages = [
            AgentMessage(
                agent=msg["agent"],
                message=msg["message"],
                timestamp=msg["timestamp"]
            )
            for msg in final_state["messages"]
        ]
        
        # Extract data sources from graph context
        data_sources = final_state["graph_context"].split("\n\n")[:5]
        
        return BoardroomDebateResponse(
            idea=idea,
            debate_transcript=agent_messages,
            final_verdict=final_state["final_verdict"],
            data_sources=data_sources
        )
    
    async def stream_debate(self, idea: str, rounds: int = 3) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream the debate in real-time as agents respond.
        
        Args:
            idea: The user's idea to debate
            rounds: Number of debate rounds
            
        Yields:
            Dictionary events for each agent message
        """
        initial_state: DebateState = {
            "idea": idea,
            "data_requirements": [],
            "graph_context": "",
            "messages": [],
            "final_verdict": "",
            "round_count": 0,
            "max_rounds": rounds
        }
        
        # Stream events from the graph
        current_state: DebateState = {**initial_state}
        async for event in self.debate_graph.astream(initial_state):
            for node_name, node_update in event.items():
                current_state = {**current_state, **node_update}
                if node_update.get("messages"):
                    latest_message = node_update["messages"][-1]
                    yield {
                        "type": "message",
                        "node": node_name,
                        "agent": latest_message["agent"],
                        "message": latest_message["message"],
                        "timestamp": latest_message["timestamp"],
                        "round_count": current_state.get("round_count", 0),
                    }

        data_sources = [
            section.strip()
            for section in current_state.get("graph_context", "").split("\n\n")
            if section.strip()
        ][:5]

        yield {
            "type": "complete",
            "final_verdict": current_state.get("final_verdict", ""),
            "data_sources": data_sources,
        }

# Made with Bob
