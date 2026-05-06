# CuraBot — Low-Level Design Document (Version 1)

> **Project:** CuraBot — Agentic AI Differential Diagnosis Tutor  
> **Version:** 1.0  
> **Date:** April 2026  
> **Disclaimer:** FOR MEDICAL EDUCATION ONLY — Not for clinical use

---

## Table of Contents

1. [System Overview](#1-system-overview)
   - 1.1 Problem Statement
   - 1.2 What the System Does
   - 1.3 Users and Use Cases
   - 1.4 Scope (In-Scope / Out-of-Scope)
2. [Architecture Decomposition](#2-architecture-decomposition)
   - 2.1 Component Overview
   - 2.2 Frontend Layer
   - 2.3 Backend Layer
   - 2.4 Database Layer
   - 2.5 Vector Database (ChromaDB)
   - 2.6 LLM Integration Layer
   - 2.7 Component Interaction Flow
3. [GenAI Capability Design](#3-genai-capability-design)
   - 3.1 How RAG Works in CuraBot
   - 3.2 How Patient History and PDFs Are Used
   - 3.3 Prompt Engineering and Flow
4. [Agentic Design](#4-agentic-design)
   - 4.1 Agent Pipeline Overview
   - 4.2 Agent 1 — Symptom Normalizer
   - 4.3 Agent 2 — Hypothesis Generator
   - 4.4 Agent 3 — Evidence Evaluator
   - 4.5 Agent 4 — Hypothesis Reviser
   - 4.6 Agent 5 — Diagnostic Strategist
   - 4.7 Agent 6 — Self-Critique & Bias Check
   - 4.8 Supporting Module — Patient History Analyzer
   - 4.9 Clinical SOPs (Standard Operating Procedures)
   - 4.10 How the Agents Work Together

---

## 1. System Overview

### 1.1 Problem Statement

Medical students and early-career healthcare learners often lack access to structured tools that can help them practise clinical reasoning skills outside the classroom. Traditional medical education relies heavily on textbook cases and limited clinical rotations, which do not provide the kind of iterative, feedback-driven diagnostic thinking that real clinical practice demands. Furthermore, patients frequently struggle to understand their symptoms before consulting a doctor, which can lead to delayed care for serious conditions.

CuraBot addresses this gap by providing an AI-powered conversational system that simulates the process of differential diagnosis. It takes a patient's symptom description in everyday language, analyses it through a structured multi-agent pipeline, and produces a ranked list of possible conditions — all while explaining its reasoning at every step. The system is designed strictly for **medical education purposes** and does not replace real clinical consultation.

### 1.2 What the System Does

CuraBot is an agentic AI chatbot that conducts a step-by-step diagnostic conversation with a user. When a user describes their symptoms, the system processes the message through a pipeline of six specialised AI agents. Each agent has a distinct role — from normalising raw symptom text into standardised medical concepts, to generating possible diagnoses, evaluating evidence, revising confidence scores, determining the best follow-up question, and finally checking for cognitive biases in the reasoning process.

The system supports both new and returning patients. For returning patients, CuraBot retrieves their past diagnosis history, uploaded medical reports (PDFs), and known conditions from a cloud database (Supabase). It uses Retrieval-Augmented Generation (RAG) to search through previously uploaded lab reports and PDFs to find relevant findings that can inform the current diagnosis. The system also implements 10 clinical Standard Operating Procedures (SOPs) — such as triage classification, chest pain protocols, stroke detection, and medication safety checks — all implemented as pure Python rule-based logic without any extra LLM calls.

At the end of a diagnostic conversation, CuraBot presents a final diagnosis with confidence scores, recommended specialist referrals, suggested lab tests, and downloadable diagnostic reports in both JSON and HTML format.

### 1.3 Users and Use Cases

**Primary Users:**

- **Medical Students:** Students who want to practise differential diagnosis by entering symptoms and observing how the AI reasons through possible conditions, evaluates evidence, and updates its hypotheses over multiple rounds of questioning.

- **General Users (Patients):** Individuals who want a preliminary understanding of what their symptoms might indicate before visiting a doctor. The system helps them understand the urgency of their condition and which specialist to consult.

**Key Use Cases:**

| # | Use Case | Description |
|---|----------|-------------|
| 1 | **Symptom Analysis** | User describes symptoms in plain language; the system identifies and normalises them into medical terms. |
| 2 | **Differential Diagnosis** | System generates a ranked list of 3–5 possible conditions with confidence scores and reasoning. |
| 3 | **Multi-Turn Conversation** | System asks targeted follow-up questions to gather more evidence and refine its diagnosis. |
| 4 | **Vital Signs Submission** | User provides blood pressure, heart rate, temperature, etc., which the system evaluates. |
| 5 | **Medical Report Upload** | User uploads PDF lab reports; system extracts text, indexes it for RAG, and uses findings in diagnosis. |
| 6 | **Returning Patient Context** | System recognises returning users and factors in past diagnoses, recurring conditions, and severity trends. |
| 7 | **Emergency Triage** | System detects red flags (e.g., stroke symptoms, crushing chest pain) and immediately escalates with emergency alerts. |
| 8 | **Diagnostic Report Download** | After diagnosis conclusion, user can download a detailed report in JSON or printable HTML format. |
| 9 | **Bias Detection** | System identifies cognitive biases like anchoring or premature closure in its own reasoning process. |
| 10 | **Profile Management** | User can create a profile with medical history, conditions, medications, and allergies. |

### 1.4 Scope

**In-Scope (Version 1):**

- Conversational symptom intake and normalisation
- 6-agent diagnostic pipeline with Gemini LLM integration
- Disease knowledge base with 100+ conditions (stored in `diseases.json`)
- 10 clinical SOPs implemented as rule-based Python logic
- RAG-based retrieval from uploaded PDF medical reports using ChromaDB
- User authentication (signup, login) with Supabase and local SQLite fallback
- Returning patient longitudinal analysis (past diagnoses, severity tracking, recurring condition detection)
- Real-time agent thought streaming to the frontend
- Confidence trajectory tracking across conversation iterations
- Downloadable diagnostic reports (JSON and HTML)
- Model fallback mechanism (Gemini → Groq → OpenRouter)
- Cognitive bias detection and SOP compliance checking

**Out-of-Scope (Version 1):**

- Real clinical use or certified medical diagnosis
- Integration with hospital EMR (Electronic Medical Record) systems
- Real-time wearable or IoT device data ingestion
- Multi-language support (system currently operates in English only)
- Voice-based symptom input
- Prescription generation or medication ordering
- HIPAA or GDPR compliance certification
- Deployment to production cloud environments (currently designed for local/dev use)

---

## 2. Architecture Decomposition

### 2.1 Component Overview

CuraBot follows a standard three-tier architecture with an additional AI layer:

The system consists of five major layers:

1. **Frontend** — The user interface built with React and TypeScript.
2. **Backend** — The API server and agent orchestration built with FastAPI.
3. **Database** — Persistent storage using Supabase (cloud) or SQLite (local fallback).
4. **Vector Database** — ChromaDB for storing and searching embeddings of disease data and patient medical records (used for RAG).
5. **LLM Layer** — External large language models (Gemini, Groq, OpenRouter) used by agents for natural language understanding and generation.

### 2.2 Frontend Layer

The frontend is a single-page application built using **React** with **TypeScript**, bundled by **Vite**, and styled with **Tailwind CSS**. It communicates with the backend exclusively through REST API calls.

**Key Pages:**

| Page | File | Purpose |
|------|------|---------|
| Landing Page | `LandingPage.tsx` | Introduction and entry point |
| Login Page | `LoginPage.tsx` | User authentication |
| Signup Page | `SignupPage.tsx` | New user registration |
| Dashboard | `DashboardPage.tsx` | Session history and past diagnoses |
| Chat Page | `ChatPage.tsx` | Main diagnostic conversation interface |
| Profile Page | `ProfilePage.tsx` | Medical history and profile management |
| About Page | `AboutPage.tsx` | System information |

The Chat Page is the core of the user experience. It renders the diagnostic conversation, displays real-time agent thoughts (what each agent is processing), shows hypothesis cards with confidence scores, presents evidence evaluation results, visualises the confidence trajectory over iterations, and provides options to submit vital signs and upload medical reports.

**State Management:** The frontend uses Zustand (`useAuthStore`) for managing authentication state, user sessions, and tokens. API calls are made using standard `fetch` or `axios` to the backend running on `http://localhost:8000`.

### 2.3 Backend Layer

The backend is a **FastAPI** application written in Python, serving as both the API gateway and the orchestration engine for the multi-agent pipeline. It runs on `http://localhost:8000` using Uvicorn.

**Key Modules:**

| Module | File | Responsibility |
|--------|------|----------------|
| API Server | `main.py` | FastAPI app with all REST endpoints (auth, chat, sessions, reports) |
| Orchestrator | `services/orchestrator.py` | Coordinates the 6-agent pipeline and 10 SOPs |
| LLM Client | `services/llm_client.py` | Manages LLM API calls with multi-provider fallback |
| Supabase Client | `services/supabase_client.py` | Database operations with cloud/local fallback |
| User Logger | `services/user_logger.py` | Logs user actions to Excel file |
| LangGraph Core | `core/graph.py` | LangGraph-based agent workflow definition |
| Diagnostic State | `core/state.py` | Pydantic state model for the diagnostic pipeline |
| Session Manager | `core/supervisor.py` | Manages sessions and checkpointing |

**Key API Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/signup` | Register a new user |
| POST | `/api/auth/login` | Authenticate and get access token |
| GET | `/api/auth/me` | Get current user profile |
| PUT | `/api/auth/profile` | Update medical profile |
| POST | `/api/chat` | Main chat — processes message through 6-agent pipeline |
| GET | `/api/sessions` | List user's past sessions |
| POST | `/api/upload-record` | Upload PDF medical report |
| GET | `/api/report/json/{id}` | Download diagnostic report as JSON |
| GET | `/api/report/html/{id}` | Download diagnostic report as printable HTML |

The `/api/chat` endpoint is the most important. When it receives a message, it initialises or restores the session, fetches the user's context (profile, past diagnoses, medical reports), performs RAG search on uploaded PDFs, runs the 6-agent pipeline through the orchestrator, saves messages and diagnosis results, and returns a structured response to the frontend.

### 2.4 Database Layer

CuraBot uses **Supabase** (a PostgreSQL-based Backend-as-a-Service) for cloud storage and **SQLite** as a local fallback when Supabase is not configured.

**Database Tables:**

| Table | Purpose |
|-------|---------|
| `users` | Stores user credentials (ID, email, password hash, name) |
| `user_profiles` | Medical profiles (age, gender, blood group, conditions, medications, allergies) |
| `chat_sessions` | Conversation sessions with status tracking |
| `chat_messages` | Individual messages with role (user/assistant), content, and metadata |
| `medical_reports` | Uploaded PDF metadata, extracted text, and cloud file URLs |
| `diagnosis_history` | Completed diagnoses with final hypotheses, evidence, and confidence trajectories |

The `SupabaseService` class automatically detects whether Supabase credentials are configured. If they are, it uses the Supabase client library to interact with the cloud database. If not, it creates a local SQLite database file (`curabot_local.db`) with an identical schema and uses standard SQL queries. This dual-mode design ensures the system works in both connected and offline environments.

For cloud deployments, physical PDF files are uploaded to a **Supabase Storage bucket** named `medical_reports`, and public URLs are stored in the database alongside the extracted text.

### 2.5 Vector Database (ChromaDB)

CuraBot uses **ChromaDB** as its vector database for storing and searching embeddings. ChromaDB is an open-source embedding database that runs locally and persists data to disk in the `chroma_db/` directory.

**Collections:**

| Collection | Purpose |
|------------|---------|
| `diseases` | Embeddings of disease descriptions from the knowledge base |
| `symptoms` | Embeddings of symptom concept mappings |
| `cases` | Embeddings of synthetic test cases |
| `patient_records` | Embeddings of uploaded PDF chunks (scoped per user for RAG) |

**Embedding Function:** When a Gemini API key is available, ChromaDB uses `GoogleGenerativeAiEmbeddingFunction` to generate real semantic embeddings. If no API key is configured, a dummy embedding function (returning zero vectors) is used as a fallback.

The `patient_records` collection is the most important for RAG. When a user uploads a PDF medical report, the system extracts the text, splits it into chunks of approximately 600 characters, and indexes each chunk into ChromaDB with metadata linking it to the user ID, report ID, and source filename. During diagnosis, the system queries this collection using the patient's symptom message to retrieve the most relevant lab findings and medical history.

### 2.6 LLM Integration Layer

The `LLMClient` class manages all interactions with large language models. It implements a **multi-provider fallback chain** to ensure the system remains functional even when one provider's rate limits are exhausted.

**Provider Priority Chain:**

1. Gemini (Primary) → gemini-2.0-flash
2. Groq (Secondary) → llama-3.3-70b-versatile
3. OpenRouter (Tertiary) → llama-3.3-70b-instruct:free / llama-3.2-3b-instruct:free / gemma-3-27b-it:free

When the primary provider (Gemini) hits a rate limit or quota error, the client automatically marks it as exhausted and falls through to Groq. If Groq also fails, it tries each OpenRouter model in sequence. Exhausted models are automatically reset after a 90-second cooldown period.

All LLM calls are serialised through a global async lock (`_api_lock`) with a 0.5-second pacing delay to avoid rate limit collisions. Responses are parsed as JSON when `expect_json=True`, with multiple fallback strategies for extracting JSON from markdown-wrapped or malformed responses. If all LLM providers fail, a local fallback response is returned that triggers rule-based processing in the agents.

### 2.7 Component Interaction Flow

The following describes the end-to-end flow when a user sends a message:

1. POST /api/chat {message, user_id, session_id}
2. Fetch user profile + past diagnoses + reports
3. RAG search on patient_records (query = message)
4. Return top 3 relevant PDF chunks
5. Run pipeline(message + RAG context, session_state, user_context)
6. Agent 1 → Normalizer prompt → Normalized symptoms JSON
7. Run SOPs (Red Flags, Triage, Chest Pain, Stroke, Vitals, Labs)
8. Agent 2 → Hypothesis Generator prompt → Ranked hypotheses JSON
9. Agent 3 → Evidence Evaluator (rule-based fallback)
10. Agent 4 → Hypothesis Reviser (Bayesian fallback)
11. Agent 5 → Diagnostic Strategist prompt → Strategy decision JSON
12. Agent 6 → Self-Critique (rule-based fallback)
13. SOP-015 Confidence Calibration
14. Save messages + diagnosis (if concluded)
15. Return ChatResponse JSON

The key insight is that not every agent makes an LLM call in every iteration. The orchestrator is optimised to use rule-based fallbacks for Agents 3 (Evidence Evaluator), 4 (Hypothesis Reviser), and 6 (Self-Critique) to save LLM API calls and reduce latency. Only Agents 1 (Symptom Normalizer), 2 (Hypothesis Generator), and 5 (Diagnostic Strategist) make actual LLM calls during a standard pipeline run.

---

## 3. GenAI Capability Design

### 3.1 How RAG Works in CuraBot

Retrieval-Augmented Generation (RAG) in CuraBot is used to bring a patient's uploaded medical records (PDF lab reports, test results, etc.) directly into the diagnostic conversation. Instead of relying solely on what the patient types in chat, the system can automatically retrieve relevant clinical data from their uploaded documents and use it to inform the diagnosis.

The RAG pipeline works in three stages:

**Stage 1 — Ingestion (at upload time):**
When a user uploads a PDF through the `/api/upload-record` endpoint, the system uses `pdfplumber` to extract readable text from every page of the PDF. The extracted text is then split into chunks of approximately 600 characters each (preserving line boundaries so that clinical parameters stay together within a chunk). Each chunk is indexed into the `patient_records` collection in ChromaDB, along with metadata including the user ID, report ID, and source filename. If a Gemini API key is configured, the chunks are embedded using Google's embedding model for semantic search capability.

**Stage 2 — Retrieval (at query time):**
When a logged-in user sends a message through the chat endpoint, the backend queries ChromaDB's `patient_records` collection using the patient's message as the search query. The search is scoped by `user_id` to ensure patients only retrieve their own records. The top 3 most relevant chunks are returned, ranked by cosine similarity.

**Stage 3 — Augmentation (during pipeline execution):**
The retrieved chunks are injected into the diagnostic pipeline in two ways. First, the chunks are formatted into a "UPLOADED MEDICAL REPORTS CONTEXT" block that is prepended to the patient's message, so the LLM agents can see the lab values directly. Second, the chunks are stored in the `user_context["extracted_medical_records"]` dictionary, which is passed to every agent in the pipeline. This allows the Evidence Evaluator to treat lab findings as evidence items, the Diagnostic Strategist to reference specific lab values when asking follow-up questions, and the Lab Value Interpreter SOP (SOP-011) to parse and flag any abnormal lab values.

### 3.2 How Patient History and PDFs Are Used

CuraBot distinguishes between **new users** and **returning users** and treats them differently throughout the pipeline.

**For New Users:**
The system casts a wide diagnostic net. It asks more detailed clarifying questions, does not assume any prior medical history, and proactively asks the user to upload medical records if they have any. The agents operate without any historical context and rely entirely on the current conversation.

**For Returning Users:**
The system builds a comprehensive **user context** package by pulling data from the database:

- **Profile:** Age, gender, blood group, known conditions, current medications, and allergies.
- **Past Diagnoses:** The last 5 completed diagnostic sessions with their final hypotheses and confidence scores.
- **Severity History:** A timeline of past conditions with confidence scores, enabling trend detection (worsening, improving, or stable).
- **Recurring Conditions:** Conditions diagnosed more than once, with occurrence count and trend analysis.
- **Medical Reports:** Metadata and extracted text from up to 10 uploaded PDF reports.
- **Recent Conversations:** The last 3 chat session transcripts.
- **Extracted Medical Records (RAG):** The top 3 relevant chunks retrieved from ChromaDB.

This context is passed to the pipeline and used by specific agents. The **Patient History Analyzer** (a supporting module that runs before the 6-agent pipeline) uses the LLM to compare the current symptoms against past conditions and determine whether this is a recurrence. If it detects a recurrence, it generates a disease-specific follow-up question (e.g., "Last time you were diagnosed with GERD. Has the burning sensation changed in intensity since then?"). The **Symptom Normalizer** appends known conditions and medications to its prompt so it can interpret symptoms in context. The **Hypothesis Generator** factors in past diagnoses and medical reports when building its differential. The **Diagnostic Strategist** references severity trends and recurring conditions to ask targeted questions, and explicitly uses RAG-retrieved lab values to confirm or deny hypotheses.

### 3.3 Prompt Engineering and Flow

CuraBot uses structured prompt engineering to ensure consistent, parseable, and clinically-focused outputs from the LLM. Each agent has two types of prompts:

**1. System Prompt (Agent Identity):**
A static instruction block that defines the agent's role, clinical rules, SOPs it must follow, and behavioural constraints. For example, the Symptom Normalizer's system prompt instructs it to "extract ALL mentioned symptoms (explicit and implied)", "classify each as primary or secondary", and "flag ambiguous descriptions". The Diagnostic Strategist's system prompt explicitly instructs it to follow the OPQRST clinical workflow and adopt a warm, empathetic doctor persona.

**2. Task Prompt (Dynamic Input):**
A template-based prompt that is filled in with the current diagnostic state — patient message, normalized symptoms, hypotheses, evidence, conversation history, user context, and iteration count. Every task prompt specifies the exact JSON schema the agent must use in its response, ensuring the output can be programmatically parsed and consumed by the next agent in the pipeline.

**Prompt Flow Through the Pipeline:**

| Agent | Key Prompt Input | Expected JSON Output |
|-------|-----------------|---------------------|
| Agent 1 (Normalizer) | Raw patient message + medical history | `{primary_symptoms, secondary_symptoms, ambiguous_signals, vital_signs, emergency_red_flags}` |
| Agent 2 (Hypothesis Generator) | Normalized symptoms + disease KB (top 10) + user context | `{hypotheses: [{name, confidence, reasoning, severity_class, key_features_present}]}` |
| Agent 3 (Evidence Evaluator) | Hypotheses + all evidence (symptoms, vitals, history, RAG records) | `{evidence_ledger: [{finding, supports, contradicts}], absent_evidence, missing_evidence}` |
| Agent 4 (Hypothesis Reviser) | Hypotheses + evidence evaluation | `{revised_hypotheses: [{name, new_confidence, change_reason, status}]}` |
| Agent 5 (Diagnostic Strategist) | Revised hypotheses + evidence + conversation history + user context | `{should_conclude, next_question, request_vitals}` or `{conclusion_message, final_recommendations}` |
| Agent 6 (Self-Critique) | Hypotheses + evidence + iteration count | `{biases_detected: [{type, severity, mitigation}], reasoning_quality}` |

The prompts are designed to enforce specific clinical standards. For instance, the Hypothesis Generator prompt includes a rule: "Confidence scores MUST sum to exactly 100%" and "ALWAYS include at least one critical-severity disease if relevant symptoms exist". The Diagnostic Strategist prompt includes a redundancy check: "If a quality (sharp, dull, etc.) is in the message history, NEVER ask for it again". These embedded rules act as guardrails that keep the LLM output clinically sound.

---

## 4. Agentic Design

### 4.1 Agent Pipeline Overview

CuraBot's diagnostic engine is built as a sequential multi-agent pipeline. Each agent receives the output of the previous agent, performs a specific analytical function, and passes its result forward. The pipeline runs once per user message and typically completes in 3–10 iterations of questioning before reaching a diagnosis.

Before the 6-agent pipeline starts, an optional **Patient History Analyzer** runs (only for returning users on the first iteration) to establish a clinical baseline. After Agent 1, a bank of **Clinical SOPs** runs as pure Python logic — no additional LLM calls. Agents 3, 4, and 6 use local rule-based fallbacks by default to conserve LLM calls, while Agents 1, 2, and 5 always call the LLM.

---

### 4.2 Agent 1 — Symptom Normalizer

**Purpose:** Converts the patient's free-text message into standardised medical concepts that the rest of the pipeline can work with.

**What It Does:**
The Symptom Normalizer is the first agent in the pipeline and acts as the translator between the patient's natural language and the system's medical ontology. When a patient says "I've had a really bad headache and my stomach has been bothering me", this agent extracts two standardised symptoms: `headache` (neurological, primary) and `abdominal_pain` (gastrointestinal, primary). It also identifies the severity, duration, and character of each symptom when mentioned, flags any ambiguous or vague descriptions that need clarification, detects vital signs mentioned in the text, and identifies emergency red-flag phrases like "crushing chest pain" or "can't breathe".

**Input:**
- Raw patient message (string)
- Conversation history (list of past messages)
- User context (medical history for returning users)

**Fallback Mechanism:** If the LLM call fails (due to rate limits or API errors), the agent falls back to a comprehensive keyword-matching system. This fallback covers over 60 symptom keywords across cardiovascular, respiratory, gastrointestinal, neurological, constitutional, and musculoskeletal systems. It also detects pain quality adjectives (sharp, dull, crushing, burning, etc.) and critical emergency keywords.

---

### 4.3 Agent 2 — Hypothesis Generator

**Purpose:** Generates a ranked list of 3–5 possible diagnoses (differential diagnosis) based on the normalised symptoms.

**What It Does:**
The Hypothesis Generator is the diagnostic brain of the pipeline. It takes the normalised symptoms from Agent 1 and cross-references them against a disease knowledge base (`diseases.json`) containing 100+ medical conditions. Each disease entry includes primary, secondary, and atypical symptoms, risk factors, severity classification (critical, serious, moderate, benign), differentiating features, prevalence data, and recommended lab tests.

The agent first performs a heuristic scoring pass to filter the disease database down to the top 10 most relevant candidates (to avoid overwhelming the LLM with too much context). It then sends these candidates along with the normalised symptoms to the LLM, which generates a ranked differential diagnosis with confidence scores that sum to exactly 100%.

**Input:**
- Normalized symptoms (output of Agent 1, accumulated across conversation turns)
- User context (past diagnoses, medical reports, medications)
- Whether the patient is new or returning

**Key Design Decisions:**
- Confidence scores always normalise to exactly 100% across all hypotheses.
- Critical-severity diseases receive a minimum 8% confidence when any matching symptoms are present, ensuring they are never prematurely dismissed.
- Discriminating symptom bonus: Symptoms that are unique to one disease (and not shared by other candidates) receive extra scoring weight.
- The heuristic scorer uses fuzzy partial-string matching and body-system matching to catch cases where symptom names differ slightly between the patient and the knowledge base.

**Fallback Mechanism:** If the LLM fails, the agent uses a sophisticated rule-based scoring system that calculates confidence from match ratio, discriminating symptom bonus, severity weights, prevalence weights, and differentiating feature bonus.

---

### 4.4 Agent 3 — Evidence Evaluator

**Purpose:** Maps every piece of available evidence (symptoms, vitals, medical history, RAG-retrieved lab values) to its supporting or contradicting relationship with each hypothesis.

**What It Does:**
The Evidence Evaluator takes the hypotheses generated by Agent 2 and evaluates every piece of clinical evidence against each one. For each evidence item (a symptom, a vital sign reading, a known pre-existing condition, or a lab value from an uploaded PDF), the agent determines whether it supports, contradicts, or is neutral for each hypothesis. It also assigns a strength rating (strong, moderate, or weak) to each relationship.

A critical feature is that the agent tracks **absent expected symptoms** — primary symptoms that would typically be present for a given disease but have not been reported by the patient. For critical-severity diseases, absent key symptoms are recorded as moderate contradicting evidence, which helps prevent over-diagnosis of dangerous conditions.

**Input:**
- Hypotheses (output of Agent 2)
- All evidence: primary symptoms, secondary symptoms, vital signs, known conditions (from user profile), and extracted medical records (from RAG)

**Key Design Decision:** In the production pipeline, this agent uses its rule-based fallback by default (not the LLM) to save API calls. The rule-based system loads the full disease knowledge base and checks each symptom against each disease's primary, secondary, and atypical symptom lists, with special handling for differentiating features.

---

### 4.5 Agent 4 — Hypothesis Reviser

**Purpose:** Updates the confidence scores of each hypothesis based on the evidence evaluation, using Bayesian-style likelihood ratio reasoning.

**What It Does:**
The Hypothesis Reviser takes the original hypotheses and the evidence ledger and recalculates confidence scores. Instead of simple arithmetic (adding or subtracting fixed amounts), it uses likelihood ratio multipliers: strong supporting evidence multiplies the confidence by 1.6×, moderate by 1.3×, and weak by 1.1×. Contradicting evidence applies reduction multipliers (strong: 0.5×, moderate: 0.7×, weak: 0.9×). After all adjustments, the scores are normalised back to 100% and a severity floor is applied — critical diseases cannot drop below 8% unless they have 3 or more contradicting evidence items, and serious diseases cannot drop below 5%.

The agent also maintains a tiebreaker system: when two hypotheses have nearly identical confidence, it uses severity rank, supporting evidence count, and contradicting evidence count to determine ordering.

**Input:**
- Hypotheses (output of Agent 2)
- Evidence evaluation (output of Agent 3)

**Key Design Decision:** Like Agent 3, this agent uses its Bayesian fallback by default in the production pipeline to save LLM calls. The mathematical approach ensures consistent, reproducible confidence updates.

---

### 4.6 Agent 5 — Diagnostic Strategist

**Purpose:** Decides the best next action — either ask a follow-up question to gather more evidence, request vital signs, or conclude the diagnosis.

**What It Does:**
The Diagnostic Strategist is the decision-maker of the pipeline. It analyses the current state of the diagnosis (revised hypotheses, evidence gathered so far, conversation history, and iteration count) and determines whether enough information has been gathered to conclude or whether more questioning is needed.

If the diagnosis is not ready to conclude, the agent generates a single, targeted, conversational follow-up question. It follows the OPQRST clinical workflow (Onset, Provocation, Quality, Region, Severity, Timing) and a Review of Systems approach. Most importantly, it performs a redundancy check — it reads through the entire conversation history to ensure it never asks a question that has already been answered. It prioritises ruling out critical-severity diseases before concluding.

If the diagnosis is ready to conclude, the agent produces a conclusion message with the final diagnosis, severity context, recommended lab tests, and specialist referral recommendations.

**Input:**
- Revised hypotheses (output of Agent 4)
- Evidence evaluation (output of Agent 3)
- Conversation history (all past user/assistant messages)
- Iteration count and total evidence count
- User context (for returning patient-specific questions)

**Dynamic Conclusion Criteria:**
The agent does not use fixed iteration limits. Instead, it applies four conditions that must all be met:
1. Top hypothesis confidence ≥ 75%
2. Confidence margin over the second hypothesis ≥ 15%
3. At least 3 iterations completed
4. No unresolved critical-severity disease with confidence > 20%

A safety soft limit at 10 iterations forces a conclusion with a disclaimer if the criteria cannot be met.

---

### 4.7 Agent 6 — Self-Critique & Bias Check

**Purpose:** Challenges the diagnostic reasoning by detecting cognitive biases, checking SOP compliance, and forcing consideration of alternative hypotheses.

**What It Does:**
The Self-Critique agent acts as a quality assurance layer. It reviews the current state of hypotheses and detects common cognitive biases that can affect diagnostic reasoning:

- **Anchoring Bias:** Flagged when the confidence gap between the top hypothesis and the second is greater than 30%. This means the system may be "anchored" to one diagnosis and ignoring alternatives.
- **Premature Closure:** Flagged when high confidence (>70%) is reached within the first 2 iterations, suggesting the system is concluding before gathering enough evidence.
- **SOP Compliance:** Checks whether key SOPs (triage, vitals evaluation, red flag scanning) were executed during the current pipeline run.

**Input:**
- Revised hypotheses (output of Agent 4)
- Iteration count
- SOP findings string (summary of which SOPs activated)

**Key Design Decision:** This agent runs using its rule-based fallback by default, which checks for specific bias patterns without making any LLM calls. The biases detected are displayed to the frontend user as educational feedback.

---

### 4.8 Supporting Module — Patient History Analyzer

**Purpose:** Analyses a returning patient's past medical data to establish a clinical baseline before the 6-agent pipeline runs.

**What It Does:**
This module runs only for returning patients during the first iteration of a new conversation. It uses the LLM to compare the patient's current symptom message against their past diagnoses, severity history, and uploaded medical records. It determines whether the current complaint is a recurrence of a past condition, a complication, or an entirely new issue.

If a recurrence is detected, the analyzer generates a **dynamic severity question** — a personalised, disease-specific follow-up that references the patient's specific history. For example: "Last time we discussed your migraine episodes. Has the frequency or intensity changed since then?" This question is injected into the first response from the Diagnostic Strategist.

The analyzer also produces a **Clinical Baseline Report** that is appended to the patient's message so that all downstream agents can see the historical context.

**Input:** User context (profile, past diagnoses, severity history, medical reports) + current message.

---

### 4.9 Clinical SOPs (Standard Operating Procedures)

CuraBot implements 10 clinical SOPs. It is critical to understand that **SOPs are not step-by-step processes**. Instead, they function as **guardrails or constraints governing system and agent behavior**. These Clinical SOPs represent actual authoritative clinical standards and act as strict boundaries within which the AI must operate. They are implemented as pure Python rule-based logic. These SOPs run between Agent 1 (Symptom Normalizer) and Agent 2 (Hypothesis Generator), and again after Agent 5 (Diagnostic Strategist) for conclusion-phase checks. They add zero LLM latency because they are entirely rule-based.

| SOP | Name | What It Does |
|-----|------|-------------|
| SOP-006 | Triage Classification | Assigns a colour-coded triage level (Red/Orange/Yellow/Green/Blue) based on symptom severity, vital signs, and red flags. Red triggers an emergency override. |
| SOP-007 | Chest Pain Protocol | Evaluates ACS (Acute Coronary Syndrome) risk when chest pain is detected. Checks for associated symptoms like radiating arm pain and diaphoresis. |
| SOP-008 | FAST Stroke Protocol | Checks for FAST stroke indicators: Face drooping, Arm weakness, Speech difficulty, Time to act. If positive, triggers an immediate stroke alert with neurologist referral. |
| SOP-009 | Respiratory Distress | Assesses respiratory distress severity when breathing symptoms are detected. |
| SOP-010 | Vital Signs Interpreter | Analyses submitted vital signs (BP, HR, temp, SpO2, RR) against normal ranges and flags abnormalities. |
| SOP-011 | Lab Value Interpreter | Parses RAG-retrieved lab text for abnormal values (haemoglobin, WBC, glucose, creatinine, etc.) and flags clinical significance. |
| SOP-012 | Medication Safety | Cross-checks current medications against diagnosis to detect drug interactions and allergy conflicts. |
| SOP-013 | Red Flag Scanner | Scans symptoms and patient message for critical red flags (sudden severe headache, blood in stool, loss of consciousness, etc.). |
| SOP-014 | Specialist Routing | Maps the final diagnosis to the appropriate medical specialist (cardiologist, neurologist, gastroenterologist, etc.). |
| SOP-015 | Confidence Calibration | Evaluates the quality of evidence gathered (vitals provided? labs available? iteration count?) and determines whether the system has enough data to safely conclude. |

The SOPs work as safety guardrails. SOP-008 (Stroke) and SOP-006 (Red Triage) can **short-circuit** the entire pipeline — if stroke indicators are positive or a red triage is triggered, the system immediately returns an emergency response without running the remaining agents.

---

### 4.10 How the Agents Work Together

The six agents form a collaborative diagnostic reasoning chain where each agent builds upon the work of the previous one. Here is how they coordinate within a single pipeline run:

**Step 1 — Understanding the Patient (Agent 1):**
The Symptom Normalizer takes the raw patient message and converts it into structured medical data. It acts as the "ears" of the system, translating everyday language into a format the other agents can work with.

**Step 2 — Safety Checks (SOPs):**
Before any diagnosis happens, the clinical SOPs scan for immediate threats. The Red Flag Scanner (SOP-013) looks for critical warning signs, the Triage system (SOP-006) assigns an urgency level, and specialised protocols (SOP-007 for chest pain, SOP-008 for stroke) perform targeted emergency assessments. If a critical emergency is detected, the pipeline short-circuits and returns an immediate alert.

**Step 3 — Generating Possibilities (Agent 2):**
The Hypothesis Generator takes the normalised symptoms (accumulated across all conversation turns) and produces a ranked list of possible conditions. It considers the disease knowledge base, the patient's history (for returning users), and the severity of each candidate condition.

**Step 4 — Weighing the Evidence (Agent 3):**
The Evidence Evaluator examines every piece of available data — symptoms, vital signs, medical history, RAG-retrieved lab values — and determines how each piece of evidence supports or contradicts each hypothesis. It also identifies absent expected symptoms and missing evidence that would help differentiate between competing diagnoses.

**Step 5 — Updating Beliefs (Agent 4):**
The Hypothesis Reviser uses the evidence evaluation to update confidence scores using Bayesian-style reasoning. Strong supporting evidence boosts a hypothesis; contradicting evidence reduces it. Severity floors ensure dangerous conditions are not prematurely dismissed.

**Step 6 — Deciding the Next Move (Agent 5) and Quality Check (Agent 6):**
These two agents run in parallel. The Diagnostic Strategist decides whether to ask another question or conclude the diagnosis, while the Self-Critique agent checks for cognitive biases. The final confidence calibration (SOP-015) determines whether the system truly has enough evidence to conclude safely.

**Step 7 — Building the Response:**
The orchestrator assembles the final response from all agent outputs — the message (either a follow-up question or a conclusion), the hypothesis list, evidence items, bias flags, agent thoughts (for transparency), and diagnostic metadata. This structured response is sent to the frontend, which visualises it for the user.

**Across multiple iterations,** symptoms are accumulated (so they are not lost between turns), evidence is accumulated, and the confidence trajectory is tracked. Each iteration refines the hypothesis space, ideally converging on a single diagnosis with high confidence and sufficient margin.

---

### 4.11 Medical Evidence Citation Engine

**Purpose:** Provides verifiable, traceable medical references for every diagnostic claim, giving users proof that the system's reasoning is grounded in real medical science.

**What It Does:**
The Medical Evidence Citation Engine (`agents/medical_citations.py`) is a pure-Python module that generates structured citation packages for every concluded diagnosis. It maps each disease in the 275-entry knowledge base to:

- **ICD-10-CM codes** with direct links to the WHO International Classification of Diseases.
- **Clinical authority references** — the specific medical society whose guidelines govern that disease's body system (e.g., AHA for cardiovascular, CDC for infectious, AGA for gastrointestinal).
- **PubMed verification links** — auto-generated search URLs that allow users to independently verify any symptom-disease relationship in the peer-reviewed medical literature.

For each evidence item in the evidence ledger, the engine produces an individual citation that states:
1. Where the symptom was matched in the knowledge base (primary, secondary, or atypical symptom list).
2. Whether it matches a differentiating feature for that disease.
3. Which clinical authority's guidelines support the relationship.
4. A direct PubMed search link for independent verification.

**When It Runs:**
The citation engine activates only when the Diagnostic Strategist concludes a diagnosis. It generates a complete "proof package" that is:
- Appended to the conclusion message shown to the user (ICD-10 code, clinical authority, confirmatory tests, and verification note).
- Returned as a `medical_citations` field in the API response for the frontend to display.

**Example Output (appended to conclusion message):**
```
Medical Reference:
- ICD-10 Code: I21 (ICD-10-CM Code: I21 — WHO International Classification of Diseases)
- Clinical Authority: American Heart Association (AHA) Clinical Guidelines
- Confirmatory Tests: Troponin I/T, CK-MB, ECG (ST elevation), BNP, Lipid Profile
- All symptom-disease relationships for Acute Myocardial Infarction can be independently
  verified via the AHA guidelines, MedlinePlus, and the PubMed medical literature database.
```

**Key Design Decision:** This module makes zero LLM calls. All citations are generated deterministically from the validated knowledge base and the authoritative medical source registry, ensuring 100% consistency and zero hallucination risk in the proof layer.

---

> **End of LLD Version 1**
