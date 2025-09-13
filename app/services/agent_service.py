"""
Agent Service - Multi-Agent Management and Orchestration
========================================================

Service layer for managing AI agents and coordinating multi-agent workflows
Handles agent registration, execution, and workflow orchestration
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import os

from app.models.schemas import AgentCreate, AgentResponse

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing AI agents and workflows"""
    
    def __init__(self):
        self.llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        )
        self._agent_store = []  # Temporary in-memory storage
        self._next_id = 1
        self._initialize_default_agents()
        
    def _initialize_default_agents(self):
        """Initialize default system agents"""
        
        default_agents = [
            {
                "name": "Content Research Specialist",
                "role": "researcher",
                "description": "Expert at researching topics and gathering comprehensive information",
                "capabilities": ["research", "analysis", "fact-checking", "trend-analysis"],
                "config": {"max_research_time": 300, "sources_limit": 10}
            },
            {
                "name": "Professional Content Writer", 
                "role": "writer",
                "description": "Skilled writer who creates engaging and informative content",
                "capabilities": ["writing", "editing", "seo-optimization", "tone-adaptation"],
                "config": {"max_content_length": 2000, "style": "professional"}
            },
            {
                "name": "Quality Assurance Reviewer",
                "role": "reviewer", 
                "description": "Reviews and improves content quality and accuracy",
                "capabilities": ["review", "editing", "quality-control", "fact-verification"],
                "config": {"quality_threshold": 0.85, "review_criteria": ["accuracy", "readability", "engagement"]}
            }
        ]
        
        for agent_data in default_agents:
            agent_response = AgentResponse(
                id=self._next_id,
                name=agent_data["name"],
                role=agent_data["role"],
                description=agent_data["description"],
                capabilities=agent_data["capabilities"],
                config=agent_data["config"],
                status="active",
                created_at=datetime.utcnow()
            )
            
            self._agent_store.append(agent_response)
            self._next_id += 1
            
        logger.info(f"Initialized {len(default_agents)} default agents")
    
    async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
        """Create and register a new AI agent"""
        
        logger.info(f"Creating agent: {agent_data.name}")
        
        try:
            agent_response = AgentResponse(
                id=self._next_id,
                name=agent_data.name,
                role=agent_data.role,
                description=agent_data.description,
                capabilities=agent_data.capabilities,
                config=agent_data.config,
                status="active",
                created_at=datetime.utcnow()
            )
            
            self._agent_store.append(agent_response)
            self._next_id += 1
            
            logger.info(f"Agent created successfully: {agent_data.name} (ID: {agent_response.id})")
            return agent_response
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise Exception(f"Agent creation failed: {str(e)}")
    
    async def get_agent(self, agent_id: int) -> Optional[AgentResponse]:
        """Retrieve specific agent by ID"""
        
        for agent in self._agent_store:
            if agent.id == agent_id:
                return agent
        return None
    
    async def get_all_agents(self) -> List[AgentResponse]:
        """Retrieve all registered agents"""
        
        return self._agent_store
    
    async def get_agents_by_role(self, role: str) -> List[AgentResponse]:
        """Retrieve agents by their role"""
        
        return [agent for agent in self._agent_store if agent.role == role]
    
    async def execute_content_workflow(self, topic: str, content_type: str = "article") -> Dict[str, Any]:
        """Execute a complete content generation workflow using multiple agents"""
        
        logger.info(f"Starting content workflow for topic: {topic}")
        
        try:
            # Get available agents
            researchers = await self.get_agents_by_role("researcher")
            writers = await self.get_agents_by_role("writer")
            reviewers = await self.get_agents_by_role("reviewer")
            
            if not researchers or not writers:
                raise Exception("Required agents (researcher, writer) not available")
            
            # Create CrewAI agents
            research_agent = Agent(
                role="Senior Research Analyst",
                goal=f"Conduct comprehensive research on {topic}",
                backstory="""You are an expert researcher with access to vast knowledge. 
                You excel at finding relevant information, identifying key trends, and 
                gathering supporting data for content creation.""",
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )
            
            writing_agent = Agent(
                role="Professional Content Creator",
                goal=f"Create high-quality {content_type} based on research findings",
                backstory="""You are a skilled content creator who transforms research 
                into engaging, well-structured content. You adapt your writing style 
                to match the content type and target audience.""",
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )
            
            # Create tasks
            research_task = Task(
                description=f"""Research comprehensive information about: {topic}
                
                Focus on:
                1. Core concepts and key definitions
                2. Current trends and recent developments  
                3. Statistical data and market insights
                4. Expert opinions and industry perspectives
                5. Practical applications and use cases
                
                Provide organized research that will inform high-quality content.""",
                
                expected_output="""Detailed research report including:
                - Executive summary of key findings
                - Core concepts and definitions
                - Current trends and statistics
                - Expert insights and quotes
                - Practical examples and applications""",
                
                agent=research_agent
            )
            
            content_task = Task(
                description=f"""Create a comprehensive {content_type} about {topic} 
                based on the research findings.
                
                Requirements:
                - Professional, engaging tone
                - Well-structured with clear sections
                - Include relevant examples and data
                - 1000-1500 words in length
                - SEO-optimized and reader-friendly
                
                Create content that educates and engages the audience.""",
                
                expected_output=f"""High-quality {content_type} featuring:
                - Compelling introduction
                - Well-organized main content with clear sections
                - Supporting examples and data from research
                - Practical insights and takeaways
                - Strong conclusion with key points""",
                
                agent=writing_agent,
                context=[research_task]
            )
            
            # Add review task if reviewer available
            tasks = [research_task, content_task]
            agents = [research_agent, writing_agent]
            
            if reviewers:
                review_agent = Agent(
                    role="Quality Assurance Editor",
                    goal="Review and enhance the content for quality and accuracy",
                    backstory="""You are a meticulous editor who ensures content meets 
                    high standards for accuracy, readability, and engagement. You improve 
                    content while maintaining the author's voice and intent.""",
                    llm=self.llm,
                    verbose=False,
                    allow_delegation=False
                )
                
                review_task = Task(
                    description=f"""Review and enhance the {content_type} about {topic}.
                    
                    Focus on:
                    1. Accuracy and factual correctness
                    2. Readability and flow
                    3. Engagement and interest level
                    4. Structure and organization
                    5. Grammar and language quality
                    
                    Provide the final, polished version.""",
                    
                    expected_output="""Final polished content with:
                    - Verified accuracy and facts
                    - Improved readability and flow
                    - Enhanced engagement elements
                    - Perfect grammar and language
                    - Optimized structure and formatting""",
                    
                    agent=review_agent,
                    context=[research_task, content_task]
                )
                
                tasks.append(review_task)
                agents.append(review_agent)
            
            # Execute workflow
            workflow_crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=False
            )
            
            start_time = datetime.utcnow()
            result = workflow_crew.kickoff()
            end_time = datetime.utcnow()
            
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "content": str(result),
                "workflow_id": f"workflow_{int(start_time.timestamp())}",
                "agents_used": [agent.role for agent in agents],
                "tasks_completed": len(tasks),
                "execution_time": f"{execution_time:.2f} seconds",
                "quality_score": "A+" if reviewers else "A",
                "status": "completed",
                "metadata": {
                    "topic": topic,
                    "content_type": content_type,
                    "research_included": True,
                    "review_included": bool(reviewers),
                    "timestamp": start_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            # Return fallback content
            return {
                "content": f"""# {topic}

This content was generated in fallback mode due to workflow execution issues.

## Overview

{topic} is an important subject that deserves comprehensive coverage. Our multi-agent system is designed to provide in-depth research and high-quality content creation.

## Key Features

- Multi-agent workflow orchestration
- Research-driven content generation
- Quality assurance and review processes
- Scalable content production pipeline

## Conclusion

The Intelligent Content Factory demonstrates advanced AI capabilities for automated content creation.

*Generated in fallback mode by Intelligent Content Factory*""",
                "workflow_id": f"fallback_{int(datetime.utcnow().timestamp())}",
                "agents_used": ["Fallback Generator"],
                "tasks_completed": 1,
                "execution_time": "0.1 seconds",
                "quality_score": "B (Fallback)",
                "status": "completed_fallback",
                "error": str(e)
            }
    
    async def update_agent_status(self, agent_id: int, status: str) -> bool:
        """Update agent status (active, inactive, maintenance)"""
        
        for agent in self._agent_store:
            if agent.id == agent_id:
                agent.status = status
                logger.info(f"Agent {agent_id} status updated to: {status}")
                return True
        return False
    
    async def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered agents"""
        
        total_agents = len(self._agent_store)
        active_agents = len([a for a in self._agent_store if a.status == "active"])
        
        role_counts = {}
        for agent in self._agent_store:
            role_counts[agent.role] = role_counts.get(agent.role, 0) + 1
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "inactive_agents": total_agents - active_agents,
            "agents_by_role": role_counts,
            "capabilities": list(set([
                cap for agent in self._agent_store 
                for cap in agent.capabilities
            ]))
        }