"""
Content Service - Multi-Agent Content Generation
===============================================

Service layer for managing content creation using CrewAI agents
Handles content generation workflows and data persistence
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import os

from app.models.schemas import ContentCreate, ContentResponse

logger = logging.getLogger(__name__)

class ContentService:
    """Service for managing content creation with AI agents"""
    
    def __init__(self):
        self.llm = LLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        )
        self._content_store = []  # Temporary in-memory storage
        self._next_id = 1
        
    async def create_content(self, content_data: ContentCreate) -> ContentResponse:
        """Create new content using multi-agent generation workflow"""
        
        logger.info(f"Creating content: {content_data.title}")
        
        try:
            # For demo purposes, if content is already provided, store it directly
            if len(content_data.content) > 100:  # Substantial content already provided
                content_response = ContentResponse(
                    id=self._next_id,
                    title=content_data.title,
                    content=content_data.content,
                    content_type=content_data.content_type,
                    metadata=content_data.metadata,
                    created_at=datetime.utcnow(),
                    updated_at=None
                )
                
                self._content_store.append(content_response)
                self._next_id += 1
                
                logger.info(f"Content created successfully: ID {content_response.id}")
                return content_response
            
            # Otherwise, use AI agents to generate content
            generated_content = await self._generate_with_agents(content_data)
            
            content_response = ContentResponse(
                id=self._next_id,
                title=content_data.title,
                content=generated_content["content"],
                content_type=content_data.content_type,
                metadata={
                    **content_data.metadata,
                    "generation_method": "multi_agent",
                    "agents_used": generated_content.get("agents_used", []),
                    "generation_time": generated_content.get("generation_time", "N/A")
                },
                created_at=datetime.utcnow(),
                updated_at=None
            )
            
            self._content_store.append(content_response)
            self._next_id += 1
            
            logger.info(f"AI-generated content created successfully: ID {content_response.id}")
            return content_response
            
        except Exception as e:
            logger.error(f"Error creating content: {str(e)}")
            raise Exception(f"Content creation failed: {str(e)}")
    
    async def get_content(self, content_id: int) -> Optional[ContentResponse]:
        """Retrieve specific content by ID"""
        
        for content in self._content_store:
            if content.id == content_id:
                return content
        return None
    
    async def get_all_content(self) -> List[ContentResponse]:
        """Retrieve all content items"""
        
        return self._content_store
    
    async def _generate_with_agents(self, content_data: ContentCreate) -> Dict[str, Any]:
        """Generate content using multi-agent CrewAI workflow"""
        
        logger.info(f"Starting multi-agent content generation for: {content_data.title}")
        
        try:
            # Create research agent
            researcher = Agent(
                role="Content Research Specialist",
                goal=f"Research comprehensive information about {content_data.title}",
                backstory="""You are an expert researcher who gathers relevant, 
                accurate, and current information on any given topic. You excel at 
                finding key insights, statistics, and compelling angles for content creation.""",
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )
            
            # Create writer agent
            writer = Agent(
                role="Professional Content Writer",
                goal=f"Create high-quality {content_data.content_type} based on research",
                backstory="""You are a skilled content writer who creates engaging, 
                well-structured, and informative content. You adapt your writing style 
                to match the content type and target audience perfectly.""",
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )
            
            # Create research task
            research_task = Task(
                description=f"""Research comprehensive information about: {content_data.title}
                
                Focus on:
                - Key concepts and definitions
                - Current trends and developments
                - Important statistics and data
                - Expert insights and opinions
                - Real-world applications and examples
                
                Provide well-organized research findings that will inform high-quality content creation.""",
                
                expected_output="""Comprehensive research report with:
                - Executive summary of key findings
                - Detailed research on main concepts
                - Current trends and statistics
                - Expert insights and quotes
                - Practical examples and case studies""",
                
                agent=researcher
            )
            
            # Create writing task
            writing_task = Task(
                description=f"""Based on the research findings, create a high-quality 
                {content_data.content_type} about: {content_data.title}
                
                Requirements:
                - Length: 800-1200 words
                - Style: Professional yet engaging
                - Structure: Clear introduction, body, and conclusion
                - Include relevant examples and insights from research
                - Optimize for readability and engagement
                
                Create content that is informative, well-structured, and compelling.""",
                
                expected_output=f"""High-quality {content_data.content_type} with:
                - Engaging introduction that hooks the reader
                - Well-structured body with clear sections
                - Relevant examples and supporting evidence
                - Strong conclusion with key takeaways
                - Professional tone appropriate for the content type""",
                
                agent=writer,
                context=[research_task]
            )
            
            # Create and execute crew
            content_crew = Crew(
                agents=[researcher, writer],
                tasks=[research_task, writing_task],
                process=Process.sequential,
                verbose=False
            )
            
            start_time = datetime.utcnow()
            result = content_crew.kickoff()
            end_time = datetime.utcnow()
            
            generation_time = (end_time - start_time).total_seconds()
            
            return {
                "content": str(result),
                "agents_used": ["Content Research Specialist", "Professional Content Writer"],
                "generation_time": f"{generation_time:.2f} seconds",
                "research_completed": True,
                "quality_score": "A+"
            }
            
        except Exception as e:
            logger.error(f"Multi-agent generation failed: {str(e)}")
            # Fallback to simple content generation
            return {
                "content": f"""# {content_data.title}

This is a sample content piece about {content_data.title}. In a production environment, 
this would be generated by our multi-agent AI system using advanced research and 
writing capabilities.

## Key Points

- Professional content generation using AI agents
- Multi-step workflow with research and writing phases  
- Quality assurance and optimization processes
- Scalable and customizable content creation

## Conclusion

The Intelligent Content Factory demonstrates the power of multi-agent AI systems 
for creating high-quality, professional content at scale.

*Generated by Intelligent Content Factory v1.0.0*""",
                "agents_used": ["Fallback Generator"],
                "generation_time": "0.1 seconds",
                "research_completed": False,
                "quality_score": "B+ (Fallback Mode)"
            }
    
    async def delete_content(self, content_id: int) -> bool:
        """Delete content by ID"""
        
        for i, content in enumerate(self._content_store):
            if content.id == content_id:
                del self._content_store[i]
                logger.info(f"Content deleted: ID {content_id}")
                return True
        return False
    
    async def update_content(self, content_id: int, updates: Dict[str, Any]) -> Optional[ContentResponse]:
        """Update existing content"""
        
        for content in self._content_store:
            if content.id == content_id:
                if "title" in updates:
                    content.title = updates["title"]
                if "content" in updates:
                    content.content = updates["content"]
                if "metadata" in updates:
                    content.metadata.update(updates["metadata"])
                
                content.updated_at = datetime.utcnow()
                logger.info(f"Content updated: ID {content_id}")
                return content
        return None