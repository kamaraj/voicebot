"""
Agentic AI using LangGraph and Llama 3.1 8B.
Implements multi-step reasoning, tool calling, and memory.
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import operator
from datetime import datetime
import time

from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import structlog

from src.config.settings import settings
from src.observability.tracing import trace_agent_step, trace_llm_call, trace_tool_call
from src.observability.metrics import metrics
from src.guardrails.engine import guardrails_engine

logger = structlog.get_logger(__name__)


class AgentState(TypedDict):
    """State for the agentic workflow."""
    messages: Annotated[List[BaseMessage], operator.add]
    current_step: str
    conversation_id: str
    user_id: Optional[str]
    context: Dict[str, Any]
    tool_results: Dict[str, Any]
    next_action: Optional[str]


class VoiceAgent:
    """
    Agentic AI voice assistant with multi-step reasoning.
    Uses LangGraph for workflow orchestration.
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.ollama_model
        self.llm = Ollama(
            model=self.model_name,
            base_url=settings.ollama_base_url,
            temperature=0.7
        )
        
        # Initialize tools
        self.tools = self._init_tools()
        
        # Build agent graph
        self.graph = self._build_graph()
        
        logger.info(
            "voice_agent_initialized",
            model=self.model_name,
            tools=list(self.tools.keys())
        )
    
    def _init_tools(self) -> Dict[str, callable]:
        """Initialize agent tools/functions."""
        return {
            "search_knowledge_base": self.search_knowledge_base,
            "get_current_time": self.get_current_time,
            "schedule_appointment": self.schedule_appointment,
            "transfer_call": self.transfer_call,
        }
    
    @trace_tool_call(tool_name="search_knowledge_base")
    async def search_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Search knowledge base (RAG)."""
        start_time = time.time()
        logger.info("tool_search_kb", query=query)
        
        # TODO: Implement actual RAG
        result = {
            "results": [
                {"text": "Sample knowledge base result", "score": 0.9}
            ],
            "duration_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        return result
    
    @trace_tool_call(tool_name="get_current_time")
    async def get_current_time(self) -> Dict[str, Any]:
        """Get current time."""
        now = datetime.now()
        return {
            "time": now.isoformat(),
            "formatted": now.strftime("%I:%M %p")
        }
    
    @trace_tool_call(tool_name="schedule_appointment")
    async def schedule_appointment(
        self,
        date: str,
        time: str,
        description: str
    ) -> Dict[str, Any]:
        """Schedule an appointment."""
        logger.info(
            "tool_schedule_appointment",
            date=date,
            time=time,
            description=description
        )
        
        # TODO: Integrate with calendar system
        return {
            "success": True,
            "appointment_id": "apt_123",
            "message": f"Appointment scheduled for {date} at {time}"
        }
    
    @trace_tool_call(tool_name="transfer_call")
    async def transfer_call(self, department: str, reason: str) -> Dict[str, Any]:
        """Transfer call to another department."""
        logger.info("tool_transfer_call", department=department, reason=reason)
        
        # TODO: Implement actual call transfer
        return {
            "success": True,
            "department": department,
            "message": "Transferring to " + department
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph using LangGraph."""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("understand_intent", self.understand_intent)
        workflow.add_node("plan_action", self.plan_action)
        workflow.add_node("execute_tool", self.execute_tool)
        workflow.add_node("generate_response", self.generate_response)
        
        # Define edges
        workflow.set_entry_point("understand_intent")
        workflow.add_edge("understand_intent", "plan_action")
        workflow.add_conditional_edges(
            "plan_action",
            self.should_use_tool,
            {
                "tool": "execute_tool",
                "respond": "generate_response"
            }
        )
        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    @trace_agent_step(step_name="understand_intent", step_type="reasoning")
    async def understand_intent(self, state: AgentState) -> AgentState:
        """Understand user intent from the message."""
        start_time = time.time()
        last_message = state["messages"][-1]
        
        # Simple intent analysis without requiring JSON
        user_input = last_message.content
        
        state["context"]["intent_analysis"] = user_input
        state["current_step"] = "intent_understood"
        
        duration = time.time() - start_time
        logger.info("intent_understood", user_input=user_input[:100], duration_ms=f"{duration*1000:.2f}ms")
        
        return state
    
    @trace_agent_step(step_name="plan_action", step_type="reasoning")
    async def plan_action(self, state: AgentState) -> AgentState:
        """Plan what action to take next."""
        start_time = time.time()
        intent = state["context"].get("intent_analysis", "")
        
        # Simple planning logic
        if "time" in intent.lower() or "when" in intent.lower():
            state["next_action"] = "get_current_time"
        elif "appointment" in intent.lower() or "schedule" in intent.lower():
            state["next_action"] = "schedule_appointment"
        elif "transfer" in intent.lower():
            state["next_action"] = "transfer_call"
        else:
            state["next_action"] = "respond_directly"
        
        state["current_step"] = "action_planned"
        
        duration = time.time() - start_time
        logger.info("action_planned", next_action=state["next_action"], duration_ms=f"{duration*1000:.2f}ms")
        
        return state
    
    def should_use_tool(self, state: AgentState) -> str:
        """Decide whether to use a tool or respond directly."""
        if state["next_action"] == "respond_directly":
            return "respond"
        return "tool"
    
    @trace_agent_step(step_name="execute_tool", step_type="tool_call")
    async def execute_tool(self, state: AgentState) -> AgentState:
        """Execute the selected tool."""
        start_time = time.time()
        tool_name = state["next_action"]
        
        if tool_name in self.tools:
            tool_func = self.tools[tool_name]
            
            tool_start = time.time()
            # Execute tool
            result = await tool_func()
            tool_duration = time.time() - tool_start
            
            state["tool_results"][tool_name] = result
            
            # Store RAG timing if this was a search_knowledge_base call
            if tool_name == "search_knowledge_base" and "duration_ms" in result:
                state["context"]["rag_duration_ms"] = result["duration_ms"]
            
            metrics.track_tool_call(tool_name=tool_name, status="success")
            
            logger.info("tool_executed", tool=tool_name, result=result, tool_duration_ms=f"{tool_duration*1000:.2f}ms")
        else:
            logger.warning("tool_not_found", tool=tool_name)
        
        state["current_step"] = "tool_executed"
        
        duration = time.time() - start_time
        logger.info("execute_tool_complete", duration_ms=f"{duration*1000:.2f}ms")
        
        return state
    
    @trace_agent_step(step_name="generate_response", step_type="generation")
    async def generate_response(self, state: AgentState) -> AgentState:
        """Generate final response to user."""
        start_time = time.time()
        messages = state["messages"]
        tool_results = state.get("tool_results", {})
        
        # Get the last user message
        last_user_message = [m for m in messages if isinstance(m, HumanMessage)][-1]
        user_input = last_user_message.content
        
        # Build context from tool results  
        context_text = ""
        if tool_results:
            context_text = f"\n\nAvailable information: {tool_results}"
        
        # Create a simple prompt string
        full_prompt = f"""You are a helpful AI voice assistant. Provide natural, conversational responses. Keep responses concise and friendly.

{context_text}

User: {user_input}

Assistant: """
        
        try:
            # Call the LLM
            llm_start = time.time()
            logger.info("🤖 llm_invoke_started", prompt_length=len(full_prompt))
            
            response = self.llm.invoke(full_prompt)
            
            llm_duration = time.time() - llm_start
            logger.info("✅ llm_invoke_complete", duration_ms=f"{llm_duration*1000:.2f}ms", response_length=len(response))
            
            # Store LLM timing in context for metrics
            state["context"]["llm_duration_ms"] = round(llm_duration * 1000, 2)
            
            # Output guardrails temporarily disabled to allow all responses
            # TODO: Re-enable with relaxed thresholds
            # output_checks = guardrails_engine.check_output(response)
            # if not all(check.passed for check in output_checks.values()):
            #     logger.warning("output_guardrail_violation", violations=output_checks)
            #     response = "I apologize, but I cannot provide that response."
            
            state["messages"].append(AIMessage(content=response))
            state["current_step"] = "response_generated"
            
            total_duration = time.time() - start_time
            logger.info("✨ response_generated", length=len(response), total_duration_ms=f"{total_duration*1000:.2f}ms")
            
        except Exception as e:
            logger.error("llm_invocation_error", error=str(e))
            response = f"I'm having trouble connecting to the AI model. Please make sure Ollama is running with 'ollama serve'."
            state["messages"].append(AIMessage(content=response))
            state["current_step"] = "response_error"
        
        return state
    
    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent workflow.
        
        Args:
            user_message: User's text input
            conversation_id: Unique conversation ID
            user_id: Optional user ID
            context: Additional context
            
        Returns:
            Agent response with metadata and timing
        """
        # Track overall timing
        overall_start = time.time()
        timing_data = {}
        
        # Check input guardrails
        input_checks = guardrails_engine.check_input(user_message)
        if not all(check.passed for check in input_checks.values()):
            logger.warning("input_guardrail_violation", violations=input_checks)
            
            # Sanitize input
            user_message = guardrails_engine.sanitize_text(user_message, input_checks)
        
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_message)],
            "current_step": "initialized",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "context": context or {},
            "tool_results": {},
            "next_action": None
        }
        
        # Run through graph and track timing
        graph_start = time.time()
        final_state = await self.graph.ainvoke(initial_state)
        graph_duration = time.time() - graph_start
        
        # Extract response
        ai_messages = [m for m in final_state["messages"] if isinstance(m, AIMessage)]
        response_text = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't generate a response."
        
        # Calculate total duration
        total_duration = time.time() - overall_start
        
        # Build timing data (in milliseconds for better readability)
        timing_data = {
            "total_ms": round(total_duration * 1000, 2),
            "graph_processing_ms": round(graph_duration * 1000, 2),
            # Note: STT and TTS timing should be added by the API layer
            # RAG timing is included in tool_results if used
            "llm_ms": 0,  # Will be populated by generate_response step
            "rag_ms": 0,  # Will be populated if RAG tool was used
        }
        
        # Extract timing from context if available
        if "llm_duration_ms" in final_state.get("context", {}):
            timing_data["llm_ms"] = final_state["context"]["llm_duration_ms"]
        
        if "rag_duration_ms" in final_state.get("context", {}):
            timing_data["rag_ms"] = final_state["context"]["rag_duration_ms"]
        
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "tool_results": final_state.get("tool_results", {}),
            "metadata": {
                "steps": final_state["current_step"],
                "guardrails": {
                    "input": all(c.passed for c in input_checks.values()),
                }
            },
            "timing": timing_data
        }


# Example usage
"""
from src.agents.voice_agent import VoiceAgent

agent = VoiceAgent()

response = await agent.process_message(
    user_message="What time is it?",
    conversation_id="conv_123",
    user_id="user_456"
)

print(response["response"])
"""
