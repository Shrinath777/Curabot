"""
Agent 2: Hypothesis Generation Agent
Generates a broad hypothesis space (possible diseases) with initial Bayesian priors.
Uses disease knowledge base + LLM reasoning.

KEY FIXES:
- Discriminating symptom bonus (unique symptoms get extra weight)
- Severity weighting (critical diseases boosted)
- Prevalence weighting
- Confidence always normalized to sum to 100%
- differentiating_features passed to LLM prompt
"""

import json
import logging
from typing import Dict, Any, List, Optional
from services.llm_client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a differential diagnosis specialist for MEDICAL EDUCATION purposes only.

Given normalized symptoms and a disease knowledge base, you must generate a ranked list of possible diagnoses (hypotheses) with initial confidence scores.

Rules:
1. RULE-04: BROAD DIFFERENTIAL — Always consider at least 3-5 possible diagnoses spanning Common, Uncommon, and Dangerous categories.
2. Assign initial confidence based on symptom match, prevalence, and risk factors.
3. For NEW patients, cast a wide net — consider common AND dangerous diagnoses.
4. For RETURNING patients, factor in their medical history and past conditions.
5. Confidence scores must sum to exactly 100% across all hypotheses.
6. RULE-01: EMERGENCY TRIAGE — Always include at least one "must-not-miss" dangerous diagnosis (e.g., MI, PE) if red flag symptoms like chest pain or dyspnea are present.
7. Provide clear reasoning for each hypothesis.

SEVERITY-AWARE SCORING:
8. For symptoms like chest_pain that appear in MANY diseases — use the differentiating_features to assign DIFFERENT confidence levels based on what the patient described.
9. Critical severity diseases should get a minimum 8% confidence when their key symptoms are present.
10. Consider the SPECIFICITY of each symptom match: a symptom matching a disease's differentiating_features deserves more weight than a generic primary symptom match.
11. NEVER give two diseases identical confidence scores — use specificity, severity, and prevalence to differentiate."""

GENERATION_PROMPT = """Based on the following normalized symptoms and disease knowledge, generate differential diagnoses.

NORMALIZED SYMPTOMS:
{symptoms_json}

DISEASE KNOWLEDGE BASE (with severity and differentiating features):
{disease_kb}

{user_context}

IMPORTANT INSTRUCTIONS:
- Confidence scores MUST sum to exactly 100%
- For shared symptoms (like chest_pain), use differentiating_features to assign different scores
- ALWAYS include at least one critical-severity disease if relevant symptoms exist
- NO two diseases should have identical confidence scores

Generate a ranked differential diagnosis list. Respond in this exact JSON format:
{{
  "hypotheses": [
    {{
      "name": "Disease Name",
      "confidence": 45.0,
      "reasoning": "Why this diagnosis is considered — specific symptom matches and clinical reasoning",
      "category": "must_not_miss / common / less_likely",
      "severity_class": "critical/serious/moderate/benign",
      "key_features_present": ["symptom1", "symptom2"],
      "key_features_absent": ["symptom that would strengthen this if present"],
      "differentiating_factor": "What makes this disease different from competing diagnoses",
      "initial_prior": "Based on prevalence and symptom match"
    }}
  ],
  "reasoning_summary": "Brief summary of differential reasoning process",
  "dominant_system": "cardiovascular/respiratory/gastrointestinal/etc"
}}"""


# ============================================================================
# NEGATIVE EXCLUSION RULES: Symptoms that CONTRADICT a diagnosis when present
# If a patient has these symptoms, the named disease is heavily penalized.
# penalty = multiplier applied per contradicting symptom found (lower = stronger)
# ============================================================================
NEGATIVE_EXCLUSIONS = {
    # Bell's Palsy vs Stroke: Bell's has NO arm/leg weakness
    "Bell's Palsy": {
        "exclude_if_present": ["arm_weakness", "leg_weakness", "hemiplegia", "hemiparesis"],
        "penalty": 0.15
    },
    # Anxiety Disorder: deprioritize when cardiac symptoms dominate
    "Anxiety Disorder": {
        "exclude_if_present": ["chest_pain", "dyspnea", "diaphoresis"],
        "penalty": 0.4
    },
    "Generalized Anxiety Disorder": {
        "exclude_if_present": ["chest_pain", "dyspnea", "diaphoresis"],
        "penalty": 0.4
    },
    # IBS: no alarm features
    "Irritable Bowel Syndrome": {
        "exclude_if_present": ["weight_loss", "hematochezia", "fever", "anemia"],
        "penalty": 0.25
    },
    # Asthma vs pneumonia/COVID: asthma has no fever typically
    "Asthma": {
        "exclude_if_present": ["high_fever", "productive_cough"],
        "penalty": 0.5
    },
    # GERD vs cardiac: GERD shouldn't have arm pain or diaphoresis
    "Gastroesophageal Reflux Disease": {
        "exclude_if_present": ["arm_pain", "diaphoresis", "jaw_pain"],
        "penalty": 0.3
    },
    "Gastroesophageal Reflux Disease (GERD)": {
        "exclude_if_present": ["arm_pain", "diaphoresis", "jaw_pain"],
        "penalty": 0.3
    },
    # Spinal Cord Injury: should not appear for GI/respiratory symptoms
    "Spinal Cord Injury": {
        "exclude_if_present": ["abdominal_pain", "nausea", "vomiting", "diarrhea",
                               "heartburn", "cough", "fever", "dyspnea"],
        "penalty": 0.15
    },
    # Osteonecrosis: should not appear for systemic/respiratory symptoms
    "Osteonecrosis": {
        "exclude_if_present": ["fever", "cough", "dyspnea", "diarrhea", "vomiting",
                               "chest_pain", "headache", "rash"],
        "penalty": 0.15
    },
    # Epidermolysis Bullosa: rare genetic condition, should not appear unless skin-specific
    "Epidermolysis Bullosa": {
        "exclude_if_present": ["chest_pain", "dyspnea", "fever", "cough",
                               "abdominal_pain", "headache", "diarrhea"],
        "penalty": 0.1
    },
    # Acute Mesenteric Ischemia: elderly patients with severe acute onset, not chronic symptoms
    "Acute Mesenteric Ischemia": {
        "exclude_if_present": ["heartburn", "relief_with_antacids", "bloating",
                               "alternating_bowel_habit", "stress_related"],
        "penalty": 0.25
    },
    # Necrotizing Fasciitis: needs wound/surgical site
    "Necrotizing Fasciitis": {
        "exclude_if_present": ["heartburn", "regurgitation", "bloating",
                               "rhinorrhea", "sneezing"],
        "penalty": 0.15
    },
    # Tracheal Cancer: rare, should not appear for common fever/cough
    "Tracheal Cancer": {
        "exclude_if_present": ["fever", "chills", "diarrhea", "vomiting",
                               "joint_pain", "rash"],
        "penalty": 0.15
    },
    # Compartment Syndrome: needs trauma/fracture history
    "Compartment Syndrome": {
        "exclude_if_present": ["fever", "cough", "headache", "diarrhea",
                               "nausea", "rash", "dyspnea", "urticaria",
                               "throat_swelling", "angioedema", "hives",
                               "generalized_urticaria", "allergen_exposure"],
        "penalty": 0.1
    },
    # Stroke (CVA): should be penalized when Bell's Palsy features present (no limb weakness)
    "Stroke (CVA)": {
        "exclude_if_present": ["isolated_facial", "taste_disturbance", "ear_pain"],
        "penalty": 0.3
    },
    "Ischemic Stroke": {
        "exclude_if_present": ["isolated_facial", "taste_disturbance", "ear_pain"],
        "penalty": 0.3
    },
    "Transient Ischemic Attack": {
        "exclude_if_present": ["isolated_facial", "taste_disturbance", "ear_pain"],
        "penalty": 0.35
    },
    # Fatal Insomnia: rare prion disease, should not appear for depression
    "Fatal insomnia": {
        "exclude_if_present": ["depressed_mood", "anhedonia", "hopelessness",
                               "worthlessness", "persistent_sadness", "hypersomnia"],
        "penalty": 0.1
    },
    # Acute Myocardial Infarction: penalize when key PE differentiators are present
    "Acute Myocardial Infarction": {
        "exclude_if_present": ["recent_surgery", "prolonged_immobility",
                               "pleuritic_chest_pain", "calf_inflammation",
                               "homans_sign"],
        "penalty": 0.5
    },
    # Myocardial Infarction (duplicate name variant)
    "Myocardial Infarction": {
        "exclude_if_present": ["recent_surgery", "prolonged_immobility",
                               "pleuritic_chest_pain", "calf_inflammation",
                               "homans_sign"],
        "penalty": 0.5
    },
    # Adrenal Insufficiency: rare, shouldn't appear for classic diabetes symptoms
    "Adrenal Insufficiency": {
        "exclude_if_present": ["family_history_diabetes", "obesity",
                               "poor_wound_healing", "peripheral_neuropathy"],
        "penalty": 0.25
    },
    # Thyroid Storm: shouldn't appear for slow-onset diabetes symptoms
    "Thyroid Storm": {
        "exclude_if_present": ["polyuria", "polydipsia", "poor_wound_healing",
                               "peripheral_neuropathy", "family_history_diabetes"],
        "penalty": 0.2
    },
    # Gallstones: penalize when hepatitis-specific features present
    "Gallstones": {
        "exclude_if_present": ["sexual_exposure", "cholestatic_pattern",
                               "dark_urine", "pale_stool"],
        "penalty": 0.4
    },
    # Actinic Keratosis: sun-related, not eczema pattern
    "Actinic Keratosis": {
        "exclude_if_present": ["flexural_distribution", "childhood_onset",
                               "weeping_lesions", "seasonal_worsening"],
        "penalty": 0.15
    },
    # COVID-19: differentiate from Influenza
    "COVID-19": {
        "exclude_if_present": ["seasonal_pattern", "workplace_outbreak"],
        "penalty": 0.5
    },
    # Necrotizing Enterocolitis: neonatal disease
    "Necrotizing Enterocolitis": {
        "exclude_if_present": ["heavy_alcohol_use", "positional_relief",
                               "radiating_back_pain", "epigastric_pain"],
        "penalty": 0.1
    },
    # Acute Mesenteric Ischemia: elderly vascular emergency
    "Acute Mesenteric Ischemia": {
        "exclude_if_present": ["heavy_alcohol_use", "positional_relief",
                               "foodborne_exposure", "household_outbreak",
                               "restaurant"],
        "penalty": 0.2
    },
    # Hemophilia A: genetic bleeding disorder, not anaphylaxis
    "Hemophilia A": {
        "exclude_if_present": ["urticaria", "angioedema", "throat_swelling",
                               "allergen_exposure", "wheezing", "hives"],
        "penalty": 0.1
    },
    # Mild Sprain: mechanical injury, not allergic
    "Mild Sprain": {
        "exclude_if_present": ["urticaria", "angioedema", "throat_swelling",
                               "allergen_exposure", "wheezing", "hives"],
        "penalty": 0.1
    },
    # Necrotizing Fasciitis: severe soft tissue infection, not metabolic/endocrine
    "Necrotizing Fasciitis": {
        "exclude_if_present": ["fruity_breath", "diabetes_history", "excessive_thirst",
                               "frequent_urination", "polyuria", "insulin",
                               "facial_drooping", "facial_weakness"],
        "penalty": 0.1
    },
    # Status Epilepticus: prolonged seizure, not for DKA pattern
    "Status epilepticus": {
        "exclude_if_present": ["fruity_breath", "excessive_thirst", "frequent_urination",
                               "insulin", "diabetes_history"],
        "penalty": 0.2
    },
    "Serious Status Epilepticus": {
        "exclude_if_present": ["fruity_breath", "excessive_thirst", "frequent_urination",
                               "insulin", "diabetes_history"],
        "penalty": 0.2
    },
    # Migraine: penalize when meningitis signs present
    "Migraine": {
        "exclude_if_present": ["neck_stiffness", "petechiae", "non_blanching_rash",
                               "facial_drooping", "facial_weakness", "isolated_facial",
                               "taste_disturbance", "ear_pain"],
        "penalty": 0.25
    },
    "Migraine with aura": {
        "exclude_if_present": ["neck_stiffness", "petechiae", "non_blanching_rash",
                               "facial_drooping", "facial_weakness"],
        "penalty": 0.25
    },
    # Tension-type Headache: not meningitis pattern
    "Tension-type Headache": {
        "exclude_if_present": ["neck_stiffness", "petechiae", "non_blanching_rash",
                               "high_fever", "confusion",
                               "facial_drooping", "facial_weakness", "isolated_facial"],
        "penalty": 0.2
    },
    "Tension Headache": {
        "exclude_if_present": ["neck_stiffness", "petechiae", "non_blanching_rash",
                               "high_fever", "confusion",
                               "facial_drooping", "facial_weakness", "isolated_facial"],
        "penalty": 0.2
    },
    # Multiple sclerosis: should not appear over Bell's Palsy
    "Multiple sclerosis": {
        "exclude_if_present": ["isolated_facial", "ear_pain", "taste_disturbance"],
        "penalty": 0.3
    },
    # Depression: should not override anxiety when panic/impending doom present
    "Depression": {
        "exclude_if_present": ["panic_episodes", "impending_doom", "brief_episodes",
                               "chest_tightness"],
        "penalty": 0.4
    },
    "Major Depressive Disorder": {
        "exclude_if_present": ["panic_episodes", "impending_doom", "brief_episodes",
                               "chest_tightness"],
        "penalty": 0.4
    },
    # Peptic Ulcer Disease: penalize when hepatitis features dominate
    "Peptic Ulcer Disease": {
        "exclude_if_present": ["jaundice", "dark_urine", "pale_stool",
                               "sexual_exposure", "cholestatic_pattern"],
        "penalty": 0.3
    },
    # Gastrointestinal Perforation: shouldn't appear for jaundice/hepatitis
    "Gastrointestinal Perforation": {
        "exclude_if_present": ["jaundice", "dark_urine", "pale_stool",
                               "sexual_exposure", "cholestatic_pattern"],
        "penalty": 0.2
    },
    # Acute Mesenteric Ischemia: strengthen exclusion for appendicitis
    "Acute Mesenteric Ischemia": {
        "exclude_if_present": ["right_lower_quadrant_pain", "periumbilical_pain",
                               "pain_migration", "pain_migration_rlq",
                               "heavy_alcohol_use", "positional_relief",
                               "foodborne_exposure", "household_outbreak"],
        "penalty": 0.2
    },
    # Epilepsy: not for facial palsy
    "Epilepsy": {
        "exclude_if_present": ["facial_drooping", "facial_weakness", "isolated_facial",
                               "taste_disturbance", "ear_pain"],
        "penalty": 0.25
    },
}


class HypothesisGeneratorAgent:
    """Agent 2: Generates differential diagnosis hypotheses using LLM + disease KB."""

    def __init__(self):
        self.disease_kb = self._load_disease_kb()

    def _load_disease_kb(self) -> List[Dict]:
        """Load disease knowledge base."""
        try:
            import os
            kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")
            with open(kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load disease KB: {e}")
            return []

    def _score_disease(self, disease: Dict, normalized_symptoms: Dict[str, Any]) -> int:
        """Heuristic scorer to fast-filter massive diseases.json datasets."""
        score = 0
        
        # Flatten patient symptoms — handle BOTH key formats:
        # LLM returns: {"primary_symptoms": [{"name":"chest_pain",...}], ...}
        # Some paths return: {"primary": ["chest_pain", ...]}
        patient_symps = set()
        for cat_base in ["primary", "secondary", "atypical", "red_flags"]:
            # Try both key formats
            for cat_key in [cat_base, f"{cat_base}_symptoms"]:
                items = normalized_symptoms.get(cat_key, [])
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("name", "")
                        if name:
                            patient_symps.add(name.lower())
                    elif isinstance(item, str):
                        patient_symps.add(item.lower())
            
        if not patient_symps:
            return 1 # Baseline score if patient hasn't provided much
            
        # Flatten disease symptoms
        dis_symps = set()
        s_dict = disease.get("symptoms", {})
        if isinstance(s_dict, dict):
            for cat in ["primary", "secondary", "atypical"]:
                dis_symps.update([str(s).lower() for s in s_dict.get(cat, [])])
                
        # 1. Exact overlap bonus
        overlap = patient_symps.intersection(dis_symps)
        score += len(overlap) * 10
        
        # 2. Fuzzy partial string match (e.g., 'chest_pain' in 'sharp_chest_pain')
        for px in patient_symps:
            for dx in dis_symps:
                if px in dx or dx in px:
                    score += 2
                    
        # 3. Safety baseline: slightly bump critical/serious conditions so they are never accidentally purged
        sev = disease.get("severity_class", "").lower()
        if sev == "critical": score += 2
        elif sev == "serious": score += 1
        
        return score

    async def process(
        self,
        normalized_symptoms: Dict[str, Any],
        user_context: Optional[Dict] = None,
        is_new_user: bool = True,
    ) -> Dict[str, Any]:
        """Generate differential diagnosis hypotheses."""
        # Build user context string
        context_str = ""
        if not is_new_user and user_context:
            context_str = "RETURNING PATIENT CONTEXT:\n"
            profile = user_context.get("profile", {})
            if profile.get("known_conditions"):
                context_str += f"- Known conditions: {', '.join(profile['known_conditions'])}\n"
            if profile.get("medications"):
                context_str += f"- Current medications: {', '.join(profile['medications'])}\n"
            if profile.get("allergies"):
                context_str += f"- Allergies: {', '.join(profile['allergies'])}\n"

            past_dx = user_context.get("past_diagnoses", [])
            if past_dx:
                context_str += "- Previous diagnoses:\n"
                for dx in past_dx[:3]:
                    hyps = dx.get("final_hypotheses", [])
                    if hyps and isinstance(hyps, list) and len(hyps) > 0:
                        context_str += f"  * {hyps[0].get('name', 'Unknown')}\n"

            reports = user_context.get("medical_reports", [])
            if reports:
                context_str += "- Medical reports on file:\n"
                for rpt in reports[:3]:
                    context_str += f"  * {rpt.get('report_type', 'Unknown')}: {rpt.get('extracted_text', '')[:200]}\n"

        # Dynamic Context Filtering (Top 40)
        # Prevents LLM Payload Too Large constraints on >200 disease sets
        scored_diseases = []
        for d in self.disease_kb:
            score = self._score_disease(d, normalized_symptoms)
            scored_diseases.append((score, d))
            
        # Sort descending by score
        scored_diseases.sort(key=lambda x: x[0], reverse=True)
        top_diseases = [item[1] for item in scored_diseases[:10]]
        
        logger.info(f"Filtering {len(self.disease_kb)} DB items down to Top {len(top_diseases)} for EXTREME Context Compression.")

        # EXTREME COMPRESSION: Omit Raw Symptoms & Prevalence to easily bypass 30,000 TPM limit
        kb_summary = json.dumps([{
            "name": d["name"],
            "severity_class": d.get("severity_class", "moderate"),
            "differentiating_features": d.get("differentiating_features", []),
        } for d in top_diseases], indent=2)

        prompt = GENERATION_PROMPT.format(
            symptoms_json=json.dumps(normalized_symptoms, indent=2),
            disease_kb=kb_summary,
            user_context=context_str
        )

        result = await llm_client.generate(
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            expect_json=True
        )

        if result.get("fallback") or result.get("parse_error"):
            return self._fallback_hypotheses(normalized_symptoms)

        # Ensure hypotheses exist and have required fields
        hypotheses = result.get("hypotheses", [])
        for h in hypotheses:
            h.setdefault("confidence", 30.0)
            h.setdefault("reasoning", "")
            h.setdefault("supporting", 0)
            h.setdefault("contradicting", 0)
            h.setdefault("severity_class", "moderate")

        # Normalize to 100%
        total_conf = sum(h["confidence"] for h in hypotheses)
        if total_conf > 0 and abs(total_conf - 100.0) > 1.0:
            for h in hypotheses:
                h["confidence"] = round(h["confidence"] / total_conf * 100, 1)

        # Sort by confidence
        hypotheses.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        result["hypotheses"] = hypotheses[:5]  # Top 5

        return result

    def _fallback_hypotheses(self, symptoms: Dict) -> Dict[str, Any]:
        """Fallback hypothesis generation with discriminating symptom bonus and severity weighting."""
        primary = symptoms.get("primary_symptoms", [])
        secondary = symptoms.get("secondary_symptoms", [])
        all_patient_symptoms = primary + secondary

        def normalize(name: str) -> str:
            return name.lower().replace("_", " ").replace("-", " ").strip()

        symptom_names_normalized = [normalize(s.get("name", "")) for s in all_patient_symptoms]

        # ================================================================
        # BODY-SYSTEM COHERENCE: Determine the dominant symptom system
        # ================================================================
        from collections import Counter
        system_counts = Counter()
        for s in all_patient_symptoms:
            sys = s.get("body_system", s.get("system", "unknown")).lower()
            if sys and sys != "unknown" and sys != "general":
                system_counts[sys] += 1

        total_system_syms = sum(system_counts.values())
        dominant_system = ""
        dominant_system_ratio = 0.0
        if system_counts:
            dominant_system, dom_count = system_counts.most_common(1)[0]
            dominant_system_ratio = dom_count / max(total_system_syms, 1)

        # Severity and prevalence weights — REDUCED critical bias to prevent
        # rare critical diseases from dominating over well-matched common ones
        SEVERITY_WEIGHT = {"critical": 1.08, "serious": 1.04, "moderate": 1.0, "benign": 0.92}
        PREVALENCE_WEIGHT = {
            "very_common": 1.15, "common": 1.05,
            "common_in_tropics": 1.0, "common_in_endemic_areas": 1.0,
            "common_in_outbreaks": 0.95, "common_in_diabetics": 0.95,
            "common_in_pregnancy": 0.95, "common_in_developing_countries": 0.95,
            "common_in_icu": 0.9, "very_common_in_older_men": 1.0,
            "uncommon": 0.85, "uncommon_but_dangerous": 0.9,
            "uncommon_but_life_threatening": 0.9,
            "rare": 0.75, "rare_but_life_threatening": 0.8,
        }

        # First pass: find ALL matching diseases and their symptoms
        all_matches = []
        all_disease_symptom_sets = {}

        for disease in self.disease_kb:
            disease_symptoms = []
            if isinstance(disease.get("symptoms"), dict):
                disease_symptoms = (
                    disease["symptoms"].get("primary", []) +
                    disease["symptoms"].get("secondary", []) +
                    disease["symptoms"].get("atypical", [])
                )
            elif isinstance(disease.get("symptoms"), list):
                disease_symptoms = disease["symptoms"]

            disease_symptoms_normalized = [normalize(ds) for ds in disease_symptoms]
            all_disease_symptom_sets[disease["name"]] = set(disease_symptoms_normalized)

            match_count = 0
            matched_symptoms = []
            for patient_sym in symptom_names_normalized:
                for ds_norm, ds_orig in zip(disease_symptoms_normalized, disease_symptoms):
                    # Exact match
                    if patient_sym == ds_norm:
                        match_count += 1
                        matched_symptoms.append(ds_orig)
                        break
                    # Substring match: require the shorter string to be >5 chars
                    # AND cover >65% of the longer string to prevent generic matches
                    # like 'weakness' matching 'muscle_weakness'
                    elif len(patient_sym) > 5 and len(ds_norm) > 5:
                        shorter = min(len(patient_sym), len(ds_norm))
                        longer = max(len(patient_sym), len(ds_norm))
                        if (patient_sym in ds_norm or ds_norm in patient_sym) and shorter / longer > 0.65:
                            match_count += 1
                            matched_symptoms.append(ds_orig)
                            break

            if match_count == 0:
                # Check system matches and description
                for ps in all_patient_symptoms:
                    ps_system = ps.get("body_system", "").lower()
                    if ps_system != "unknown" and ps_system == disease.get("system", "").lower():
                        match_count += 0.5

                raw_text = symptoms.get("summary", "").lower()
                if disease["name"].lower() in raw_text or any(k in raw_text for k in disease.get("risk_factors", [])):
                    match_count += 1

            if match_count > 0:
                all_matches.append({
                    "disease": disease,
                    "match_count": match_count,
                    "matched_symptoms": matched_symptoms,
                })

        # Second pass: calculate discriminating symptom bonus
        hypotheses = []
        for match_info in all_matches:
            disease = match_info["disease"]
            match_count = match_info["match_count"]
            matched_symptoms = match_info["matched_symptoms"]

            # Count discriminating symptoms (unique to this disease among candidates)
            disease_syms = all_disease_symptom_sets.get(disease["name"], set())
            other_disease_syms = set()
            for other in all_matches:
                if other["disease"]["name"] != disease["name"]:
                    other_disease_syms.update(all_disease_symptom_sets.get(other["disease"]["name"], set()))

            unique_symptoms = disease_syms - other_disease_syms
            unique_matched = 0
            for ms in matched_symptoms:
                if normalize(ms) in unique_symptoms:
                    unique_matched += 1

            # Calculate confidence with IMPROVED formula
            primary_syms = disease.get("symptoms", {}).get("primary", []) if isinstance(disease.get("symptoms"), dict) else []
            all_disease_syms = disease_syms
            total_primary = max(len(primary_syms), 1)
            total_all = max(len(all_disease_syms), 1)
            match_ratio = match_count / total_primary

            # Base score from match ratio (0-60 range, increased from 0-50)
            base = min(match_ratio * 60, 60)

            # Match coverage: penalize diseases where patient matches <20% of all symptoms
            # This prevents diseases with huge symptom lists from scoring high on 1-2 generic matches
            coverage = match_count / total_all
            if coverage < 0.15 and match_count <= 1:
                base *= 0.25  # Very heavy penalty for weak single-symptom matches
            elif coverage < 0.1 and match_count <= 2:
                base *= 0.4  # Heavy penalty for very low coverage even with 2 matches

            # Discriminating symptom bonus (+12 per unique match, up from +10)
            disc_bonus = unique_matched * 12

            # Severity weight
            severity = disease.get("severity_class", "moderate")
            sev_weight = SEVERITY_WEIGHT.get(severity, 1.0)

            # Prevalence weight
            prev_weight = PREVALENCE_WEIGHT.get(disease.get("prevalence", "common"), 1.0)

            # Differentiating features bonus: if patient symptoms match any differentiating feature
            diff_bonus = 0
            diff_features = disease.get("differentiating_features", [])
            raw_text = symptoms.get("summary", "").lower()
            for df in diff_features:
                df_lower = df.lower()
                for ps in symptom_names_normalized:
                    if ps in df_lower or any(word in df_lower for word in ps.split() if len(word) > 3):
                        diff_bonus += 7
                        break

            confidence = (base + disc_bonus + diff_bonus) * sev_weight * prev_weight

            # Minimum for critical diseases — REDUCED from 12 to 5 to prevent
            # rare critical diseases from floating above well-matched common ones
            if severity == "critical" and match_count >= 2:
                confidence = max(confidence, 5.0)

            # ================================================================
            # NEGATIVE EXCLUSION: Penalize diseases contradicted by present symptoms
            # ================================================================
            contradicting_count = 0
            exclusion_rules = NEGATIVE_EXCLUSIONS.get(disease["name"], {})
            exclude_if_present = exclusion_rules.get("exclude_if_present", [])
            for excl_sym in exclude_if_present:
                excl_norm = normalize(excl_sym)
                if excl_norm in symptom_names_normalized or any(
                    excl_norm in ps or ps in excl_norm for ps in symptom_names_normalized
                ):
                    contradicting_count += 1

            if contradicting_count > 0:
                # Strong penalty: each contradicting symptom reduces confidence significantly
                penalty = exclusion_rules.get("penalty", 0.3)
                confidence *= penalty ** contradicting_count

            # ================================================================
            # BODY-SYSTEM COHERENCE: Boost diseases matching dominant symptom system
            # ================================================================
            disease_system = disease.get("system", "").lower()
            if dominant_system and dominant_system != "unknown":
                # Use substring matching: 'gastrointestinal' matches 'gastrointestinal/hepatic'
                system_match = (
                    disease_system == dominant_system or
                    dominant_system in disease_system or
                    disease_system in dominant_system
                )
                if system_match:
                    confidence *= 1.4  # Boost matching system
                elif disease_system and not system_match:
                    # Only penalize if there's a clear dominant system (>= 60% of symptoms)
                    if dominant_system_ratio >= 0.6:
                        confidence *= 0.7  # Penalize mismatched system

            reasoning_parts = [
                f"Matched {match_count} symptom(s): {', '.join(matched_symptoms[:4])}",
            ]
            if unique_matched > 0:
                reasoning_parts.append(f"{unique_matched} discriminating symptom(s)")
            if diff_bonus > 0:
                reasoning_parts.append(f"Differentiating features matched")
            if contradicting_count > 0:
                reasoning_parts.append(f"{contradicting_count} contradicting symptom(s)")

            cpc = disease.get("chest_pain_characteristics", {})
            if cpc and any("chest" in s for s in symptom_names_normalized):
                if cpc.get("character"):
                    reasoning_parts.append(f"Character: {cpc['character'][:80]}")

            hypotheses.append({
                "name": disease["name"],
                "confidence": round(confidence, 1),
                "reasoning": ". ".join(reasoning_parts),
                "category": "must_not_miss" if severity == "critical" else "common" if severity in ("moderate", "benign") else "serious",
                "severity_class": severity,
                "supporting": match_count,
                "contradicting": contradicting_count,
                "key_features_present": matched_symptoms,
                "differentiating_factor": diff_features[0] if diff_features else "",
            })

        if not hypotheses:
            hypotheses = [{
                "name": "Unspecified Condition",
                "confidence": 100.0,
                "reasoning": "Insufficient symptom data for differential diagnosis. Please provide more clinical details.",
                "category": "less_likely",
                "severity_class": "moderate",
                "supporting": 0,
                "contradicting": 0,
            }]

        # Normalize confidences to sum to 100%
        total_conf = sum(h["confidence"] for h in hypotheses)
        if total_conf > 0:
            for h in hypotheses:
                h["confidence"] = round(h["confidence"] / total_conf * 100, 1)

        # Ensure no exact ties — add small epsilon based on severity
        hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        for i in range(len(hypotheses) - 1):
            if hypotheses[i]["confidence"] == hypotheses[i + 1]["confidence"]:
                # Break tie: boost higher severity
                sev_i = SEVERITY_WEIGHT.get(hypotheses[i].get("severity_class", "moderate"), 1.0)
                sev_j = SEVERITY_WEIGHT.get(hypotheses[i + 1].get("severity_class", "moderate"), 1.0)
                if sev_i >= sev_j:
                    hypotheses[i]["confidence"] = round(hypotheses[i]["confidence"] + 0.3, 1)
                    hypotheses[i + 1]["confidence"] = round(hypotheses[i + 1]["confidence"] - 0.3, 1)
                else:
                    hypotheses[i]["confidence"] = round(hypotheses[i]["confidence"] - 0.3, 1)
                    hypotheses[i + 1]["confidence"] = round(hypotheses[i + 1]["confidence"] + 0.3, 1)

        hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        return {
            "hypotheses": hypotheses[:5],
            "reasoning_summary": f"KB-based matching found {len(hypotheses)} possible diagnoses with discriminating symptom analysis",
            "dominant_system": dominant_system if dominant_system else (hypotheses[0].get("category", "unknown") if hypotheses else "unknown")
        }


# Singleton
hypothesis_generator = HypothesisGeneratorAgent()