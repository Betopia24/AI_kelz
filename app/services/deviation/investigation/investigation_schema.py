from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ImpactLevel(str, Enum):
    """Enumeration for impact assessment levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    NOT_SPECIFIED = "Not specified"

class DeviationTheme(str, Enum):
    """Enumeration for deviation themes."""
    MANUFACTURING = "Manufacturing"
    QUALITY_CONTROL = "Quality Control"
    DOCUMENTATION = "Documentation"
    EQUIPMENT = "Equipment"
    PERSONNEL = "Personnel"
    ENVIRONMENTAL = "Environmental"
    SUPPLIER = "Supplier"
    PACKAGING = "Packaging"
    VALIDATION = "Validation"
    OTHER = "Other"

class TriageStatus(str, Enum):
    """Enumeration for triage response options."""
    YES = "Yes"
    NO = "No"
    NOT_APPLICABLE = "Not applicable"

# NEW: Simple 3-field input schema
class SimpleInvestigationInput(BaseModel):
    """Schema for simple 3-field investigation input."""
    incident_description: str = Field(
        ..., 
        description="Description of the incident or deviation that occurred",
        min_length=1,
        max_length=5000
    )
    background_information: str = Field(
        ..., 
        description="Background context, circumstances, or additional details about the incident",
        min_length=1,
        max_length=5000
    )
    initial_observations: str = Field(
        ..., 
        description="Initial findings, observations, or immediate actions taken",
        min_length=1,
        max_length=5000
    )

    class Config:
        schema_extra = {
            "example": {
                "incident_description": "Temperature excursion observed in cold storage area between 14:00-16:00 on January 15th. Temperature monitoring system showed readings above 8°C specification limit reaching 12°C.",
                "background_information": "The cold storage area houses finished pharmaceutical products awaiting release. Normal operating temperature should be maintained between 2-8°C. The area was accessed twice during the morning shift for routine inventory checks.",
                "initial_observations": "HVAC system appeared to be running normally. No visible signs of equipment malfunction. Products in affected area have been quarantined pending investigation. Temperature logs show gradual increase starting at 13:45."
            }
        }

# Core Data Models for Investigation Structure

class BackgroundData(BaseModel):
    """Schema for background information."""
    summary: str = Field(..., description="Comprehensive background summary")
    deviation_details: str = Field(..., description="Detailed description of what occurred")

class DeviationTriageData(BaseModel):
    """Schema for deviation triage assessment data."""
    deviation_theme: str = Field("", description="Primary theme/category of the deviation")
    impact_assessment: ImpactLevel = Field(ImpactLevel.NOT_SPECIFIED, description="Overall impact assessment level")
    product_quality: ImpactLevel = Field(ImpactLevel.NOT_SPECIFIED, description="Impact on product quality")
    patient_safety: ImpactLevel = Field(ImpactLevel.NOT_SPECIFIED, description="Impact on patient safety")
    regulatory_impact: ImpactLevel = Field(ImpactLevel.NOT_SPECIFIED, description="Regulatory compliance impact")
    validation_impact: ImpactLevel = Field(ImpactLevel.NOT_SPECIFIED, description="Impact on validation status")
    criticality: ImpactLevel = Field(ImpactLevel.NOT_SPECIFIED, description="Overall criticality assessment")
    
    class Config:
        use_enum_values = True

class DeviationTriageAnalysis(BaseModel):
    """Schema for deviation triage analysis."""
    impact_level: str = Field(..., description="Overall impact assessment")
    priority: str = Field(..., description="Investigation priority level")
    resources_required: str = Field(..., description="Resources needed for investigation")

class DiscussionData(BaseModel):
    """Schema for investigation discussion section."""
    process: str = Field(..., description="Analysis of process-related factors")
    equipment: str = Field(..., description="Equipment-related analysis and failures")
    environment: str = Field(..., description="Environmental factors analysis")
    people: str = Field(..., description="Personnel-related factors and human error analysis")
    documentation_adequacy: str = Field(..., description="Assessment of documentation adequacy")

class FiveWhyAnalysis(BaseModel):
    """Schema for 5 Why analysis."""
    why_1: str = Field(..., description="First why - immediate cause")
    why_2: str = Field(..., description="Second why - underlying cause")
    why_3: str = Field(..., description="Third why - system cause")
    why_4: str = Field(..., description="Fourth why - organizational cause")
    why_5: str = Field(..., description="Fifth why - root cause")

class FishboneAnalysis(BaseModel):
    """Schema for Fishbone analysis."""
    method: str = Field(..., description="Method-related causes")
    machine: str = Field(..., description="Machine/equipment-related causes")
    material: str = Field(..., description="Material-related causes")
    measurement: str = Field(..., description="Measurement/monitoring-related causes")
    man: str = Field(..., description="Human-related causes")
    environment: str = Field(..., description="Environmental causes")

class FiveMsAnalysis(BaseModel):
    """Schema for 5M's analysis."""
    man: str = Field(..., description="Personnel competency and training issues")
    machine: str = Field(..., description="Equipment reliability and maintenance")
    material: str = Field(..., description="Raw material and component quality")
    method: str = Field(..., description="Process and procedure effectiveness")
    measurement: str = Field(..., description="Monitoring and control system adequacy")

class FMEAAnalysis(BaseModel):
    """Schema for FMEA analysis."""
    failure_modes: List[str] = Field(default_factory=list, description="Potential failure modes identified")
    effects: List[str] = Field(default_factory=list, description="Effects of each failure mode")
    causes: List[str] = Field(default_factory=list, description="Root causes for each failure mode")
    risk_priority: str = Field(..., description="Risk priority number assessment")

class RootCauseAnalysis(BaseModel):
    """Schema for comprehensive root cause analysis."""
    five_why: FiveWhyAnalysis = Field(..., description="5 Why analysis results")
    fishbone: FishboneAnalysis = Field(..., description="Fishbone diagram analysis")
    five_ms: FiveMsAnalysis = Field(..., description="5M's analysis results")
    fmea: FMEAAnalysis = Field(..., description="FMEA analysis results")

class FinalAssessment(BaseModel):
    """Schema for final assessment section."""
    patient_safety: str = Field(..., description="Patient safety impact assessment")
    product_quality: str = Field(..., description="Product quality impact evaluation")
    compliance_impact: str = Field(..., description="Regulatory compliance implications")
    validation_impact: str = Field(..., description="Impact on validation status")
    regulatory_impact: str = Field(..., description="Regulatory reporting requirements")

class HistoricReview(BaseModel):
    """Schema for historic review section."""
    previous_occurrence: str = Field(..., description="Analysis of previous occurrences")
    pattern_analysis: str = Field(..., description="Pattern identification from historical data")
    rca_adequacy_impact: str = Field(..., description="Impact on RCA adequacy")
    capa_adequacy_impact: str = Field(..., description="Impact on CAPA adequacy")

class CAPARecommendations(BaseModel):
    """Schema for CAPA recommendations section."""
    correction: str = Field(..., description="Immediate correction actions")
    interim_action: str = Field(..., description="Interim containment actions")
    corrective_action: str = Field(..., description="Systematic corrective actions")
    preventive_action: str = Field(..., description="Preventive actions")

class TranscriptionData(BaseModel):
    """Schema for transcription data."""
    original_transcription: str = Field(..., description="Original transcription from voice file")
    polished_transcription: str = Field(..., description="Polished/cleaned transcription")
    transcription_length: int = Field(..., description="Length of original transcription")

class InvestigationData(BaseModel):
    """Schema for complete investigation analysis data."""
    background: BackgroundData = Field(..., description="Background and deviation details")
    deviation_triage: DeviationTriageAnalysis = Field(..., description="Triage analysis")
    discussion: DiscussionData = Field(..., description="Investigation discussion details")
    root_cause_analysis: RootCauseAnalysis = Field(..., description="Comprehensive root cause analysis")
    final_assessment: FinalAssessment = Field(..., description="Final assessment and conclusions")
    historic_review: HistoricReview = Field(..., description="Historical review and pattern analysis")
    capa: CAPARecommendations = Field(..., description="CAPA recommendations")
    investigation_summary: str = Field(..., description="Concise investigation summary")

# Request Models

class InvestigationRequest(BaseModel):
    """Schema for text-based investigation processing request."""
    investigation_id: Optional[str] = Field(None, description="Unique investigation identifier")
    incident_description: str = Field(..., description="Description of the incident (text or transcribed)")
    background_details: str = Field("", description="Background details from deviation report")
    deviation_triage: Optional[DeviationTriageData] = Field(None, description="Triage assessment data")
    attachments: Optional[List[str]] = Field(None, description="List of attachment file paths")
    
    class Config:
        schema_extra = {
            "example": {
                "investigation_id": "INV-2024-001",
                "incident_description": "Temperature excursion observed in storage area during weekend shift. HVAC system malfunction caused temperature to rise above 25°C specification.",
                "background_details": "Product stored in controlled temperature environment showed temperature readings above specification",
                "deviation_triage": {
                    "deviation_theme": "Environmental",
                    "impact_assessment": "High",
                    "product_quality": "High",
                    "patient_safety": "Medium",
                    "regulatory_impact": "High",
                    "validation_impact": "Low",
                    "criticality": "High"
                },
                "attachments": ["path/to/temperature_log.pdf", "path/to/storage_procedure.docx"]
            }
        }

class VoiceInvestigationRequest(BaseModel):
    """Schema for voice-based investigation request (used for documentation)."""
    voice_file: str = Field(..., description="Voice file to be processed")
    background_details: str = Field("", description="Additional background information")
    deviation_triage: Optional[DeviationTriageData] = Field(None, description="Triage assessment data")
    attachments: Optional[List[str]] = Field(None, description="List of attachment file paths")

# Response Models

class SimpleInvestigationResponse(BaseModel):
    """Schema for simple investigation analysis response."""
    status: str = Field(..., description="Processing status (success/error)")
    investigation_analysis: InvestigationData = Field(..., description="Complete investigation analysis")
    input_summary: str = Field(..., description="Summary of the provided input fields")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    message: str = Field(..., description="Response message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "investigation_analysis": "... (complete investigation data structure)",
                "input_summary": "Temperature excursion incident in cold storage with HVAC-related observations",
                "processing_time": 35.8,
                "message": "Investigation analysis completed successfully"
            }
        }

class InvestigationResponse(BaseModel):
    """Schema for investigation processing response."""
    status: str = Field(..., description="Processing status (success/error)")
    investigation_id: str = Field(..., description="Unique investigation identifier")
    investigation_analysis: InvestigationData = Field(..., description="Complete investigation analysis")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    message: str = Field(..., description="Response message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "investigation_id": "INV-2024-001",
                "investigation_analysis": {
                    "background": {
                        "summary": "Temperature excursion in controlled storage area affecting pharmaceutical products",
                        "deviation_details": "HVAC system malfunction during weekend shift"
                    },
                    "discussion": {
                        "process": "Storage process followed correctly, environmental control failed",
                        "equipment": "HVAC system component failure identified",
                        "environment": "Temperature rose from 20°C to 28°C over 2-hour period",
                        "people": "Weekend staff followed proper escalation procedures",
                        "documentation_adequacy": "Temperature monitoring documented appropriately"
                    },
                    "root_cause_analysis": {
                        "five_why": {
                            "why_1": "Temperature exceeded specification limits",
                            "why_2": "HVAC system failed to maintain set temperature",
                            "why_3": "Cooling unit component malfunction occurred",
                            "why_4": "Preventive maintenance was overdue",
                            "why_5": "Maintenance scheduling system was inadequate"
                        }
                    },
                    "investigation_summary": "Temperature excursion in storage area due to HVAC failure. Product stored above acceptable limits."
                },
                "processing_time": 45.2,
                "message": "Investigation completed successfully"
            }
        }

class VoiceInvestigationResponse(BaseModel):
    """Schema for voice investigation response."""
    status: str = Field(..., description="Processing status")
    investigation_id: str = Field(..., description="Generated investigation ID")
    filename: str = Field(..., description="Original voice filename")
    transcription_data: TranscriptionData = Field(..., description="Transcription results")
    investigation_analysis: InvestigationData = Field(..., description="Complete investigation analysis")
    processing_time: Optional[float] = Field(None, description="Total processing time")
    message: str = Field(..., description="Response message")

class InvestigationSummaryResponse(BaseModel):
    """Schema for investigation summary response."""
    investigation_id: str = Field(..., description="Unique investigation identifier")
    status: str = Field(..., description="Investigation status")
    summary: str = Field(..., description="Brief investigation summary")
    background: str = Field(..., description="Background summary")
    root_cause: str = Field(..., description="Primary root cause identified")
    patient_safety_impact: str = Field(..., description="Patient safety impact")
    corrective_action: str = Field(..., description="Primary corrective action")
    preventive_action: str = Field(..., description="Primary preventive action")
    created_at: Optional[str] = Field(None, description="Investigation creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "investigation_id": "INV-2024-001",
                "status": "completed",
                "summary": "Temperature excursion in storage area due to HVAC system failure",
                "background": "Environmental control deviation in pharmaceutical storage facility",
                "root_cause": "Inadequate preventive maintenance scheduling system",
                "patient_safety_impact": "Low risk - products quarantined before distribution",
                "corrective_action": "HVAC system repair and immediate temperature validation",
                "preventive_action": "Enhanced preventive maintenance program implementation",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T14:45:00Z"
            }
        }

class ValidationResult(BaseModel):
    """Schema for triage validation results."""
    is_valid: bool = Field(..., description="Whether triage data is complete and valid")
    validation_issues: List[str] = Field(default_factory=list, description="List of validation issues found")
    recommendations: List[str] = Field(default_factory=list, description="Validation recommendations")
    risk_level: str = Field(..., description="Assessed risk level based on triage data")
    message: str = Field(..., description="Validation result message")
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "validation_issues": [],
                "recommendations": ["High-priority investigation recommended due to safety concerns"],
                "risk_level": "high",
                "message": "Triage validation completed successfully"
            }
        }

class BatchProcessingResult(BaseModel):
    """Schema for individual batch processing result."""
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status (success/error)")
    investigation_id: Optional[str] = Field(None, description="Generated investigation ID")
    summary: Optional[str] = Field(None, description="Brief summary if successful")
    transcription_length: Optional[int] = Field(None, description="Length of transcription")
    message: str = Field(..., description="Result message")

class BatchProcessingResponse(BaseModel):
    """Schema for batch processing response."""
    status: str = Field(..., description="Overall batch status")
    total_files: int = Field(..., description="Total number of files processed")
    successful: int = Field(..., description="Number of successful processes")
    failed: int = Field(..., description="Number of failed processes")
    results: List[BatchProcessingResult] = Field(..., description="Individual processing results")
    message: str = Field(..., description="Batch processing summary message")

class AttachmentInfo(BaseModel):
    """Schema for attachment information."""
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    content_preview: Optional[str] = Field(None, description="Preview of file content")
    extraction_status: str = Field(..., description="Text extraction status")

class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    message: str = Field(..., description="Health check message")

# Error response schemas

class InvestigationError(BaseModel):
    """Schema for investigation error responses."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    status: str = Field(default="error", description="Response status")
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "INVESTIGATION_PROCESSING_FAILED",
                "error_message": "Failed to process investigation due to missing required data",
                "details": {
                    "missing_fields": ["incident_description"],
                    "validation_errors": ["Triage data is incomplete"]
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "status": "error"
            }
        }

# Additional utility schemas

class InvestigationMetrics(BaseModel):
    """Schema for investigation performance metrics."""
    total_investigations: int = Field(..., description="Total number of investigations")
    completed_investigations: int = Field(..., description="Number of completed investigations")
    pending_investigations: int = Field(..., description="Number of pending investigations")
    average_processing_time: float = Field(..., description="Average processing time in seconds")
    high_risk_investigations: int = Field(..., description="Number of high-risk investigations")

class InvestigationFilter(BaseModel):
    """Schema for filtering investigation queries."""
    date_from: Optional[datetime] = Field(None, description="Filter investigations from this date")
    date_to: Optional[datetime] = Field(None, description="Filter investigations to this date")
    deviation_theme: Optional[DeviationTheme] = Field(None, description="Filter by deviation theme")
    criticality: Optional[ImpactLevel] = Field(None, description="Filter by criticality level")
    status: Optional[str] = Field(None, description="Filter by investigation status")
    responsible_party: Optional[str] = Field(None, description="Filter by responsible party")

class InvestigationUpdateRequest(BaseModel):
    """Schema for updating existing investigations."""
    investigation_id: str = Field(..., description="Investigation ID to update")
    updates: Dict[str, Any] = Field(..., description="Fields to update")
    update_reason: str = Field(..., description="Reason for the update")
    updated_by: str = Field(..., description="User making the update")

class InvestigationInput(BaseModel):
    voice_file_path: str = Field(..., description="Path to the voice file for investigation")

class SingleInvestigationInput(BaseModel):
    incident_1stpart: str = Field(..., description="First part of the incident description", min_length=1, max_length=5000)
    incident_2ndpart: str = Field(..., description="Second part of the incident description", min_length=1, max_length=5000)
    incident_full: str = Field(..., description="Full incident description", min_length=1, max_length=10000)
    is_attachment: bool = Field(False, description="Whether there is an attachment")

class SingleInvestigationResponse(BaseModel):
    status: str
    investigation_analysis: dict
    message: str