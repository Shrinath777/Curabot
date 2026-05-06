import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime, timedelta
import random
import shutil

output_dir = "synthetic_records"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)

HOSPITAL_NAME = "APOLLO GENERAL DIAGNOSTICS"
HOSPITAL_ADDR = "123 Medical Center Blvd, Health City, 10001"

# ==================== PATIENT DATABASE ====================
# Each patient has: name, age, sex, disease_target (= folder name), test_name,
# treatment_history (surgeries, medications, procedures), and lab results

patients = [
    # ───────────── HEART TRANSPLANT POST-OP (4 patients) ─────────────
    {"name": "William Davis", "age": 55, "sex": "M", "disease_target": "Heart_Transplant",
     "test_name": "CARDIAC TRANSPLANT IMMUNOLOGY PANEL",
     "treatment": "Heart transplant surgery (2024). On Tacrolimus 2mg BD, Mycophenolate 500mg BD, Prednisone 5mg OD. Last endomyocardial biopsy: Grade 1R rejection.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Tacrolimus (Prograf) Trough","3.2","ng/mL","5.0 - 15.0","LOW"),
        ("Cyclosporine Level","85","ng/mL","100 - 400","LOW"),
        ("WBC Count","14.5","10^3/uL","4.5 - 11.0","HIGH"),
        ("High-Sens Troponin T","45","ng/L","< 14","HIGH"),
        ("NT-proBNP","1250","pg/mL","< 125","HIGH")]},
    {"name": "Margaret Holmes", "age": 62, "sex": "F", "disease_target": "Heart_Transplant",
     "test_name": "POST-TRANSPLANT REJECTION SCREENING",
     "treatment": "Orthotopic heart transplant (2023). Current: Everolimus 0.75mg BD, Tacrolimus 1.5mg BD. History of CMV reactivation post-transplant.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Donor-Specific Antibodies (DSA)","Positive - Class II","N/A","Negative","ABNORMAL"),
        ("Tacrolimus Trough","11.2","ng/mL","5.0 - 15.0",""),
        ("CMV PCR","< 200","copies/mL","< 200",""),
        ("BNP","890","pg/mL","< 100","HIGH"),
        ("Creatinine","1.8","mg/dL","0.7 - 1.3","HIGH")]},
    {"name": "Richard Thompson", "age": 48, "sex": "M", "disease_target": "Heart_Transplant",
     "test_name": "CARDIAC BIOPSY FOLLOW-UP PANEL",
     "treatment": "Heart transplant (2025). Endomyocardial biopsy Grade 2R rejection. Started pulsed IV methylprednisolone 1g x3 days, increased Tacrolimus.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Troponin I","2.8","ng/mL","< 0.04","HIGH"),
        ("CRP","45","mg/L","< 5","HIGH"),
        ("WBC Count","18.2","10^3/uL","4.5 - 11.0","HIGH"),
        ("Tacrolimus Trough","4.1","ng/mL","8.0 - 15.0","LOW"),
        ("Echocardiogram LVEF","35","%","55 - 70","LOW")]},
    {"name": "Susan Clark", "age": 59, "sex": "F", "disease_target": "Heart_Transplant",
     "test_name": "ANNUAL TRANSPLANT SURVEILLANCE",
     "treatment": "Heart transplant (2022). Stable on triple immunosuppression. No rejection episodes in 2 years. Coronary angiography: mild CAV.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Tacrolimus Trough","8.5","ng/mL","5.0 - 15.0",""),
        ("eGFR","62","mL/min","> 90","LOW"),
        ("Fasting Glucose","118","mg/dL","70 - 99","HIGH"),
        ("Cholesterol Total","245","mg/dL","< 200","HIGH"),
        ("Hemoglobin A1c","6.2","%","< 5.7","HIGH")]},

    # ───────────── CANCER TREATMENT (5 patients) ─────────────
    {"name": "Evelyn Carter", "age": 42, "sex": "F", "disease_target": "Cancer_Treatment",
     "test_name": "LEUKEMIA CHEMOTHERAPY CBC",
     "treatment": "Acute Lymphoblastic Leukemia. Completed induction chemo (Vincristine+Daunorubicin+Prednisone+Asparaginase). Currently in consolidation phase. Neutropenic precautions active.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("WBC Count","0.8","10^3/uL","4.5 - 11.0","LOW"),
        ("ANC","350","cells/uL","1500 - 8000","LOW"),
        ("Platelet Count","25","10^3/uL","150 - 450","LOW"),
        ("Hemoglobin","7.8","g/dL","12.0 - 15.5","LOW"),
        ("LDH","850","U/L","140 - 280","HIGH")]},
    {"name": "Patricia Moore", "age": 56, "sex": "F", "disease_target": "Cancer_Treatment",
     "test_name": "BREAST CANCER TUMOR MARKER PANEL",
     "treatment": "Invasive ductal carcinoma Stage IIB. Completed 6 cycles AC-T chemo. Bilateral mastectomy performed. Currently on Tamoxifen 20mg daily. Radiation therapy completed.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("CA 15-3","42","U/mL","< 30","HIGH"),
        ("CEA","8.5","ng/mL","< 3.0","HIGH"),
        ("Estrogen Receptor","Positive 95%","N/A","N/A",""),
        ("HER2/neu","Negative","N/A","N/A",""),
        ("WBC Count","3.8","10^3/uL","4.5 - 11.0","LOW")]},
    {"name": "George Wilson", "age": 67, "sex": "M", "disease_target": "Cancer_Treatment",
     "test_name": "LUNG CANCER STAGING PANEL",
     "treatment": "Non-small cell lung cancer Stage IIIA. Lobectomy right upper lobe performed. Currently receiving Cisplatin+Pemetrexed adjuvant chemotherapy cycle 3/4. PET scan shows partial response.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("CYFRA 21-1","12.5","ng/mL","< 3.3","HIGH"),
        ("NSE","28","ng/mL","< 16.3","HIGH"),
        ("Hemoglobin","10.2","g/dL","13.5 - 17.5","LOW"),
        ("Creatinine","1.6","mg/dL","0.7 - 1.3","HIGH"),
        ("Albumin","2.8","g/dL","3.4 - 5.4","LOW")]},
    {"name": "Helen Rodriguez", "age": 38, "sex": "F", "disease_target": "Cancer_Treatment",
     "test_name": "CERVICAL CANCER TREATMENT MONITORING",
     "treatment": "Cervical squamous cell carcinoma Stage IB2. Radical hysterectomy + pelvic lymphadenectomy. Concurrent chemoradiation with Cisplatin weekly x5. HPV 16 positive.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("SCC Antigen","4.2","ng/mL","< 1.5","HIGH"),
        ("CA-125","68","U/mL","< 35","HIGH"),
        ("WBC Count","2.9","10^3/uL","4.5 - 11.0","LOW"),
        ("Platelet Count","98","10^3/uL","150 - 450","LOW"),
        ("Creatinine","1.4","mg/dL","0.6 - 1.1","HIGH")]},
    {"name": "Daniel Brown", "age": 71, "sex": "M", "disease_target": "Cancer_Treatment",
     "test_name": "PROSTATE CANCER PSA MONITORING",
     "treatment": "Prostate adenocarcinoma Gleason 4+3. Radical prostatectomy (2024). Rising PSA - started Enzalutamide 160mg daily + Lupron depot 22.5mg q3mo. Bone scan negative.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("PSA","4.8","ng/mL","< 0.2 post-RP","HIGH"),
        ("Testosterone","18","ng/dL","< 50 on ADT",""),
        ("Alkaline Phosphatase","145","U/L","44 - 147",""),
        ("Hemoglobin","11.5","g/dL","13.5 - 17.5","LOW"),
        ("LDH","310","U/L","140 - 280","HIGH")]},

    # ───────────── CHRONIC KIDNEY FAILURE (3 patients) ─────────────
    {"name": "Michael Ford", "age": 68, "sex": "M", "disease_target": "Chronic_Kidney_Failure",
     "test_name": "END STAGE RENAL PANEL & DIALYSIS PREP",
     "treatment": "CKD Stage 5. Hemodialysis 3x/week via left AV fistula. On Epoetin alfa 10000U 3x/wk, Sevelamer 800mg TID, Calcitriol 0.25mcg daily. Awaiting kidney transplant.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("BUN","95","mg/dL","7 - 20","HIGH"),
        ("Serum Creatinine","6.5","mg/dL","0.7 - 1.3","HIGH"),
        ("eGFR","8","mL/min","> 90","LOW"),
        ("Potassium","6.2","mEq/L","3.5 - 5.0","HIGH"),
        ("Phosphorus","7.5","mg/dL","2.5 - 4.5","HIGH")]},
    {"name": "Dorothy Jenkins", "age": 74, "sex": "F", "disease_target": "Chronic_Kidney_Failure",
     "test_name": "PERITONEAL DIALYSIS MONITORING",
     "treatment": "CKD Stage 5 from diabetic nephropathy. On CAPD (continuous ambulatory peritoneal dialysis) since 2024. Insulin-dependent DM Type 2. History of peritonitis x1.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Creatinine","8.2","mg/dL","0.6 - 1.1","HIGH"),
        ("BUN","88","mg/dL","7 - 20","HIGH"),
        ("Albumin","2.5","g/dL","3.4 - 5.4","LOW"),
        ("Hemoglobin","9.2","g/dL","12.0 - 15.5","LOW"),
        ("PTH Intact","450","pg/mL","15 - 65","HIGH")]},
    {"name": "Thomas Lee", "age": 52, "sex": "M", "disease_target": "Chronic_Kidney_Failure",
     "test_name": "POST-KIDNEY TRANSPLANT PANEL",
     "treatment": "Living donor kidney transplant (2025). On Tacrolimus+Mycophenolate+Prednisone. Previous 4 years on hemodialysis. Excellent graft function at 3 months.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Creatinine","1.2","mg/dL","0.7 - 1.3",""),
        ("eGFR","68","mL/min","> 90","LOW"),
        ("Tacrolimus Trough","7.8","ng/mL","5.0 - 15.0",""),
        ("BK Virus PCR","< 500","copies/mL","< 10000",""),
        ("Urinalysis Protein","Trace","N/A","Negative","ABNORMAL")]},

    # ───────────── POST-SURGERY SEPSIS (3 patients) ─────────────
    {"name": "Sophia Reynolds", "age": 31, "sex": "F", "disease_target": "Post_Surgery_Sepsis",
     "test_name": "ICU SEPSIS SHOCK PROTOCOL",
     "treatment": "Post-appendectomy wound infection progressed to septic shock. On IV Meropenem 1g q8h + Vancomycin. Vasopressor support with Norepinephrine. Central line placed.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Serum Lactate","8.5","mmol/L","0.5 - 2.2","HIGH"),
        ("Procalcitonin","14.2","ng/mL","< 0.1","HIGH"),
        ("CRP","310","mg/L","< 5","HIGH"),
        ("WBC Count","28.5","10^3/uL","4.5 - 11.0","HIGH"),
        ("Blood Culture","Positive - Staph aureus","N/A","No Growth","ABNORMAL")]},
    {"name": "James Parker", "age": 65, "sex": "M", "disease_target": "Post_Surgery_Sepsis",
     "test_name": "POST-CABG INFECTION PANEL",
     "treatment": "Coronary artery bypass graft x3 (10 days ago). Sternal wound dehiscence with MRSA. On IV Daptomycin + wound VAC therapy. ICU day 5.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("WBC Count","22.1","10^3/uL","4.5 - 11.0","HIGH"),
        ("Procalcitonin","8.6","ng/mL","< 0.1","HIGH"),
        ("Lactate","4.2","mmol/L","0.5 - 2.2","HIGH"),
        ("Wound Culture","MRSA Positive","N/A","No Growth","ABNORMAL"),
        ("INR","1.8","Ratio","0.8 - 1.1","HIGH")]},
    {"name": "Emily Watson", "age": 44, "sex": "F", "disease_target": "Post_Surgery_Sepsis",
     "test_name": "POST-HYSTERECTOMY SEPSIS SCREEN",
     "treatment": "Total abdominal hysterectomy for fibroids. Developed post-op pelvic abscess day 4. CT-guided drainage performed. On IV Piperacillin-Tazobactam.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("WBC Count","19.8","10^3/uL","4.5 - 11.0","HIGH"),
        ("CRP","185","mg/L","< 5","HIGH"),
        ("Procalcitonin","3.5","ng/mL","< 0.1","HIGH"),
        ("Hemoglobin","8.9","g/dL","12.0 - 15.5","LOW"),
        ("Abscess Culture","E. coli + Bacteroides","N/A","No Growth","ABNORMAL")]},

    # ───────────── SEVERE COPD (3 patients) ─────────────
    {"name": "Arthur Briggs", "age": 72, "sex": "M", "disease_target": "Severe_COPD",
     "test_name": "ABG - ACUTE EXACERBATION",
     "treatment": "COPD GOLD Stage IV. Acute exacerbation requiring BiPAP. On Tiotropium+Fluticasone/Salmeterol inhalers, IV methylprednisolone, nebulized salbutamol q4h. Home O2 2L/min.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("pH","7.28","N/A","7.35 - 7.45","LOW"),
        ("pCO2","68","mmHg","35 - 45","HIGH"),
        ("pO2","55","mmHg","75 - 100","LOW"),
        ("Bicarbonate","32","mEq/L","22 - 28","HIGH"),
        ("O2 Saturation","86","%","95 - 100","LOW")]},
    {"name": "Barbara Phillips", "age": 66, "sex": "F", "disease_target": "Severe_COPD",
     "test_name": "PULMONARY FUNCTION + INFECTION SCREEN",
     "treatment": "COPD with recurrent infective exacerbations. Currently on Azithromycin prophylaxis. Completed pulmonary rehabilitation. FEV1 28% predicted. Evaluated for lung transplant.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("FEV1","0.72","L","2.5 - 3.5","LOW"),
        ("FEV1/FVC Ratio","38","%","> 70","LOW"),
        ("Sputum Culture","Pseudomonas aeruginosa","N/A","Normal Flora","ABNORMAL"),
        ("WBC Count","13.2","10^3/uL","4.5 - 11.0","HIGH"),
        ("Pro-BNP","580","pg/mL","< 125","HIGH")]},
    {"name": "Harold Stevens", "age": 78, "sex": "M", "disease_target": "Severe_COPD",
     "test_name": "COPD WITH COR PULMONALE PANEL",
     "treatment": "End-stage COPD with right heart failure (cor pulmonale). On long-term O2 therapy, Furosemide 40mg, Spironolactone. Previous ICU intubation x2. DNR/DNI status.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("BNP","1850","pg/mL","< 100","HIGH"),
        ("pCO2","72","mmHg","35 - 45","HIGH"),
        ("Hemoglobin","18.5","g/dL","13.5 - 17.5","HIGH"),
        ("Creatinine","1.9","mg/dL","0.7 - 1.3","HIGH"),
        ("Echocardiogram RVSP","65","mmHg","< 30","HIGH")]},

    # ───────────── LIVER CIRRHOSIS (3 patients) ─────────────
    {"name": "Marcus Kane", "age": 59, "sex": "M", "disease_target": "Liver_Cirrhosis",
     "test_name": "END STAGE HEPATIC FAILURE PANEL",
     "treatment": "Cirrhosis from Hepatitis C (treated with Sofosbuvir/Velpatasvir - SVR achieved). Child-Pugh C. MELD score 28. On Lactulose, Rifaximin, Propranolol. Listed for liver transplant.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Total Bilirubin","14.5","mg/dL","0.1 - 1.2","HIGH"),
        ("Serum Albumin","2.1","g/dL","3.4 - 5.4","LOW"),
        ("INR","2.8","Ratio","0.8 - 1.1","HIGH"),
        ("Ammonia","145","umol/L","15 - 45","HIGH"),
        ("Platelet Count","45","10^3/uL","150 - 450","LOW")]},
    {"name": "Nancy Edwards", "age": 51, "sex": "F", "disease_target": "Liver_Cirrhosis",
     "test_name": "ALCOHOLIC LIVER DISEASE PANEL",
     "treatment": "Alcoholic cirrhosis with recent variceal bleed. Emergency band ligation performed. On Octreotide infusion, Nadolol 40mg. Required 4 units PRBC transfusion.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("AST","285","U/L","10 - 40","HIGH"),
        ("ALT","142","U/L","7 - 56","HIGH"),
        ("GGT","520","U/L","9 - 48","HIGH"),
        ("Hemoglobin","6.8","g/dL","12.0 - 15.5","LOW"),
        ("INR","2.2","Ratio","0.8 - 1.1","HIGH")]},
    {"name": "Frank Martinez", "age": 63, "sex": "M", "disease_target": "Liver_Cirrhosis",
     "test_name": "HEPATOCELLULAR CARCINOMA SCREENING",
     "treatment": "Cirrhosis NASH-related. HCC screening positive - 3cm lesion in segment VI. Undergoing TACE (transarterial chemoembolization). On Sorafenib 400mg BD.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("AFP","485","ng/mL","< 10","HIGH"),
        ("Total Bilirubin","3.8","mg/dL","0.1 - 1.2","HIGH"),
        ("Albumin","2.9","g/dL","3.4 - 5.4","LOW"),
        ("Platelet Count","68","10^3/uL","150 - 450","LOW"),
        ("AFP-L3","18","%","< 10","HIGH")]},

    # ───────────── DIABETES (4 patients) ─────────────
    {"name": "James Smith", "age": 19, "sex": "M", "disease_target": "Diabetes",
     "test_name": "DIABETIC KETOACIDOSIS PANEL",
     "treatment": "Type 1 DM - DKA admission. IV insulin infusion protocol initiated. K+ replacement ongoing. Newly diagnosed - started on Lantus 20U + Humalog sliding scale.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Glucose","485","mg/dL","70 - 99","HIGH"),
        ("Potassium","5.2","mEq/L","3.5 - 5.0","HIGH"),
        ("Bicarbonate","12","mEq/L","23 - 29","LOW"),
        ("Blood Ketones","4.5","mmol/L","< 0.6","HIGH"),
        ("Anion Gap","22","mEq/L","8 - 12","HIGH")]},
    {"name": "Linda Chang", "age": 58, "sex": "F", "disease_target": "Diabetes",
     "test_name": "DIABETIC COMPLICATIONS SCREENING",
     "treatment": "Type 2 DM x15 years. On Metformin 1g BD + Empagliflozin 25mg + Insulin Glargine 40U. Diabetic retinopathy (laser treatment done). Peripheral neuropathy on Pregabalin.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("HbA1c","9.2","%","< 7.0","HIGH"),
        ("Fasting Glucose","210","mg/dL","70 - 99","HIGH"),
        ("Urine Albumin/Creatinine","185","mg/g","< 30","HIGH"),
        ("eGFR","52","mL/min","> 90","LOW"),
        ("Total Cholesterol","268","mg/dL","< 200","HIGH")]},
    {"name": "Robert Singh", "age": 45, "sex": "M", "disease_target": "Diabetes",
     "test_name": "DIABETIC FOOT ULCER WORKUP",
     "treatment": "Type 2 DM with infected Wagner Grade 3 foot ulcer. On IV Ertapenem. Vascular surgery consult - ABI 0.6 left. Scheduled for angioplasty. Wound care with negative pressure.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("HbA1c","11.5","%","< 7.0","HIGH"),
        ("WBC Count","16.8","10^3/uL","4.5 - 11.0","HIGH"),
        ("ESR","85","mm/hr","0 - 20","HIGH"),
        ("CRP","95","mg/L","< 5","HIGH"),
        ("Wound Culture","MRSA + Pseudomonas","N/A","No Growth","ABNORMAL")]},
    {"name": "Catherine Wu", "age": 32, "sex": "F", "disease_target": "Diabetes",
     "test_name": "GESTATIONAL DIABETES PANEL",
     "treatment": "Gestational diabetes at 28 weeks. Failed OGTT. Started on insulin Aspart before meals + Insulin NPH at bedtime. Close fetal monitoring with biophysical profile.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("OGTT 1-hr","198","mg/dL","< 180","HIGH"),
        ("OGTT 2-hr","165","mg/dL","< 153","HIGH"),
        ("Fasting Glucose","105","mg/dL","< 92","HIGH"),
        ("HbA1c","6.8","%","< 6.0 in pregnancy","HIGH"),
        ("Fructosamine","285","umol/L","205 - 285","")]},

    # ───────────── CARDIAC EMERGENCY (4 patients) ─────────────
    {"name": "Robert Chen", "age": 61, "sex": "M", "disease_target": "Cardiac_Emergency",
     "test_name": "ACUTE MI - STEMI PROTOCOL",
     "treatment": "STEMI anterior wall. Emergency PCI with DES to LAD. On Aspirin+Ticagrelor+Heparin drip. Started Atorvastatin 80mg, Metoprolol, ACE inhibitor. LVEF 40%.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Troponin I","1250","ng/L","< 14","HIGH"),
        ("CK-MB","45","ng/mL","< 5","HIGH"),
        ("Myoglobin","350","ng/mL","< 85","HIGH"),
        ("BNP","680","pg/mL","< 100","HIGH"),
        ("D-Dimer","1.2","mg/L","< 0.5","HIGH")]},
    {"name": "Stanley Hudson", "age": 58, "sex": "M", "disease_target": "Cardiac_Emergency",
     "test_name": "HEART FAILURE - DECOMPENSATION",
     "treatment": "CHF NYHA Class IV decompensation. On IV Furosemide drip + Dobutamine. BiV ICD implanted 2024. Fluid restricted 1.5L/day. Cardiology evaluating for LVAD.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("BNP","4200","pg/mL","< 100","HIGH"),
        ("Troponin I","0.08","ng/mL","< 0.04","HIGH"),
        ("Na+","128","mEq/L","136 - 145","LOW"),
        ("Creatinine","2.4","mg/dL","0.7 - 1.3","HIGH"),
        ("Echocardiogram LVEF","15","%","55 - 70","LOW")]},
    {"name": "Angela Brooks", "age": 45, "sex": "F", "disease_target": "Cardiac_Emergency",
     "test_name": "PULMONARY EMBOLISM PANEL",
     "treatment": "Massive PE with hemodynamic instability. Catheter-directed thrombolysis with Alteplase performed. Started therapeutic Heparin, transitioning to Rivaroxaban. IVC filter placed.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("D-Dimer","8.5","mg/L","< 0.5","HIGH"),
        ("Troponin I","0.45","ng/mL","< 0.04","HIGH"),
        ("BNP","920","pg/mL","< 100","HIGH"),
        ("CT-PA","Bilateral PE confirmed","N/A","No PE","ABNORMAL"),
        ("O2 Saturation","82","%","95 - 100","LOW")]},
    {"name": "Kenneth Wright", "age": 70, "sex": "M", "disease_target": "Cardiac_Emergency",
     "test_name": "AORTIC DISSECTION EMERGENCY",
     "treatment": "Stanford Type A aortic dissection. Emergency ascending aortic replacement with Dacron graft. On Esmolol drip for HR/BP control. ICU post-op day 2.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("D-Dimer","12.8","mg/L","< 0.5","HIGH"),
        ("Lactate","5.5","mmol/L","0.5 - 2.2","HIGH"),
        ("Hemoglobin","8.2","g/dL","13.5 - 17.5","LOW"),
        ("Creatinine","2.1","mg/dL","0.7 - 1.3","HIGH"),
        ("Troponin I","0.95","ng/mL","< 0.04","HIGH")]},

    # ───────────── NEUROLOGICAL (3 patients) ─────────────
    {"name": "Liam Nelson", "age": 8, "sex": "M", "disease_target": "Neurological",
     "test_name": "BACTERIAL MENINGITIS CSF",
     "treatment": "Acute bacterial meningitis. IV Ceftriaxone 100mg/kg/day + Vancomycin + Dexamethasone. LP confirmed Streptococcus pneumoniae. Seizure prophylaxis with Levetiracetam.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("CSF Appearance","Cloudy","N/A","Clear","ABNORMAL"),
        ("CSF WBC","1250","cells/uL","0 - 5","HIGH"),
        ("CSF Protein","180","mg/dL","15 - 45","HIGH"),
        ("CSF Glucose","25","mg/dL","40 - 70","LOW"),
        ("CSF Culture","S. pneumoniae","N/A","No Growth","ABNORMAL")]},
    {"name": "Victoria Adams", "age": 68, "sex": "F", "disease_target": "Neurological",
     "test_name": "ACUTE ISCHEMIC STROKE PANEL",
     "treatment": "Left MCA territory ischemic stroke. IV Alteplase (tPA) given within 3hr window. Mechanical thrombectomy performed. On Aspirin+Clopidogrel, Atorvastatin 80mg. NIHSS improved 14→6.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("CT Head","Hypodense L MCA territory","N/A","Normal","ABNORMAL"),
        ("INR","1.0","Ratio","0.8 - 1.1",""),
        ("Glucose","165","mg/dL","70 - 99","HIGH"),
        ("LDL Cholesterol","168","mg/dL","< 100","HIGH"),
        ("HbA1c","7.8","%","< 5.7","HIGH")]},
    {"name": "Oscar Martinez", "age": 35, "sex": "M", "disease_target": "Neurological",
     "test_name": "EPILEPSY MONITORING PANEL",
     "treatment": "Drug-resistant temporal lobe epilepsy. Failed Levetiracetam+Carbamazepine+Lacosamide. Evaluated for epilepsy surgery - SEEG monitoring completed. Scheduled for anterior temporal lobectomy.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Levetiracetam Level","8","ug/mL","12 - 46","LOW"),
        ("Carbamazepine Level","5.2","ug/mL","4 - 12",""),
        ("Sodium","132","mEq/L","136 - 145","LOW"),
        ("Liver Function ALT","62","U/L","7 - 56","HIGH"),
        ("EEG","L temporal spikes","N/A","Normal","ABNORMAL")]},

    # ───────────── THYROID DISORDERS (3 patients) ─────────────
    {"name": "Arun Kumar", "age": 45, "sex": "M", "disease_target": "Thyroid_Disorders",
     "test_name": "GRAVES DISEASE HYPERTHYROID PANEL",
     "treatment": "Graves' disease with thyroid storm history. On Methimazole 30mg daily (dose being tapered). Beta-blocker Propranolol 40mg TID. Considering radioactive iodine ablation.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("TSH","0.01","mIU/L","0.40 - 4.50","LOW"),
        ("Free T4","2.9","ng/dL","0.8 - 1.8","HIGH"),
        ("Free T3","5.1","pg/mL","2.3 - 4.2","HIGH"),
        ("TSI (Thyroid Stimulating Immunoglobulin)","485","%","< 140","HIGH"),
        ("WBC Count","3.5","10^3/uL","4.5 - 11.0","LOW")]},
    {"name": "Maria Garcia", "age": 52, "sex": "F", "disease_target": "Thyroid_Disorders",
     "test_name": "HASHIMOTO'S HYPOTHYROID PANEL",
     "treatment": "Hashimoto's thyroiditis with severe hypothyroidism. On Levothyroxine 150mcg daily (recently increased). Thyroid ultrasound shows diffuse heterogeneous gland. Annual monitoring.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("TSH","8.70","mIU/L","0.40 - 4.50","HIGH"),
        ("Free T4","0.6","ng/dL","0.8 - 1.8","LOW"),
        ("Anti-TPO","120","IU/mL","< 34","HIGH"),
        ("Anti-Thyroglobulin","85","IU/mL","< 40","HIGH"),
        ("Total Cholesterol","285","mg/dL","< 200","HIGH")]},
    {"name": "Priya Sharma", "age": 34, "sex": "F", "disease_target": "Thyroid_Disorders",
     "test_name": "THYROID CANCER POST-OP PANEL",
     "treatment": "Papillary thyroid carcinoma. Total thyroidectomy + central neck dissection performed. Radioactive iodine (RAI) 150mCi administered. On suppressive dose Levothyroxine 200mcg.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Thyroglobulin","0.3","ng/mL","< 0.2 post-thyroidectomy","HIGH"),
        ("Anti-Thyroglobulin Ab","< 1","IU/mL","< 4",""),
        ("TSH","0.08","mIU/L","0.40 - 4.50","LOW"),
        ("Free T4","2.1","ng/dL","0.8 - 1.8","HIGH"),
        ("Calcium","8.2","mg/dL","8.5 - 10.5","LOW")]},

    # ───────────── INFECTIOUS DISEASE (4 patients) ─────────────
    {"name": "Sarah Jenkins", "age": 28, "sex": "F", "disease_target": "Infectious_Disease",
     "test_name": "DENGUE FEVER CBC",
     "treatment": "Dengue hemorrhagic fever. IV fluid resuscitation with NS. Platelet transfusion given (count was 18K). Close monitoring for plasma leakage. Acetaminophen for fever.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Hemoglobin","14.2","g/dL","12.0 - 15.5",""),
        ("Hematocrit","48.5","%","36.0 - 46.0","HIGH"),
        ("WBC Count","3.2","10^3/uL","4.5 - 11.0","LOW"),
        ("Platelet Count","65","10^3/uL","150 - 450","LOW"),
        ("Dengue NS1 Antigen","Positive","N/A","Negative","ABNORMAL")]},
    {"name": "Rajesh Koothrappali", "age": 35, "sex": "M", "disease_target": "Infectious_Disease",
     "test_name": "MALARIA PANEL + COMPLICATIONS",
     "treatment": "Severe P. falciparum malaria with cerebral involvement. IV Artesunate initiated. Exchange transfusion considered (parasitemia 12%). ICU monitoring for ARDS and renal failure.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Malaria Smear","P. falciparum - 12% parasitemia","N/A","Negative","ABNORMAL"),
        ("Hemoglobin","7.5","g/dL","13.5 - 17.5","LOW"),
        ("Platelet Count","32","10^3/uL","150 - 450","LOW"),
        ("Total Bilirubin","6.8","mg/dL","0.1 - 1.2","HIGH"),
        ("Creatinine","3.2","mg/dL","0.7 - 1.3","HIGH")]},
    {"name": "Nina Simone", "age": 40, "sex": "F", "disease_target": "Infectious_Disease",
     "test_name": "TUBERCULOSIS WORKUP",
     "treatment": "Pulmonary TB confirmed by GeneXpert MTB/RIF. Started RIPE therapy (Rifampin+Isoniazid+Pyrazinamide+Ethambutol). Pyridoxine 25mg added. Contact tracing initiated. Sputum AFB monitoring.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("GeneXpert MTB","MTB Detected - Rif Sensitive","N/A","Not Detected","ABNORMAL"),
        ("Sputum AFB Smear","3+ Acid Fast Bacilli","N/A","No AFB","ABNORMAL"),
        ("ESR","65","mm/hr","0 - 20","HIGH"),
        ("CRP","42","mg/L","< 5","HIGH"),
        ("Albumin","2.8","g/dL","3.4 - 5.4","LOW")]},
    {"name": "David Kim", "age": 33, "sex": "M", "disease_target": "Infectious_Disease",
     "test_name": "HIV SCREENING AND STAGING",
     "treatment": "Newly diagnosed HIV-1. CD4 count critically low. Started ART: Bictegravir/Emtricitabine/TAF (Biktarvy). Prophylaxis: TMP-SMX for PCP + Azithromycin for MAC. Viral load monitoring at 4 weeks.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("HIV-1 Ab/Ag (4th Gen)","Reactive","N/A","Non-Reactive","ABNORMAL"),
        ("HIV-1 RNA Viral Load","185000","copies/mL","< 20","HIGH"),
        ("CD4 Count","85","cells/uL","500 - 1500","LOW"),
        ("CD4/CD8 Ratio","0.12","Ratio","1.0 - 3.0","LOW"),
        ("Hemoglobin","10.5","g/dL","13.5 - 17.5","LOW")]},

    # ───────────── AUTOIMMUNE (3 patients) ─────────────
    {"name": "Rachel Green", "age": 29, "sex": "F", "disease_target": "Autoimmune",
     "test_name": "SYSTEMIC LUPUS PANEL",
     "treatment": "SLE with lupus nephritis Class IV. On Hydroxychloroquine 200mg BD + Mycophenolate 1g BD + Prednisone 20mg (tapering). Recent flare with proteinuria. Considering Belimumab.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("ANA","1:640 Homogeneous","N/A","< 1:40","ABNORMAL"),
        ("Anti-dsDNA","185","IU/mL","< 30","HIGH"),
        ("Complement C3","42","mg/dL","90 - 180","LOW"),
        ("Complement C4","6","mg/dL","10 - 40","LOW"),
        ("Urine Protein/Creatinine","3.2","g/g","< 0.2","HIGH")]},
    {"name": "Michael Scott", "age": 48, "sex": "M", "disease_target": "Autoimmune",
     "test_name": "RHEUMATOID ARTHRITIS PANEL",
     "treatment": "Seropositive RA with erosive disease. Failed MTX+HCQ. Currently on Adalimumab 40mg q2wk + low-dose Prednisone. TB screening negative. Joint replacement right knee (2024).",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("RF (Rheumatoid Factor)","245","IU/mL","< 14","HIGH"),
        ("Anti-CCP","> 300","U/mL","< 20","HIGH"),
        ("ESR","58","mm/hr","0 - 20","HIGH"),
        ("CRP","32","mg/L","< 5","HIGH"),
        ("Hemoglobin","11.2","g/dL","13.5 - 17.5","LOW")]},
    {"name": "Sandra Lee", "age": 36, "sex": "F", "disease_target": "Autoimmune",
     "test_name": "CROHN'S DISEASE ACTIVITY PANEL",
     "treatment": "Crohn's disease with ileal stricture. History: right hemicolectomy (2023). Currently on Infliximab 5mg/kg q8wk. Recent flare - adding Azathioprine. Iron infusions for anemia.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Fecal Calprotectin","850","ug/g","< 50","HIGH"),
        ("CRP","28","mg/L","< 5","HIGH"),
        ("Albumin","2.6","g/dL","3.4 - 5.4","LOW"),
        ("Hemoglobin","9.5","g/dL","12.0 - 15.5","LOW"),
        ("Vitamin B12","125","pg/mL","200 - 900","LOW")]},

    # ───────────── RESPIRATORY (3 patients) ─────────────
    {"name": "Tom Hanks", "age": 50, "sex": "M", "disease_target": "Respiratory",
     "test_name": "SEVERE PNEUMONIA PANEL",
     "treatment": "Community-acquired pneumonia CURB-65 score 3. On IV Ceftriaxone + Azithromycin. Supplemental O2 via high-flow nasal cannula 40L/min. Chest tube placed for parapneumonic effusion.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("WBC Count","18.5","10^3/uL","4.5 - 11.0","HIGH"),
        ("Procalcitonin","5.2","ng/mL","< 0.1","HIGH"),
        ("CRP","220","mg/L","< 5","HIGH"),
        ("Sputum Culture","Strep pneumoniae","N/A","Normal Flora","ABNORMAL"),
        ("Pleural Fluid LDH","680","U/L","< 200","HIGH")]},
    {"name": "Chloe Decker", "age": 25, "sex": "F", "disease_target": "Respiratory",
     "test_name": "SEVERE ASTHMA EXACERBATION",
     "treatment": "Status asthmaticus requiring ICU. Continuous nebulized albuterol + IV magnesium sulfate + IV methylprednisolone. Intubation avoided with BiPAP. Stepped up to Dupilumab biologic.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Peak Flow","120","L/min","380 - 500","LOW"),
        ("pCO2","52","mmHg","35 - 45","HIGH"),
        ("pH","7.32","N/A","7.35 - 7.45","LOW"),
        ("Eosinophils","12","%","1 - 4","HIGH"),
        ("IgE Total","850","IU/mL","< 100","HIGH")]},
    {"name": "Walter White", "age": 52, "sex": "M", "disease_target": "Respiratory",
     "test_name": "COVID-19 SEVERE ILLNESS PANEL",
     "treatment": "COVID-19 ARDS. Proning protocol. High-flow O2 60L/min. Dexamethasone 6mg x10 days + Remdesivir 5-day course + Tocilizumab single dose. Prophylactic anticoagulation with Enoxaparin.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("SARS-CoV-2 PCR","Positive - Ct 15","N/A","Not Detected","ABNORMAL"),
        ("CRP","285","mg/L","< 5","HIGH"),
        ("Ferritin","2850","ng/mL","20 - 250","HIGH"),
        ("D-Dimer","4.5","mg/L","< 0.5","HIGH"),
        ("IL-6","185","pg/mL","< 7","HIGH")]},

    # ───────────── BLOOD DISORDERS (3 patients) ─────────────
    {"name": "Emma Woods", "age": 22, "sex": "F", "disease_target": "Blood_Disorders",
     "test_name": "SEVERE IRON DEFICIENCY ANEMIA",
     "treatment": "Severe iron deficiency anemia from menorrhagia. IV Iron Sucrose 200mg x5 infusions. Referred to OB-GYN - Mirena IUD placed. Oral Ferrous sulfate 325mg BD with vitamin C.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Hemoglobin","6.2","g/dL","12.0 - 15.5","LOW"),
        ("MCV","62","fL","80 - 100","LOW"),
        ("Ferritin","4","ng/mL","12 - 150","LOW"),
        ("Iron","15","ug/dL","60 - 170","LOW"),
        ("TIBC","450","ug/dL","250 - 370","HIGH")]},
    {"name": "Oliver Twist", "age": 18, "sex": "M", "disease_target": "Blood_Disorders",
     "test_name": "SICKLE CELL VASO-OCCLUSIVE CRISIS",
     "treatment": "Sickle cell disease (HbSS) with acute vaso-occlusive crisis. IV fluids + PCA morphine pump. On Hydroxyurea 1g daily. History: cholecystectomy, avascular necrosis right hip. Considering gene therapy trial.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Hemoglobin","6.8","g/dL","13.5 - 17.5","LOW"),
        ("Reticulocyte Count","12.5","%","0.5 - 2.5","HIGH"),
        ("LDH","580","U/L","140 - 280","HIGH"),
        ("Total Bilirubin","4.8","mg/dL","0.1 - 1.2","HIGH"),
        ("Hb Electrophoresis","HbS 82%, HbF 12%","N/A","HbA > 95%","ABNORMAL")]},
    {"name": "Martha Stewart", "age": 65, "sex": "F", "disease_target": "Blood_Disorders",
     "test_name": "DIC COAGULATION PANEL",
     "treatment": "Disseminated intravascular coagulation secondary to sepsis. Cryoprecipitate + FFP + platelet transfusions. Treating underlying E.coli urosepsis source. Hematology consult for possible TTP.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Platelet Count","28","10^3/uL","150 - 450","LOW"),
        ("PT","22","seconds","11 - 13.5","HIGH"),
        ("INR","2.5","Ratio","0.8 - 1.1","HIGH"),
        ("Fibrinogen","85","mg/dL","200 - 400","LOW"),
        ("D-Dimer","18.5","mg/L","< 0.5","HIGH")]},

    # ───────────── HEALTHY BASELINE (3 patients) ─────────────
    {"name": "Jane Doe", "age": 29, "sex": "F", "disease_target": "Healthy_Baseline",
     "test_name": "ANNUAL WELLNESS PANEL",
     "treatment": "Routine annual wellness visit. No active complaints. Exercises 4x/week. Non-smoker, social drinker. Family history: HTN (mother). Counseled on diet and screening.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("WBC Count","6.2","10^3/uL","4.5 - 11.0",""),
        ("Hemoglobin","13.8","g/dL","12.0 - 15.5",""),
        ("Platelet Count","250","10^3/uL","150 - 450",""),
        ("Glucose","85","mg/dL","70 - 99",""),
        ("Total Cholesterol","178","mg/dL","< 200","")]},
    {"name": "Chris Evans", "age": 38, "sex": "M", "disease_target": "Healthy_Baseline",
     "test_name": "EXECUTIVE HEALTH SCREENING",
     "treatment": "Annual executive health checkup. All parameters within normal limits. Vaccinations up to date. BMI 24.2. Advised to continue current lifestyle.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Hemoglobin","15.2","g/dL","13.5 - 17.5",""),
        ("Fasting Glucose","88","mg/dL","70 - 99",""),
        ("Creatinine","0.9","mg/dL","0.7 - 1.3",""),
        ("TSH","2.1","mIU/L","0.40 - 4.50",""),
        ("LDL Cholesterol","95","mg/dL","< 100","")]},
    {"name": "Amira Patel", "age": 24, "sex": "F", "disease_target": "Healthy_Baseline",
     "test_name": "PRE-EMPLOYMENT MEDICAL CLEARANCE",
     "treatment": "Pre-employment medical fitness certificate. No significant history. Non-smoker, no medications. Vision 20/20 bilateral. Hearing normal. Cleared for employment.",
     "results": [("Parameters","Result","Units","Ref. Range","Flag"),
        ("Hemoglobin","13.2","g/dL","12.0 - 15.5",""),
        ("WBC Count","5.8","10^3/uL","4.5 - 11.0",""),
        ("Glucose","82","mg/dL","70 - 99",""),
        ("Urinalysis","Normal","N/A","Normal",""),
        ("Chest X-Ray","Normal","N/A","Normal","")]},
]


def generate_pdf(patient):
    disease_folder = os.path.join(output_dir, patient['disease_target'])
    os.makedirs(disease_folder, exist_ok=True)

    filename = f"{patient['name'].replace(' ', '_')}_{patient['test_name'].split()[0]}.pdf"
    filepath = os.path.join(disease_folder, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('HospitalTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=18, spaceAfter=5, textColor=colors.darkblue)
    addr_style = ParagraphStyle('Address', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10, spaceAfter=20, textColor=colors.slategray)
    report_title = ParagraphStyle('ReportTitle', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=14, spaceAfter=15, alignment=1)
    treatment_style = ParagraphStyle('Treatment', parent=styles['Normal'], fontName='Helvetica',
        fontSize=9, spaceAfter=15, textColor=colors.darkslategray, leftIndent=10, rightIndent=10,
        borderColor=colors.lightgrey, borderWidth=1, borderPadding=8, backColor=colors.Color(0.97, 0.97, 1.0))

    # Header
    story.append(Paragraph(HOSPITAL_NAME, title_style))
    story.append(Paragraph(HOSPITAL_ADDR, addr_style))
    story.append(Paragraph(f"LABORATORY REPORT: {patient['test_name']}", report_title))

    # Patient Info
    date_collected = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%d-%b-%Y %H:%M")
    patient_info = [
        ["Patient Name:", patient['name'], "Patient ID:", f"MRN-{random.randint(100000, 999999)}"],
        ["Age/Sex:", f"{patient['age']}Y / {patient['sex']}", "Collection Date:", date_collected],
        ["Specimen:", "Blood/Serum/Other", "Report Date:", datetime.now().strftime("%d-%b-%Y %H:%M")]
    ]
    info_table = Table(patient_info, colWidths=[100, 160, 100, 160])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.darkslategray),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # Treatment / Clinical History section
    if patient.get('treatment'):
        story.append(Paragraph("<b>CLINICAL HISTORY &amp; TREATMENT:</b>", ParagraphStyle(
            'TreatLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.darkblue, spaceAfter=5)))
        story.append(Paragraph(patient['treatment'], treatment_style))
        story.append(Spacer(1, 10))

    # Results Table
    results_data = patient['results']
    results_table = Table(results_data, colWidths=[180, 70, 70, 120, 80])
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
    ]
    for i in range(1, len(results_data)):
        flag = results_data[i][4]
        if flag in ["HIGH", "ABNORMAL"]:
            t_style.append(('TEXTCOLOR', (4,i), (4,i), colors.red))
            t_style.append(('FONTNAME', (1,i), (1,i), 'Helvetica-Bold'))
        elif flag == "LOW":
            t_style.append(('TEXTCOLOR', (4,i), (4,i), colors.blue))
            t_style.append(('FONTNAME', (1,i), (1,i), 'Helvetica-Bold'))
    results_table.setStyle(TableStyle(t_style))
    story.append(results_table)

    # Footer
    story.append(Spacer(1, 40))
    disclaimer = """<font size=8 color=gray>
    * This report was generated synthetically for MEDICAL EDUCATION ONLY. Not for clinical use.<br/>
    * Reference ranges may vary depending on the testing methodology employed by the laboratory.<br/>
    * A clinical correlation is required for an accurate interpretation of these results.
    </font>"""
    story.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', parent=styles['Normal'], alignment=0)))

    doc.build(story)
    return disease_folder, filename


if __name__ == "__main__":
    print(f"=" * 70)
    print(f"  GENERATING {len(patients)} CATEGORIZED SYNTHETIC MEDICAL RECORDS")
    print(f"=" * 70)

    categories = {}
    for p in patients:
        cat = p['disease_target']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p['name'])

    print(f"\n  Categories: {len(categories)}")
    for cat, names in categories.items():
        print(f"    [DIR] {cat}/ ({len(names)} reports)")

    print(f"\n  Generating PDFs...\n")
    for p in patients:
        folder, fname = generate_pdf(p)
        print(f"  [OK] {folder}/{fname}")

    print(f"\n{'=' * 70}")
    print(f"  COMPLETE! {len(patients)} reports in {len(categories)} disease folders")
    print(f"  Output: {os.path.abspath(output_dir)}/")
    print(f"{'=' * 70}")
