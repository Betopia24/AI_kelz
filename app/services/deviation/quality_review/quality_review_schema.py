#!/usr/bin/env python3
"""
Quality Review Schema Definitions
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

# Base response models
class BaseResponse(BaseModel):
    status: str = Field(..., description="Response status (success, warning, error)")
    message: str = Field(..., description="Response message")

class ErrorResponse(BaseResponse):
    error: str = Field(..., description="Error description")
    status: str = Field(default="error", description="Error status")

# Transcription models
class TranscriptionData(BaseModel):
    original: str = Field(..., description="Original transcribed text")
    polished: str = Field(..., description="Polished transcription (if available)")
    length: int = Field(..., description="Length of transcription in characters")

# Quality Review models
class InvestigationCompleteness(BaseModel):
    investigation_status: Optional[str] = Field(None, description="Complete/Incomplete/Partially Complete")
    completeness_score: Optional[str] = Field(None, description="Completeness score (1-10)")
    missing_elements: Optional[str] = Field(None, description="Missing investigation elements")
    adequacy_assessment: Optional[str] = Field(None, description="Assessment of investigation thoroughness")

class RootCauseAnalysis(BaseModel):
    root_cause_identified: Optional[str] = Field(None, description="Yes/No/Partially")
    root_cause_quality: Optional[str] = Field(None, description="Adequate/Inadequate/Needs Enhancement")
    analysis_method_used: Optional[str] = Field(None, description="RCA method identified")
    depth_of_analysis: Optional[str] = Field(None, description="Shallow/Moderate/Comprehensive")
    root_cause_statement: Optional[str] = Field(None, description="Root cause statement")

class CapaAssessment(BaseModel):
    capa_actions_identified: Optional[str] = Field(None, description="Yes/No/Partially")
    capa_adequacy: Optional[str] = Field(None, description="Adequate/Inadequate/Needs Enhancement")
    prevention_focus: Optional[str] = Field(None, description="Strong/Moderate/Weak")
    corrective_actions: Optional[str] = Field(None, description="Corrective actions mentioned")
    preventive_actions: Optional[str] = Field(None, description="Preventive actions mentioned")
    capa_effectiveness_potential: Optional[str] = Field(None, description="High/Medium/Low")

class RiskEvaluation(BaseModel):
    risks_discussed: Optional[str] = Field(None, description="Yes/No/Partially")
    risk_assessment_quality: Optional[str] = Field(None, description="Comprehensive/Moderate/Limited")
    risk_mitigation: Optional[str] = Field(None, description="Adequate/Inadequate/Not Addressed")
    identified_risks: Optional[str] = Field(None, description="Risks mentioned in investigation")
    mitigation_strategies: Optional[str] = Field(None, description="Mitigation strategies discussed")

class QualityConcerns(BaseModel):
    product_impact: Optional[str] = Field(None, description="Assessed/Not Assessed/Unclear")
    patient_safety: Optional[str] = Field(None, description="Considered/Not Considered/Unclear")
    regulatory_compliance: Optional[str] = Field(None, description="Addressed/Not Addressed/Unclear")
    quality_system_impact: Optional[str] = Field(None, description="Evaluated/Not Evaluated/Unclear")

class QualityRecommendations(BaseModel):
    quality_reviewer_actions: Optional[str] = Field(None, description="Specific actions needed")
    follow_up_required: Optional[str] = Field(None, description="Follow-up activities needed")
    additional_investigation: Optional[str] = Field(None, description="Additional investigation needed")
    documentation_requirements: Optional[str] = Field(None, description="Additional documentation needed")

class QualityReviewData(BaseModel):
    overall_assessment: str = Field(..., description="Overall quality review assessment")
    investigation_completeness: Dict[str, Any] = Field(default_factory=dict, description="Investigation completeness data")
    root_cause_analysis: Dict[str, Any] = Field(default_factory=dict, description="Root cause analysis data")
    capa_assessment: Dict[str, Any] = Field(default_factory=dict, description="CAPA assessment data")
    risk_evaluation: Dict[str, Any] = Field(default_factory=dict, description="Risk evaluation data")
    quality_concerns: Dict[str, Any] = Field(default_factory=dict, description="Quality concerns data")
    recommendations: Dict[str, Any] = Field(default_factory=dict, description="Quality recommendations")

# SME Review models
class TechnicalInvestigationReview(BaseModel):
    investigation_methodology: Optional[str] = Field(None, description="Appropriate/Inappropriate/Needs Enhancement")
    technical_depth: Optional[str] = Field(None, description="Comprehensive/Moderate/Insufficient")
    scientific_approach: Optional[str] = Field(None, description="Sound/Questionable/Flawed")
    data_analysis_quality: Optional[str] = Field(None, description="Thorough/Adequate/Inadequate")
    investigation_scope: Optional[str] = Field(None, description="Complete/Incomplete/Needs Expansion")

class TechnicalRootCauseAssessment(BaseModel):
    root_cause_technical_validity: Optional[str] = Field(None, description="Valid/Questionable/Invalid")
    technical_evidence_supporting_rca: Optional[str] = Field(None, description="Strong/Moderate/Weak")
    scientific_method_application: Optional[str] = Field(None, description="Proper/Improper/Unclear")
    technical_analysis_tools_used: Optional[str] = Field(None, description="Tools/methods identified")
    alternative_causes_considered: Optional[str] = Field(None, description="Yes/No/Partially")

class TechnicalCapaEvaluation(BaseModel):
    technical_feasibility: Optional[str] = Field(None, description="High/Medium/Low")
    implementation_complexity: Optional[str] = Field(None, description="Simple/Moderate/Complex")
    technical_resource_requirements: Optional[str] = Field(None, description="Identified/Not Identified/Unclear")
    technology_process_changes: Optional[str] = Field(None, description="Appropriate/Inappropriate/Unclear")
    technical_risk_of_capa_implementation: Optional[str] = Field(None, description="Low/Medium/High")

class ProcessAndSystemAnalysis(BaseModel):
    process_understanding: Optional[str] = Field(None, description="Demonstrated/Limited/Not Demonstrated")
    system_knowledge: Optional[str] = Field(None, description="Comprehensive/Adequate/Inadequate")
    equipment_considerations: Optional[str] = Field(None, description="Addressed/Not Addressed/Unclear")
    technology_factors: Optional[str] = Field(None, description="Considered/Not Considered/Unclear")
    process_interaction_effects: Optional[str] = Field(None, description="Evaluated/Not Evaluated/Unclear")

class TechnicalRiskAssessment(BaseModel):
    technical_risk_identification: Optional[str] = Field(None, description="Comprehensive/Partial/Inadequate")
    process_risk_evaluation: Optional[str] = Field(None, description="Thorough/Moderate/Limited")
    system_risk_analysis: Optional[str] = Field(None, description="Complete/Incomplete/Not Performed")
    technical_risk_mitigation: Optional[str] = Field(None, description="Effective/Moderate/Ineffective")
    cross_functional_impact: Optional[str] = Field(None, description="Assessed/Not Assessed/Unclear")

class SmeTechnicalRecommendations(BaseModel):
    technical_improvements_needed: Optional[str] = Field(None, description="Specific technical recommendations")
    additional_technical_investigation: Optional[str] = Field(None, description="Required/Not Required/Conditional")
    expert_consultation_needed: Optional[str] = Field(None, description="Expert consultation areas")
    technical_validation_required: Optional[str] = Field(None, description="Validation activities needed")
    process_system_modifications: Optional[str] = Field(None, description="Recommended modifications")

class SmeReviewData(BaseModel):
    sme_overall_assessment: str = Field(..., description="Overall SME assessment")
    technical_investigation_review: Dict[str, Any] = Field(default_factory=dict, description="Technical investigation review")
    technical_root_cause_assessment: Dict[str, Any] = Field(default_factory=dict, description="Technical root cause assessment")
    technical_capa_evaluation: Dict[str, Any] = Field(default_factory=dict, description="Technical CAPA evaluation")
    process_and_system_analysis: Dict[str, Any] = Field(default_factory=dict, description="Process and system analysis")
    technical_risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Technical risk assessment")
    sme_technical_recommendations: Dict[str, Any] = Field(default_factory=dict, description="SME technical recommendations")

# Document Summary models
class DocumentSummaryData(BaseModel):
    document_type: Optional[str] = Field(None, description="Type of document identified")
    executive_summary: Optional[str] = Field(None, description="High-level summary")
    key_findings: Optional[List[str]] = Field(None, description="Main findings from document")
    main_sections: Optional[List[str]] = Field(None, description="Main sections covered")
    important_details: Optional[List[str]] = Field(None, description="Important details extracted")
    action_items: Optional[List[str]] = Field(None, description="Action items mentioned")
    quality_relevance: Optional[str] = Field(None, description="Relevance to quality systems")
    regulatory_implications: Optional[str] = Field(None, description="Regulatory implications")

# Response models
class VoiceQualityReviewResponse(BaseResponse):
    filename: str = Field(..., description="Uploaded audio filename")
    transcription: TranscriptionData = Field(..., description="Transcription data")
    quality_review: QualityReviewData = Field(..., description="Quality review analysis")
    sme_review: SmeReviewData = Field(..., description="SME review analysis")

class DocumentSummaryResponse(BaseResponse):
    filename: str = Field(..., description="Uploaded document filename")
    extracted_text: str = Field(..., description="Text extracted from document")
    text_length: int = Field(..., description="Length of extracted text")
    summary: str = Field(..., description="AI-generated document summary")

class CombinedQualityReviewResponse(BaseResponse):
    audio_filename: str = Field(..., description="Uploaded audio filename")
    document_filename: str = Field(..., description="Uploaded document filename")
    voice_analysis: Dict[str, Any] = Field(..., description="Voice analysis results")
    document_analysis: Dict[str, Any] = Field(..., description="Document analysis results")

# Request models (if needed for future endpoints)
class QualityReviewRequest(BaseModel):
    investigation_id: Optional[str] = Field(None, description="Investigation ID for reference")
    review_type: str = Field(..., description="Type of review (quality, sme, combined)")
    priority: Optional[str] = Field("medium", description="Review priority (low, medium, high)")
    due_date: Optional[datetime] = Field(None, description="Review due date")

class QualityAssessmentRequest(BaseModel):
    content: str = Field(..., description="Content to assess")
    assessment_type: Optional[str] = Field("standard", description="Type of assessment")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")

# Template models
class QualityReviewChecklist(BaseModel):
    investigation_completeness: List[str] = Field(..., description="Investigation completeness checklist")
    root_cause_analysis: List[str] = Field(..., description="Root cause analysis checklist")
    capa_assessment: List[str] = Field(..., description="CAPA assessment checklist")
    risk_evaluation: List[str] = Field(..., description="Risk evaluation checklist")

class SmeReviewChecklist(BaseModel):
    technical_assessment: List[str] = Field(..., description="Technical assessment checklist")
    process_evaluation: List[str] = Field(..., description="Process evaluation checklist")

class ReviewGuidelines(BaseModel):
    quality_reviewer_focus: List[str] = Field(..., description="Quality reviewer focus areas")
    sme_reviewer_focus: List[str] = Field(..., description="SME reviewer focus areas")

class ReviewTemplates(BaseModel):
    quality_review_checklist: QualityReviewChecklist = Field(..., description="Quality review checklist")
    sme_review_checklist: SmeReviewChecklist = Field(..., description="SME review checklist")
    review_guidelines: ReviewGuidelines = Field(..., description="Review guidelines")

class ReviewTemplatesResponse(BaseResponse):
    templates: ReviewTemplates = Field(..., description="Quality review templates")

# File format models
class AudioFormats(BaseModel):
    supported_types: List[str] = Field(..., description="Supported MIME types")
    extensions: List[str] = Field(..., description="Supported file extensions")
    max_size: str = Field(..., description="Maximum file size")
    notes: str = Field(..., description="Additional notes")

class DocumentFormats(BaseModel):
    directly_supported: List[str] = Field(..., description="Directly supported formats")
    convertible_formats: List[str] = Field(..., description="Convertible formats")
    max_size: str = Field(..., description="Maximum file size or page limit")
    notes: str = Field(..., description="Additional notes")

class SupportedFormats(BaseModel):
    audio_formats: AudioFormats = Field(..., description="Supported audio formats")
    document_formats: DocumentFormats = Field(..., description="Supported document formats")

class SupportedFormatsResponse(BaseResponse):
    supported_formats: SupportedFormats = Field(..., description="Supported file formats")

# Health check models
class ServiceHealth(BaseModel):
    transcription_service: str = Field(..., description="Transcription service status")
    ai_analysis_service: str = Field(..., description="AI analysis service status")
    document_ocr_service: str = Field(..., description="Document OCR service status")
    overall_status: str = Field(..., description="Overall system status")

class HealthCheckResponse(BaseResponse):
    health: ServiceHealth = Field(..., description="Service health status")

# Configuration for Pydantic models
class Config:
    json_encoders = {
        datetime: lambda v: v.isoformat()
    }
    schema_extra = {
        "example": {
            "status": "success",
            "message": "Operation completed successfully"
        }
    }