# CuraBot: Complete System Architecture & Context Dump
**Purpose:** Use this document as the system context prompt for Claude AI (or any other LLM) to generate an Enterprise Low-Level Design (LLD), High-Level Design (HLD), or architecture documentation.

---

## 1. Project Overview & Scope
- **Project Name:** CuraBot — Agentic AI Differential Diagnosis Tutor
- **Purpose:** A conversational AI system designed to simulate differential diagnosis interviews for medical students and provide preliminary symptom insights for patients. 
- **Disclaimer:** Strictly for MEDICAL EDUCATION. Not for clinical use or real diagnosis.
- **Autonomy Level:** L2/L3 (Supervised Assistant / Recommend-Only). It never executes clinical actions or prescribes medications.

## 2. Technology Stack & Deployment
- **Frontend:** React, TypeScript, Vite, Tailwind CSS (Hosted locally via npm).
- **Backend:** Python, FastAPI, Uvicorn, LangGraph (for agent orchestration).
- **Relational Database:** Supabase (Cloud PostgreSQL) with automatic local fallback to SQLite (`curabot_local.db`) for offline development.
- **Vector Database:** ChromaDB (Local file-based storage in `chroma_db/`) used for semantic search.
- **LLM Integration:** Multi-provider fallback chain (Gemini 2.0 Flash → Groq LLaMA 3 → OpenRouter free models).
- **Containerization:** Configured via `docker-compose.yml` defining `backend`, `frontend`, and optional `redis` containers.

## 3. Database Schema Overview
- `users`: User authentication (ID, email, name, password hash).
- `user_profiles`: Medical data (age, gender, blood group, chronic conditions, medications, allergies).
- `chat_sessions`: Tracks diagnostic interview status (active, concluded).
- `chat_messages`: Logs individual conversational turns, tracking role (user/assistant).
- `medical_reports`: Metadata for uploaded PDFs (URLs and extracted text).
- `diagnosis_history`: Stores the final hypotheses, evidence ledger, and confidence trajectory of concluded sessions.

## 4. The 6-Agent LangGraph Pipeline
The core of the system is a multi-agent orchestration pipeline. Each agent outputs strictly structured JSON.

1. **Agent 1: Symptom Normalizer**
   - *Input:* User's raw message.
   - *Task:* Extracts and normalizes symptoms, severities, durations, and flags emergency keywords.
   - *Fallback:* Rule-based keyword matching regex covering 60+ symptoms if LLM fails.
2. **Agent 2: Hypothesis Generator**
   - *Input:* Normalized symptoms + Top 10 disease candidates from the local `diseases.json` knowledge base.
   - *Task:* Generates 3-5 ranked diagnostic hypotheses with confidence scores totaling exactly 100%. Ensures critical diseases receive a minimum 8% safety floor.
3. **Agent 3: Evidence Evaluator**
   - *Input:* Hypotheses + All gathered evidence (symptoms, vitals, RAG lab data).
   - *Task:* Maps every piece of evidence to hypotheses as supporting, contradicting, or neutral. Crucially tracks *absent expected symptoms* as contradicting evidence.
   - *Implementation Note:* Defaults to a pure-Python rule-based execution to save LLM API calls.
4. **Agent 4: Hypothesis Reviser**
   - *Input:* Evidence Ledger + Current Hypotheses.
   - *Task:* Uses Bayesian-style likelihood ratio multipliers (e.g., strong support = 1.6x, strong contradiction = 0.5x) to recalculate confidence scores. 
   - *Implementation Note:* Defaults to pure-Python rule-based execution.
5. **Agent 5: Diagnostic Strategist**
   - *Input:* Revised Hypotheses + Conversation History + User Context.
   - *Task:* Decides to either generate a targeted follow-up question (following OPQRST clinical guidelines) OR concludes the diagnosis if confidence is >75% with a 15% margin. Ensures no redundant questions are asked.
6. **Agent 6: Self-Critique & Bias Check**
   - *Input:* Current Hypotheses + State.
   - *Task:* Detects cognitive biases like "Anchoring" (ignoring secondary hypotheses) or "Premature Closure" (concluding too early).

## 5. The 10 Clinical SOPs (Standard Operating Procedures)
These are pure-Python rule-based scripts that run between Agent 1 and Agent 2, and again at conclusion. They act as strict safety guardrails and execute instantly without LLM latency.
- **SOP-006 (Triage):** Assigns Red/Orange/Yellow/Green urgency. Red triggers an immediate system override.
- **SOP-007 (Chest Pain):** Evaluates ACS (Acute Coronary Syndrome) risk.
- **SOP-008 (FAST Stroke):** Checks Face, Arm, Speech, Time. Triggers instant neurological emergency override.
- **SOP-009 (Respiratory Distress):** Evaluates breathing emergency severity.
- **SOP-010 (Vitals Interpreter):** Evaluates user-submitted BP, HR, Temp, SpO2 against normal ranges.
- **SOP-011 (Lab Value Interpreter):** Parses RAG-retrieved text to flag abnormal lab metrics (glucose, WBC, etc.).
- **SOP-012 (Medication Safety):** Cross-checks user profile medications against hypotheses for drug interactions.
- **SOP-013 (Red Flag Scanner):** Scans for critical phrases (e.g., "blood in stool").
- **SOP-014 (Specialist Routing):** Maps the final diagnosis to the correct specialist referral.
- **SOP-015 (Confidence Calibration):** Checks if enough iterations and evidence exist to safely conclude.

## 6. RAG (Retrieval-Augmented Generation) Architecture
Used to process patient medical records (e.g., past blood test PDFs).
1. **Ingestion:** Uploaded PDFs are parsed using `pdfplumber`.
2. **Chunking:** Text is split into ~600-character chunks, preserving line boundaries so lab values aren't split.
3. **Embedding:** Chunks are vectorized using Google Generative AI embeddings (with dummy zero-vector fallback).
4. **Storage:** Indexed in ChromaDB under the `patient_records` collection.
5. **Retrieval:** Vector search is strictly isolated using `user_id` metadata filtering. The top 3 chunks are injected into the agent pipeline as "Extracted Medical Records Context".

## 7. Medical Evidence Citation Engine
- A pure-Python module running at the conclusion of the diagnosis.
- Maps the final diagnosis to its **ICD-10-CM code**.
- Identifies the Clinical Authority (e.g., AHA for cardiology).
- Auto-generates PubMed search URLs for the specific symptom-disease relationships so users can independently verify the AI's reasoning.

## 8. State Management & Context Handling
- **New vs. Returning Users:** Returning users are processed by the **Patient History Analyzer**, which fetches past diagnoses, severity history, and known conditions from the database. It can generate dynamic follow-up questions (e.g., *"Is this migraine worse than the one you had last month?"*).
- **Session State:** Managed by LangGraph's `StateGraph`, maintaining the `DiagnosticState` (Pydantic model) across conversation turns.

## 9. Error Handling & LLM Resilience
- **API Pacing:** Global `asyncio.Lock` (`_api_lock`) ensures LLM requests are paced (0.5s delay) to prevent 429 Too Many Requests errors.
- **Fallback Chain:** If Gemini fails, it attempts Groq, then OpenRouter. Exhausted providers are placed on a 90-second cooldown.
- **Schema Recovery:** If the LLM returns malformed JSON, markdown-stripping and regex repair scripts attempt to salvage the data. If completely failed, the system defaults to local keyword/heuristic rules.

## 10. SDLC, Evaluation, & Benchmarking
- **Golden Benchmark Suite:** A local testing framework (`test_all_sops.py`, `diagnose_failures.py`) that runs synthetic patient symptom configurations through the pipeline offline.
- **Accuracy Target:** Benchmarked against >100 cases tracking Top-3 diagnostic inclusion, negative exclusion (avoiding false positives), and body-system coherence.
