# Low-Level Design (LLD): AI Safety & Architecture Documentation

## 1. Document Control

### 1.1 Document Header
- **Project:** CuraBot - Agentic AI Differential Diagnosis Tutor
- **System Name:** CuraBot Diagnostic Engine
- **Environment:** Development / Staging / Production
- **Confidentiality:** Confidential - Internal Use Only

### 1.2 Versioning & Change Log
| Version | Author | Description of Changes | Date | Status |
| :--- | :--- | :--- | :--- | :--- |
| v0.1 | Architecture Team | Initial draft for AI safety and LLD structure | 2026-04-22 | Draft |
| v0.2 | Security Lead | Added Threat Model and Data Sensitivity details | 2026-04-22 | Review |
| v1.0 | Project Sponsor | Final approval and sign-off | 2026-04-23 | **Approved** |

### 1.3 Approval Matrix
| Area | Reviewer | Approver | Evidence/Link |
| :--- | :--- | :--- | :--- |
| **Architecture** | Lead Architect | Architecture Review Board (ARB) | [ADR List (Architecture Decision Records)](#) |
| **Security** | Security Lead | CISO Delegate | [System Threat Model](#) |
| **Compliance** | Compliance SME | Compliance Board / AIRB | [Policy & Regulatory Checklist](#) |
| **Product** | Product Manager | VP of Product | [Business Requirements Document (BRD)](#) |
| **Ops** | Lead DevOps Engineer | Head of Operations | [Deployment & Test Plan](#) |

### 1.4 AI Safety Classification & Data Handling
- **AI Safety Classification:** **Non-Regulated (Medical Education Use Only)**. (Note: Should the system ever transition to real patient data, this will be escalated to **Regulated/High-Risk**).
- **Data Sensitivity Summary:** The system currently processes simulated patient cases. It handles **Simulated PHI/PII**. Strict data sanitization pipelines are in place to ensure no real patient data is ingested or retained.

### 1.5 AI Autonomy Level
- **Current Autonomy Level:** **L3 (Supervised Agent)**
- **Action Paradigm:** **Recommend-Only**. 
- **Description:** The AI generates hypotheses, evaluates evidence, and provides differential diagnoses for educational purposes. It operates strictly in a "recommendation" capacity and does not execute clinical actions, prescribe treatments, or act without explicit human oversight and approval.

### 1.6 Key Reference Artifacts
- 📄 [Business Requirements Document (BRD)](#)
- 📄 [High-Level Design (HLD)](#)
- 📄 [Architecture Decision Records (ADRs)](#)
- 📄 [Threat Model & Security Assessment](#)
- 📄 [Quality Assurance & Test Plan](#)

---

## 2. System Overview

### 2.1 Business Context and Stakeholders
The CuraBot Diagnostic Engine is designed to teach clinical reasoning concepts to medical professionals and students through simulated agentic workflows.
- **Primary Personas:** 
  - Medical Students (Primary Users)
  - Clinical Instructors / Educators (Curriculum Designers)
  - System Administrators
- **Consuming Teams:** University Medical Programs, Corporate Medical Training Departments.

### 2.2 Problem Statement
Medical education requires extensive, scalable, and personalized feedback on clinical reasoning to prevent diagnostic errors.
- **Pain Points:** 
  - High latency in receiving instructor feedback on simulated cases.
  - Significant manual effort required by instructors to design and monitor dynamic patient scenarios.
  - Difficulty in consistently identifying and correcting cognitive biases (e.g., anchoring bias, premature closure) during the learning process.

### 2.3 Scope Boundaries
| Category | Included (In-Scope) | Excluded (Out-of-Scope) |
| :--- | :--- | :--- |
| **User Journeys** | - Conducting simulated multi-stage diagnostic interviews (Max 10 turns).<br>- Tracking supporting/contradicting evidence.<br>- Real-time cognitive bias detection & feedback. | - Actual clinical diagnosis or treatment planning for real patients.<br>- Autonomous prescription generation. |
| **Integrations** | - 15 standardized Clinical SOPs.<br>- Gemini LLM integration for reasoning. | - Integration with live EHR/EMR systems.<br>- Direct ingestion of real-world patient charts. |

### 2.4 Success Metrics and KPIs
| Dimension | Metric / KPI | Baseline Approach |
| :--- | :--- | :--- |
| **Quality** | Reduction in cognitive bias occurrences during simulated cases. | Track bias flags per session over a student's semester. |
| **Time** | Agent response latency (Symptom to Hypothesis generation). | Maintain end-to-end response time under < 2.5 seconds. |
| **Cost / Effort** | Reduction in instructor hours per simulated case creation. | Measure time spent building vs. utilizing CuraBot scenarios. |
| **Compliance** | 100% adherence to Medical Education disclaimers. | Automated pre-flight checks on all UI rendering components. |

### 2.5 Assumptions and Constraints
- **Assumptions:** 
  - Users are authenticated and understand the purely educational nature of the platform.
  - The underlying LLM (Gemini) maintains consistent reasoning capabilities without sudden API deprecations.
- **Constraints:**
  - Strict limitation to a maximum of 10 interaction turns per diagnostic session to control API costs and prevent hallucination drift.
  - System must gracefully fallback if the LLM provider experiences downtime or throttling.

### 2.6 AI Autonomy Level Target
- **Current Target:** **L1 Assistant** transitioning to **L3 Supervised Agent** (Recommend-Only).
- **Future Considerations:** The system is explicitly designed *not* to exceed L3 autonomy to comply with safety guardrails regarding medical applications.
