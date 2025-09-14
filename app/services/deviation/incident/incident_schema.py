#!/usr/bin/env python3
"""
Incident Schema Module
Consolidated Pydantic model for incident-related API requests and responses
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class IncidentAnalysis(BaseModel):
    """Detailed incident analysis fields"""
    title: Optional[str] = Field(None, description="AI-generated incident title")
    who: Optional[str] = Field(None, description="People involved in the incident")
    what: Optional[str] = Field(None, description="Description of what happened")
    where: Optional[str] = Field(None, description="Location where incident occurred")
    immediate_action: Optional[str] = Field(None, description="Actions taken immediately")
    quality_concerns: Optional[str] = Field(None, description="Quality-related concerns")
    quality_controls: Optional[str] = Field(None, description="Quality control measures")
    rca_tool: Optional[str] = Field(None, description="Recommended root cause analysis tool")
    expected_interim_action: Optional[str] = Field(None, description="Expected interim actions")
    capa: Optional[str] = Field(None, description="Corrective and Preventive Actions")

class IncidentRequest(BaseModel):
    """Request model for incident processing"""
    transcribed_text: str = Field(..., description="Transcribed text to analyze")

class IncidentResponse(BaseModel):
    """Response model for incident processing"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status or error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    transcription: Optional[str] = Field(None, description="Original transcribed text")
    incident_description: Optional[str] = Field(None, description="AI-generated incident description")
    headline: Optional[str] = Field(None, description="Succinct headline of incident")
    analysis: Optional[IncidentAnalysis] = Field(None, description="Detailed incident analysis")
    deviation_triage: Optional[str] = Field(None, description="Deviation triage (Yes/No)")
    product_quality: Optional[dict] = Field(None, description="Product quality impact (dict with yes_no/level)")
    patient_safety: Optional[dict] = Field(None, description="Patient safety impact (dict with yes_no/level)")
    regulatory_impact: Optional[dict] = Field(None, description="Regulatory impact (dict with yes_no/level)")
    validation_impact: Optional[str] = Field(None, description="Validation impact (Yes/No)")
    customer_notification: Optional[str] = Field(None, description="Customer notification (Yes/No)")
    review_qta: Optional[str] = Field(None, description="Review QTA string")
    criticality: Optional[str] = Field(None, description="Criticality (Minor/Major)")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Incident processed successfully",
                "headline": "Equipment failure in production line",
                "timestamp": "2024-01-15T10:30:00"
            }
        }
    )

class IncidentSummaryResponse(BaseModel):
    """Response model for incident summary"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status or error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    summary: Optional[str] = Field(None, description="Brief incident summary")
    headline: Optional[str] = Field(None, description="Succinct headline of incident")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class FileUploadResponse(BaseModel):
    """Response model for file uploads"""
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Status or error message")
    filename: Optional[str] = Field(None, description="Name of uploaded file")
    file_size: Optional[int] = Field(None, description="Size of uploaded file in bytes")

class ErrorResponse(BaseModel):
    """Error response model"""
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")

# Legacy schema for backward compatibility
class IncidentSchema(BaseModel):
    """Unified schema for all incident-related operations (Legacy)"""
    
    # Common fields
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status or error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    
    # Request fields
    transcribed_text: Optional[str] = Field(None, description="Transcribed text to analyze")
    
    # Response fields
    transcription: Optional[str] = Field(None, description="Original transcribed text")
    incident_description: Optional[str] = Field(None, description="AI-generated incident description")
    headline: Optional[str] = Field(None, description="Succinct headline of incident")
    summary: Optional[str] = Field(None, description="Brief incident summary")
    
    # Analysis fields
    title: Optional[str] = Field(None, description="AI-generated incident title")
    who: Optional[str] = Field(None, description="People involved in the incident")
    what: Optional[str] = Field(None, description="Description of what happened")
    where: Optional[str] = Field(None, description="Location where incident occurred")
    immediate_action: Optional[str] = Field(None, description="Actions taken immediately")
    quality_concerns: Optional[str] = Field(None, description="Quality-related concerns")
    quality_controls: Optional[str] = Field(None, description="Quality control measures")
    rca_tool: Optional[str] = Field(None, description="Recommended root cause analysis tool")
    expected_interim_action: Optional[str] = Field(None, description="Expected interim actions")
    capa: Optional[str] = Field(None, description="Corrective and Preventive Actions")
    analysis: Optional[IncidentAnalysis] = Field(None, description="Detailed incident analysis")
    
    # File upload fields
    filename: Optional[str] = Field(None, description="Name of uploaded file")
    file_size: Optional[int] = Field(None, description="Size of uploaded file in bytes")
    
    # Error fields
    error_type: Optional[str] = Field(None, description="Type of error")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Incident processed successfully",
                "headline": "Equipment failure in production line",
                "summary": "Brief description of the incident",
                "timestamp": "2024-01-15T10:30:00"
            }
        }
    )