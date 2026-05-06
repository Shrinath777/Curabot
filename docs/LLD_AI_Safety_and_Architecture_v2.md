# Low-Level Design (LLD): Agentic AI Applications
**Project:** CuraBot - Agentic AI Differential Diagnosis Tutor

---

## 1. Document Control & Metadata

### 1.1 Document Header
- **Project:** CuraBot - Agentic AI Differential Diagnosis Tutor
- **System Name:** CuraBot Diagnostic Engine
- **Environment:** Development / Staging / Production
- **Confidentiality:** Confidential - Internal Use Only

### 1.2 Versioning & Change Log
| Version | Author | Description of Changes | Date | Status |
| :--- | :--- | :--- | :--- | :--- |
| v0.1 | Architecture Team | Initial draft for AI safety and LLD structure | 2026-04-22 | Draft |
| v1.0 | Project Sponsor | Final complete documentation covering all 13 sections | 2026-04-22 | **Approved** |

### 1.3 Approval Matrix
| Area | Reviewer | Approver | Evidence/Link |
| :--- | :--- | :--- | :--- |
| **Architecture** | Lead Architect | ARB/TRB | [ADR list](#) |
| **Security** | Security Lead | CISO delegate | [Threat model](#) |
| **Compliance** | Compliance SME | AIRB/Compliance board | [Policy checklist](#) |
| **Product** | Product Manager | VP of Product | [BRD](#) |

### 1.4 AI Safety Classification & Data Handling
- **Classification:** **Non-Regulated (Medical Education Use Only)**
- **Data Sensitivity:** Handles **Simulated PHI/PII** for educational patient scenarios. However, the underlying knowledge base is built on **real-world, medically validated data for 275 diseases** sourced directly from clinical studies and authoritative medical websites. No real patient profiles are ingested.

### 1.5 AI Autonomy Level
- **Target:** **L3 Supervised Agent** (Recommend-Only). The AI cannot execute final clinical actions or prescribe treatments without human instructor approval.

---

## 2. System Overview

### 2.1 Business Context and Stakeholders
- **Primary Personas:** Medical Students (Users), Clinical Instructors (Curriculum Designers).
- **Consuming Teams:** University Medical Programs.

### 2.2 Problem Statement
- **Pain:** High latency in instructor feedback, manual effort required to design patient cases, difficulty catching cognitive biases (anchoring, premature closure) during diagnostic training.

### 2.3 Scope Boundaries
| Category | In-Scope | Out-of-Scope (Explicit Non-Goals) |
| :--- | :--- | :--- |
| **Journeys** | Simulated diagnostic interviews, real-time bias detection, 15 core Clinical SOPs. | Actual clinical diagnosis for real patients, autonomous prescription generation. |

### 2.4 Success Metrics & KPIs
- **Quality:** Reduction in cognitive bias occurrences during simulated cases.
- **Time:** Real-time agentic response latency (< 2.5 seconds).
- **Cost:** Reduction in instructor hours per simulated case creation.

### 2.5 Assumptions & Constraints
- **Assumptions:** Users understand the purely educational nature.
- **Constraints:** Strict 10-turn interaction limit to control LLM cost and drift.

---

## 3. Architecture Decomposition

### 3.1 C4 Context Diagram
The CuraBot Diagnostic Engine sits between the Medical Student UI, the Gemini LLM Gateway, and the Medical Knowledge Base (Vector DB).

![C4 Context Diagram](C:\Users\Admin\.gemini\antigravity\brain\e8a4a7ba-0852-4d6c-a381-d42c602a2b5a\c4_context_diagram_1776871948679.png)

### 3.2 C4 Container & Components
- **UI:** React 18.2 Dashboard (Glassmorphism UI).
- **API Gateway:** FastAPI Gateway handling auth and rate-limiting.
- **Orchestrator:** Python backend managing agent state and 10-turn limits.
- **Agent Runtime:** LangChain/Custom agent execution environment.
- **Data Stores:** ChromaDB/Pinecone for Vector Retrieval, Supabase for logging.

### 3.3 Deployment Topology
The system is deployed in a secure Kubernetes cluster with private endpoints separating the LLM gateway.

![Deployment Topology](C:\Users\Admin\.gemini\antigravity\brain\e8a4a7ba-0852-4d6c-a381-d42c602a2b5a\deployment_topology_1776871969165.png)

---

## 4. GenAI Capability Design

### 4.1 RAG Pipeline Flow
- **Approach:** Vector-RAG with Metadata filtering (hybrid).
- **Pipeline:** Ingest Medical SOPs → Chunk by logical section → Embed using standard text-embedding models → Vector Index → Retrieve top-K → Generate Answer → Validate Schema.

![RAG Pipeline](C:\Users\Admin\.gemini\antigravity\brain\e8a4a7ba-0852-4d6c-a381-d42c602a2b5a\rag_pipeline_flow_1776871989004.png)

### 4.2 Guardrails & Confidence Scoring
- **Grounding Policy:** "Answer only from retrieved evidence."
- **Guardrails:** Prompt-injection mitigation via standard system prompts; output validation strictly enforcing JSON schemas for agent outputs.

---

## 5. Agentic Design

### 5.1 Agent Inventory
| Agent | Type | Inputs | Outputs | Tools Allowed | Cannot Do |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Symptom Normalizer** | Utility | Raw text | Standardized medical terms | SNOMED mapping | No diagnosis |
| **Hypothesis Generator** | Specialist | Symptoms | Differential Diagnosis list | Vector Search | No treatment |
| **Evidence Evaluator** | Governance | Hypotheses + new data | Updated Bayesian weights | Evidence validation | No final action |

### 5.2 Orchestration Graph
The orchestrator dictates the workflow graph, coordinating specialist agents through human-in-the-loop checkpoints.

![Agent Orchestration Graph](C:\Users\Admin\.gemini\antigravity\brain\e8a4a7ba-0852-4d6c-a381-d42c602a2b5a\agent_orchestration_1776872005064.png)

---

## 6. Data & Knowledge Fabric
- **Sources:** 15 Standardized Clinical SOPs, and a medically validated Knowledge Base containing real-world symptom and diagnostic data for **275 distinct diseases**, sourced from verified medical websites and clinical studies.
- **Ingestion:** Extract → Normalize → Chunk → Embed → Index.
- **Caching:** Semantic cache for common medical queries; TTL set to 24 hours.
- **Retention Policies:** Strictly no retention of actual PHI; simulated logs retained for 30 days for instructor review.

---

## 7. API & Service Design
- **API Gateway:** Centralized routing.
- **Endpoints:**
  - `POST /api/v1/chat` (Must-have): Sends user message, returns agent thought streams.
  - `GET /api/v1/case/{id}` (Must-have): Retrieves specific scenario data.
- **Error Handling:** Retries/backoff for LLM API timeouts; graceful degradation with fallback to cached "standard" responses.

---

## 8. Security & Governance
- **LLM Gateway:** All calls route through a single secure gateway applying policy-as-code.
- **RBAC:** Medical Students (read/interact), Instructors (write scenarios), Admin (system config).
- **Audit Trails:** Complete retention of prompts, retrieved chunks, and final outputs in a secure log schema.
- **FinOps:** Token usage monitoring with hard caps at 10 turns per session.

---

## 9. Non-Functional Design
| Metric | Target | Notes |
| :--- | :--- | :--- |
| **Performance (Latency)** | p95 < 2.5s | Time from query to first generated token. |
| **Scalability** | HPA | Horizontal Pod Autoscaling based on queue depth. |
| **Availability** | 99.9% | Multi-zone failover within the region. |
| **Security** | Zero-Trust | Secret rotation every 30 days, regular vulnerability scanning. |

---

## 10. Observability & Evaluation
- **Telemetry:** Enforced end-to-end correlation IDs tracing a student's session across all agent nodes.
- **RAG Evaluation:** Offline harness testing precision/recall of the top-5 retrieved medical SOPs.
- **Dashboards:** Monitoring latency, API cost/tokens, and safety flag overrides.
- **A/B Testing:** Canary rollout for new System Prompt versions.

---

## 11. SDLC Integration
- **CI/CD Stages:** Lint → Test → Security Scan → Build → Deploy → AI Regression Test.
- **Quality Gates:** Prompt validation and policy compliance before merge.
- **Drift Detection:** Triggering documentation updates via webhooks when Agent definitions change.
- **Release Governance:** Clear rollback runbooks; kill-switch defaults agents to "recommend-only".

---

## 12. Risks & Failure Modes
| Risk | Detection Signal | Mitigation / Fallback |
| :--- | :--- | :--- |
| **Hallucination** | Low generation confidence | Grounding policy; fallback to deterministic rules. |
| **Prompt Injection** | Policy violation spike | Safe refusal; disable tool access temporarily. |
| **Cost Spikes** | FinOps alert | Hard cap on tokens; disable complex agents, use simpler models. |

---

## 13. Appendix
- **Reference Diagrams:** [C4 Context Diagram](#31-c4-context-diagram), [Deployment Topology](#33-deployment-topology).
- **Glossary:** 
  - *SOP:* Standard Operating Procedure (functions as guardrails or constraints governing system and agent behavior, rather than a step-by-step process; treated as authoritative clinical standards)
  - *PHI:* Protected Health Information
  - *LLM:* Large Language Model
  - *RAG:* Retrieval-Augmented Generation
