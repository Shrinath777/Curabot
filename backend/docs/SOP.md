# CuraBot Medical Diagnostic SOPs (Standard Operating Procedures)

These protocols define the mandatory diagnostic workflow for all Aura AI agents to ensure clinical reliability, consistency, and safety.

## SOP-001: Emergency Triage & Red Flag screening
**Objective**: Immediately identify life-threatening conditions before proceeding with detailed history.
- **Protocol**: If the patient mentions chest pain, severe dyspnea, sudden neurological deficit, or massive bleeding, the agent must prioritize "Must-Not-Miss" diagnoses (MI, PE, Stroke).
- **Mandatory Action**: Check for red flags (diaphoresis, syncope, SpO2 < 92%) in the first 2 iterations.

## SOP-002: Evidence-Based Quality Extraction
**Objective**: Prevent redundant questioning by maximizing information gain from every user message.
- **Protocol**: Agents must extract not just the symptom (e.g., "headache") but its quality (e.g., "throbbing"), duration, and triggers.
- **Mandatory Action**: If a quality is present in the `raw_text` or `conversation_history`, it MUST be locked into the Evidence Ledger. Never ask a question for information already provided.

## SOP-003: Longitudinal History Integration (RAG)
**Objective**: Correlate current symptoms with the patient's uploaded medical records and past history.
- **Protocol**: Every diagnostic cycle MUST check the `extracted_medical_records` (RAG) for relevant past surgeries, chronic conditions, or recent lab tests.
- **Mandatory Action**: If a RAG match is found, the agent must reference it explicitly (e.g., "Given your history of hypertension mentioned in your June report...").

## SOP-004: Differential Diagnosis (DDx) Strategy
**Objective**: Maintain a broad yet focused differential.
- **Protocol**: Always maintain 3-5 hypotheses spanning Common, Uncommon, and Dangerous categories.
- **Mandatory Action**: The next question generated must be the "One Best Question" that differentiates between the top two competing hypotheses.

## SOP-005: Conclusion & Grade of Recommendation
**Objective**: Provide clear, safe, and actionable conclusions.
- **Protocol**: Conclusions must state the primary suspected diagnosis, the confidence level, and the evidence-based rationale.
- **Mandatory Action**: Always include "Red Flag" warnings and a recommendation to consult a human professional for definitive diagnosis.
