#!/usr/bin/env python3
"""
Impact Assessment Service
Encapsulates OCR extraction, prompt building, AI invocation, and strict output formatting.
"""
from __future__ import annotations

import os
import json
import tempfile
from typing import Optional, List

from app.services.utils.document_ocr import DocumentOCR
from app.services.utils.ai_analysis import AIAnalyzer


class ImpactAssessmentManager:
    """
    Manager to generate the impact assessment fields using prior analysis text and optional OCR text.

    Produces exactly eight lines, in this order:
      DEVIATION_TRIAGE:
      PRODUCT_QUALITY:
      PATIENT_SAFETY:
      REGULATORY_IMPACT:
      VALIDATION_IMPACT:
      CUSTOMER_NOTIFICATION:
      REVIEW_QTA:
      CRITICALITY:
    """

    def __init__(self) -> None:
        self.ocr = DocumentOCR()
        self.analyzer = AIAnalyzer()

    # --------------- Public API ---------------
    def extract_text_from_document(self, file_content: bytes, filename: str) -> Optional[str]:
        """Extract text from uploaded document using DocumentOCR."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        try:
            text = self.ocr.process_file(tmp_path)
            return (text or '').strip() or None
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def generate_assessment_text(self, analysis_input: str, extracted_text: Optional[str]) -> str:
        """
        Build the AI prompt from provided context and return a strict 8-line assessment
        with sensible defaults if AI output is incomplete.
        """
        prior_text = self._normalize_prior_analysis(analysis_input)
        prompt = self._build_prompt(prior_text, extracted_text)
        ai_out = self.analyzer.analyze_with_prompt(prompt)
        return self._coerce_output(ai_out)

    # --------------- Internal Helpers ---------------
    def _normalize_prior_analysis(self, analysis_input: str) -> str:
        prior_text = (analysis_input or '').strip()
        if not prior_text:
            return ''
        # If JSON, pretty-print essential parts for context
        try:
            parsed = json.loads(prior_text)
            if isinstance(parsed, dict):
                keys_of_interest: List[str] = [
                    'INCIDENT_TITLE', 'WHO', 'WHAT', 'WHERE', 'IMMEDIATE_ACTION', 'QUALITY_CONCERNS',
                    'QUALITY_CONTROLS', 'RCA_TOOL', 'EXPECTED_INTERIM_ACTION', 'CAPA', 'ATTENDEES'
                ]
                block_lines: List[str] = []
                for k in keys_of_interest:
                    v = parsed.get(k)
                    if v is None:
                        v = parsed.get(k.lower())
                    if v is None:
                        v = parsed.get(k.lower().replace(' ', '_'))
                    if v is not None and isinstance(v, (dict, list)):
                        try:
                            v = json.dumps(v)
                        except Exception:
                            v = str(v)
                    if v is not None:
                        block_lines.append(f"{k}: {str(v)}")
                if block_lines:
                    prior_text = "\n".join(block_lines)
        except Exception:
            # Not JSON; assume it's strict prior analysis text already
            pass
        return prior_text

    def _build_prompt(self, prior_analysis: str, doc_text: Optional[str]) -> str:
        context_parts = []
        pa = (prior_analysis or '').strip()
        if pa:
            context_parts.append("PRIOR INCIDENT ANALYSIS (from /incident/analyze/audio):\n" + pa)
        if doc_text:
            context_parts.append("EXTRACTED DOCUMENT TEXT (OCR):\n" + doc_text)
        context = "\n\n".join(context_parts)

        prompt = f"""
INSTRUCTIONS:
- You are performing an impact assessment for a deviation/incident.
- Use the provided context (prior incident analysis and extracted document text) to COMPLETE ALL FIELDS BELOW.
- For each field, especially DEVIATION_TRIAGE, use your best expert judgment based on the context. Do NOT default to 'No' unless there is clear evidence. If the context suggests a possible triage, answer 'Yes' and justify in the related fields.
- ALWAYS make a best-guess assessment based on your analysis. Do NOT leave any field blank or as "Not specified".
- Use the JSON format for PRODUCT_QUALITY, PATIENT_SAFETY, and REGULATORY_IMPACT.
- Respond ONLY with the following 8 lines, exactly in this order, one line per field. No extra lines, no headers, no explanations.

DEVIATION_TRIAGE: [Yes or No]
PRODUCT_QUALITY: [If Yes, JSON: {{"yes_no": "Yes", "level": "High/Medium/Low"}}; if No, {{"yes_no": "No", "level": null}}]
PATIENT_SAFETY: [Same format as PRODUCT_QUALITY]
REGULATORY_IMPACT: [Same format as PRODUCT_QUALITY]
VALIDATION_IMPACT: [Yes or No]
CUSTOMER_NOTIFICATION: [Yes or No]
REVIEW_QTA: [Summary about QTA/customer notification]
CRITICALITY: [Minor or Major]

CONTEXT:
{context}
"""
        return prompt

    def _coerce_output(self, text: str) -> str:
        """Ensure output strictly contains 8 lines in the required format; fix common deviations."""
        if not text:
            return self._default_output()
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        # Filter out any accidental headers/footers
        lines = [l for l in lines if not l.upper().startswith("===")]
        # Try to map fields by prefix
        expected = [
            'DEVIATION_TRIAGE:',
            'PRODUCT_QUALITY:',
            'PATIENT_SAFETY:',
            'REGULATORY_IMPACT:',
            'VALIDATION_IMPACT:',
            'CUSTOMER_NOTIFICATION:',
            'REVIEW_QTA:',
            'CRITICALITY:'
        ]
        mapped = {}
        for l in lines:
            for key in expected:
                if l.upper().startswith(key):
                    mapped[key] = l[len(key):].strip()
                    break
        # Build final lines with defaults if missing
        out = []
        for key in expected:
            val = (mapped.get(key) or '').strip()
            if not val or val.lower() == 'not specified':
                val = self._default_value_for(key)
            out.append(f"{key} {val}")
        return "\n".join(out)

    def _default_output(self) -> str:
        fields = [
            ("DEVIATION_TRIAGE:", "No"),
            ("PRODUCT_QUALITY:", '{"yes_no": "No", "level": null}'),
            ("PATIENT_SAFETY:", '{"yes_no": "No", "level": null}'),
            ("REGULATORY_IMPACT:", '{"yes_no": "No", "level": null}'),
            ("VALIDATION_IMPACT:", "No"),
            ("CUSTOMER_NOTIFICATION:", "No"),
            ("REVIEW_QTA:", "Based on available information, QTA review not required."),
            ("CRITICALITY:", "Minor"),
        ]
        return "\n".join([f"{k} {v}" for k, v in fields])

    def _default_value_for(self, key: str) -> str:
        if key == 'DEVIATION_TRIAGE:':
            return 'No'
        if key in ('PRODUCT_QUALITY:', 'PATIENT_SAFETY:', 'REGULATORY_IMPACT:'):
            return '{"yes_no": "No", "level": null}'
        if key == 'VALIDATION_IMPACT:':
            return 'No'
        if key == 'CUSTOMER_NOTIFICATION:':
            return 'No'
        if key == 'REVIEW_QTA:':
            return 'Based on available information, QTA review not required.'
        if key == 'CRITICALITY:':
            return 'Minor'
        return ''
