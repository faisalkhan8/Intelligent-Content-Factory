"""
Data Models and Schemas for Intelligent Content Factory
======================================================

Pydantic models for API request/response serialization
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

# Content Models
class ContentCreate(BaseModel):
    """Schema for creating new content"""
    title: str = Field(..., description="Content title", min_length=1, max_length=200)
    content: str = Field(..., description="Content body", min_length=1, max_length=10000)
    content_type: str = Field(default="article", description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class ContentResponse(BaseModel):
    """Schema for content API responses"""
    id: int = Field(..., description="Unique content identifier")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Content body")
    content_type: str = Field(..., description="Type of content")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True

# Agent Models
class AgentCreate(BaseModel):
    """Schema for creating new agents"""
    name: str = Field(..., description="Agent name", min_length=1, max_length=100)
    role: str = Field(..., description="Agent role", min_length=1, max_length=50)
    description: str = Field(..., description="Agent description", max_length=500)
    capabilities: List[str] = Field(default=[], description="Agent capabilities")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Agent configuration")

class AgentResponse(BaseModel):
    """Schema for agent API responses"""
    id: int = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    description: str = Field(..., description="Agent description")
    capabilities: List[str] = Field(default=[], description="Agent capabilities")
    config: Dict[str, Any] = Field(default={}, description="Agent configuration")
    status: str = Field(default="active", description="Agent status")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True

# Workflow Models
class WorkflowRequest(BaseModel):
    """Schema for workflow execution requests"""
    topic: str = Field(..., description="Content topic", min_length=1, max_length=200)
    content_type: str = Field(default="article", description="Desired content type")
    requirements: Optional[Dict[str, Any]] = Field(default={}, description="Special requirements")
    agents: Optional[List[str]] = Field(default=[], description="Specific agents to use")

class WorkflowResponse(BaseModel):
    """Schema for workflow execution responses"""
    id: str = Field(..., description="Workflow execution ID")
    status: str = Field(..., description="Workflow status")
    result: Optional[Dict[str, Any]] = Field(None, description="Workflow result")
    started_at: datetime = Field(..., description="Workflow start time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    agents_used: List[str] = Field(default=[], description="Agents that participated")

# Health Check Models
class HealthResponse(BaseModel):
    """Schema for health check responses"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Health check timestamp")

# Metrics Models
class MetricsResponse(BaseModel):
    """Schema for system metrics responses"""
    status: str = Field(..., description="System operational status")
    active_agents: int = Field(..., description="Number of active agents")
    total_content_generated: int = Field(..., description="Total content items generated")
    average_generation_time: str = Field(..., description="Average content generation time")
    success_rate: str = Field(..., description="System success rate percentage")
    uptime: str = Field(..., description="System uptime percentage")

# Error Models
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    path: Optional[str] = Field(None, description="API path where error occurred")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")