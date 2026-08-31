# GPT-5.5 Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT-5.5 评估指南

本指南用于让 GPT-5.5 对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT-5.5 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

## 评估角色

请作为独立评估者，逐条评价候选布尔表达式。每条样本只允许使用以下信息：

- 原始纳排标准文本。
- 一个候选布尔表达式。
- 本指南中的评分细则。

请不要推测候选表达式由哪种方法生成，不要使用任何隐藏参考答案，不要根据表达式长短直接加分或扣分。评价重点是候选表达式是否保留原文临床含义。

## 输入字段

每条候选通常包含：

- `candidate_id`：盲化候选编号。
- `doc_id`：原始纳排标准编译单元编号。
- `case_bucket`：样本类型，可能为 `or`、`scope` 或 `other`。
- `source_criterion`：原始纳排标准文本。
- `candidate_expression`：候选布尔表达式。

`candidate_id` 是唯一需要在输出中保留的样本键。不要输出方法名。

## 评分流程

对每条候选按以下顺序评估：

1. 阅读 `source_criterion`，识别关键临床条件、数值、时间、限定词、否定、并列关系和局部分组。
2. 阅读 `candidate_expression`，判断它是否表达了相同临床含义。
3. 分别给五个维度打 0、1、2 分。
4. 选择适用的 `error_flags`。
5. 写一句非常简短的 `brief_rationale`，说明主要扣分原因或为什么基本正确。

不同候选之间不要相互比较；每条候选都只与自己的原始文本比较。

## 评分维度

每个维度均为 0、1、2 分。

### 1. predicate_completeness

评价关键临床谓词是否完整。

- 2：疾病、药物、检查、数值、时间、限定词、否定等关键信息基本完整，并整合为清晰谓词。
- 1：主要谓词存在，但部分数值、时间、限定词、修饰语或谓词归属缺失或碎片化。
- 0：关键谓词大量缺失、严重碎片化、空输出或不可理解。

### 2. logical_correctness

评价 AND、OR、NOT 是否保留原文逻辑。

- 2：合取、析取和否定关系基本正确。
- 1：主体逻辑部分正确，但至少一个重要 AND、OR 或 NOT 关系错误或模糊。
- 0：布尔逻辑显著改变原文含义。

### 3. grouping_correctness

评价并列项、共享修饰语、局部分组和层级结构。

- 2：替代项、共享修饰语、局部条件组和嵌套结构清晰。
- 1：部分分组正确，但替代项归属或共享修饰语作用范围有错误。
- 0：分组缺失或严重误导。

### 4. faithfulness

评价候选表达式是否忠实于原文。

- 2：没有临床重要的新增条件或遗漏。
- 1：总体忠实，但存在需要人工修正的重要细节。
- 0：新增原文不支持的条件、遗漏核心条件或与原文矛盾。

### 5. downstream_usability

评价是否可作为队列查询或患者筛选的中间表示。

- 2：基本可用于后续查询生成或患者筛选，只需少量人工修正。
- 1：部分可用，但需要明显人工修复。
- 0：难以下游使用。

## 错误标签

从以下标签中选择 1 个或多个：

- `missing_key_condition`：遗漏关键条件。
- `extra_condition`：新增原文不支持的条件。
- `wrong_or_logic`：析取条件遗漏或被错误表示为 AND。
- `wrong_and_logic`：必须同时满足的条件遗漏或被错误表示为 OR。
- `wrong_negation`：否定缺失、误加或作用范围错误。
- `wrong_scope_or_grouping`：分组、嵌套或共享修饰语作用范围错误。
- `predicate_fragmentation`：同一临床谓词被拆成混乱片段。
- `overly_verbose`：表达过度冗长并影响可用性。
- `empty_or_unusable`：空输出或不可用。
- `none`：无明显错误标签。

如果没有明显错误，`error_flags` 只能填写 `["none"]`。如果存在其他错误标签，不要同时填写 `none`。

## 输出格式

请严格输出 JSONL。每个候选只输出一行 JSON，不要输出 Markdown 表格，不要输出额外解释文字。

输出字段必须为：

- `candidate_id`
- `predicate_completeness`
- `logical_correctness`
- `grouping_correctness`
- `faithfulness`
- `downstream_usability`
- `total_score`
- `error_flags`
- `brief_rationale`

示例：

```json
{"candidate_id":"EXAMPLE_ID","predicate_completeness":2,"logical_correctness":2,"grouping_correctness":1,"faithfulness":2,"downstream_usability":1,"total_score":8,"error_flags":["wrong_scope_or_grouping"],"brief_rationale":"Main predicates and logic are preserved, but one local grouping is ambiguous."}
```

`total_score` 必须等于五个维度分数之和，范围为 0-10。

## 推荐投喂方式

全量评估约有 8000 个候选，不建议一次性输入。建议每批 20-50 个候选。

可用以下命令导出批次文件：

```powershell
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
```

批次文件位于：

```text
data/evaluation/gpt_manual_batches/
```

每批评估步骤：

1. 粘贴本评估指南。
2. 粘贴一批候选 JSONL。
3. 要求模型只输出同样数量的 JSONL 评分结果。
4. 检查输出行数是否与输入候选数一致。
5. 将输出追加保存到 `results/llm_eval/llm_judge_results.jsonl`。

全部批次保存后运行：

```powershell
python src/criteria_boolean/summarize_llm_judge.py
```

## 给 Codex 或 GPT-5.5 的输入模板

如果使用 Codex 直接读取本项目文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md 中的所有候选。

要求：
1. 只根据每条样本的 source_criterion 和 candidate_expression 评分。
2. 不要读取或使用 data/evaluation/llm_judge/llm_eval_key.csv。
3. 不要推测方法名。
4. 每个 candidate_id 输出一行 JSONL。
5. 输出字段必须包含 candidate_id、五个维度分数、total_score、error_flags、brief_rationale。
6. 不输出 Markdown 表格，不输出额外解释文字。
```

如果需要 Codex 直接写入结果文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md，
并把 JSONL 结果追加保存到 results/llm_eval/llm_judge_results.jsonl。

注意：
- 不要读取 data/evaluation/llm_judge/llm_eval_key.csv。
- 如果结果文件不存在，请创建它。
- 如果输出行数不是25行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM03701", "doc_id": "NCT03182114_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women scheduled for elective cesarean delivery", "candidate_expression": "((cesarean delivery) AND (elective) AND (full term) AND (pregnant) AND (scheduled for) AND (singleton) AND (women))"}
{"candidate_id": "LLM03702", "doc_id": "NCT02056288_exc", "case_bucket": "or", "source_criterion": "Pulseless extremity Compromised neurologic status on exam (specifically assessment of radial, ulnar, and median nerve) Known allergy to local anesthetics (7) Not scheduled for closed reduction with percutaneous pinning under general anesthesia Bleeding diathesis American Society of Anesthesiologist (ASA) status 4 or higher. Sleep apnea by polysomnography", "candidate_expression": "((4 or higher) AND (American Society of Anesthesiologist (ASA) status) AND (Bleeding diathesis) AND (Compromised neurologic status) AND (Not) AND (Pulseless extremity) AND (Sleep apnea) AND (allergy) AND (closed reduction with percutaneous pinning) AND (general anesthesia) AND (local anesthetics) AND (median nerve) AND (nerve radial) AND (nerve ulnar) AND (polysomnography) AND (scheduled for))"}
{"candidate_id": "LLM03703", "doc_id": "NCT03472495_inc", "case_bucket": "or", "source_criterion": ">/= 18 years old Atrial fibrillation or flutter on electrocardiogram Heart rate >110 beats/min Systolic blood pressure >/= 90 mmHg", "candidate_expression": "((>/= 18 years old) AND (>/= 90 mmHg) AND (>110 beats/min) AND (Atrial fibrillation) AND (Atrial flutter) AND (Heart rate) AND (Systolic blood pressure) AND (electrocardiogram) AND (old))"}
{"candidate_id": "LLM03704", "doc_id": "NCT01642875_inc", "case_bucket": "or", "source_criterion": "Primary periampullary tumor R0, R1 resection Chronic pancreatitis requiring pancreatoduodenectomy", "candidate_expression": "((Chronic pancreatitis requiring) AND (pancreatoduodenectomy) AND (periampullary tumor Primary) AND ((R0 resection) OR (R1 resection)))"}
{"candidate_id": "LLM03705", "doc_id": "NCT03260790_exc", "case_bucket": "other", "source_criterion": "Research exemption requested History of PCV-13 vaccination History of cochlear implant Cerebrospinal Fluid (CSF) leak Congestive Heart Failure (CHF) Diabetes Mellitus (DM) Chronic Kidney Disease (CKD) Human Immunodeficiency Virus (HIV) Common Variable Immune Deficiency (CVID) Patients who have received the PPSV23 vaccine in the last 5 years Women who are pregnant will also be excluded from the study by performing 2 point of care urine pregnancy tests ( prior to vaccinations)", "candidate_expression": "((Cerebrospinal Fluid (CSF) leak) AND (Chronic Kidney Disease (CKD)) AND (Common Variable Immune Deficiency (CVID)) AND (Congestive Heart Failure (CHF)) AND (Diabetes Mellitus (DM)) AND (Human Immunodeficiency Virus (HIV)) AND (PCV-13 vaccination History) AND (PPSV23 vaccine in the last 5 years) AND (Research exemption requested) AND (Women) AND (cochlear implant History) AND (point of care urine pregnancy tests 2 prior to vaccinations) AND (pregnant) AND (vaccinations))"}
{"candidate_id": "LLM03706", "doc_id": "NCT02570321_inc", "case_bucket": "or", "source_criterion": "Corneal ulcer that is smear positive for either bacteria or filamentous fungus Pinhole visual acuity worse than 20/70 in the affected eye Not treated already with antimicrobial medications at presentation Age over 18 years Basic understanding of the study as determined by the physician Commitment to return for follow up visits", "candidate_expression": "((Age) AND (Commitment to return for follow up visits) AND (Corneal ulcer) AND (Pinhole visual acuity) AND (antimicrobial medications) AND (over 18 years) AND (positive) AND (smear) AND (worse than 20/70) AND ((bacteria) OR (filamentous fungus)))"}
{"candidate_id": "LLM03707", "doc_id": "NCT01650792_exc", "case_bucket": "or", "source_criterion": "Patients with a history of an untreated malignancy (except local skin cancers) Ischemic stroke (determined using the Questionnaire for Verifying Stroke-Free Status (QVSFS) Patients on renal dialysis or with end-stage hepatic dysfunction Acute infection/inflammation (Temperature > 101.5 F, and/or WBC> 15, 000) Inability to obtain informed consent from patient or next of kin Anticoagulant use (warfarin or heparin)", "candidate_expression": "((Anticoagulant) AND (Inability to obtain informed consent from patient or next of kin) AND (Ischemic stroke Questionnaire for Verifying Stroke-Free Status (QVSFS)) AND (malignancy untreated) AND NOT (local skin cancers) AND ((infection) OR (inflammation)) AND ((Temperature > 101.5 F) OR (WBC > 15, 000)) AND ((heparin) OR (warfarin)) AND ((end-stage hepatic dysfunction) OR (renal dialysis)))"}
{"candidate_id": "LLM03708", "doc_id": "NCT02907554_exc", "case_bucket": "or", "source_criterion": "Contra-indication for multiorgan procurement (infections, cancer, etc) Preexistent chronic renal failure. Refusal for organ procurement by the donor (confirmed by the French national register or reported by the next-of-kin). Need for a double kidney transplantation. Need for a multiorgan transplantation", "candidate_expression": "((Contra-indication) AND (Refusal by the donor French national register reported by the next-of-kin) AND (cancer) AND (chronic renal failure Preexistent) AND (double kidney transplantation Need for) AND (infections) AND (multiorgan procurement) AND (multiorgan transplantation Need for) AND (organ procurement))"}
{"candidate_id": "LLM03709", "doc_id": "NCT02645474_inc", "case_bucket": "or", "source_criterion": "adult patients ASA class 1 to 3 patients patients scheduled for elective breast mastectomy or quadrantectomy", "candidate_expression": "((1 to 3) AND (ASA class) AND (adult) AND (breast quadrantectomy) AND (elective) AND (mastectomy))"}
{"candidate_id": "LLM03710", "doc_id": "NCT02876484_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting plasma glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((3 months after RYGB) AND (< 48 mmol/mol) AND (< 7,0 mM) AND (Fasting plasma glucose) AND (HbA1c) AND (RYGB) AND (Uncomplicated) AND (minimum 3 months prior to the study) AND (the study))"}
{"candidate_id": "LLM03711", "doc_id": "NCT03434951_inc", "case_bucket": "other", "source_criterion": "elective primary total knee arthroplasty ASA I-III written consent", "candidate_expression": "((ASA) AND (I-III) AND (elective) AND (primary) AND (total knee arthroplasty) AND (written consent))"}
{"candidate_id": "LLM03712", "doc_id": "NCT02958566_exc", "case_bucket": "or", "source_criterion": "History of constipation Pre-existing use of narcotics or opioids Pre-existing renal or hepatic failure Mental illness, mental retardation, or inability to participate in informed consent due to mental status Pre-existing dementia Allergy to any protocol medication Emergency operation Subjects who are incarcerated or wards of the state Minors Subjects with inflammatory bowel disease, active colitis, or pre-existing intra-abdominal inflammation. Diverticulitis without active infection/inflammation will not be excluded.", "candidate_expression": "((Allergy) AND (Diverticulitis) AND (Emergency) AND (Mental illness) AND (Minors) AND (Pre-existing) AND (active) AND (colitis) AND (constipation) AND (dementia) AND (hepatic failure) AND (inability to participate in informed consent) AND (infection) AND (inflammation) AND (inflammatory bowel disease) AND (intra-abdominal inflammation) AND (mental retardation) AND (mental status) AND (narcotics) AND (not be excluded) AND (operation) AND (opioids) AND (pre-existing) AND (renal failure) AND (without))"}
{"candidate_id": "LLM03713", "doc_id": "NCT03663387_inc", "case_bucket": "or", "source_criterion": "Male and female subjects between 40-85 years old will be enrolled. Younger subjects are not included as the risk for brain amyloid lesions is too low All subjects will speak English as their first language or demonstrate proficiency in English (defined as reaching a scaled score of > 11 on the WAIS vocabulary test). All subjects will have normal cognition at baseline: a Clinical Dementia Rating CDR=0, Global Deterioration Scale GDS<2. All subjects will be in good general health and able to participate in the LP and imaging exams. This determination is made by the study neurologist and reviewed at a consensus meeting for each subject.", "candidate_expression": "((<2) AND (=0) AND (> 11) AND (Clinical Dementia Rating CDR) AND (Global Deterioration Scale GDS) AND (LP) AND (Male) AND (WAIS vocabulary test) AND (able to participate) AND (at baseline) AND (between 40-85 years) AND (female) AND (first language) AND (good general health) AND (imaging exams) AND (normal cognition) AND (old) AND (proficiency in English) AND (speak English))"}
{"candidate_id": "LLM03714", "doc_id": "NCT02429765_inc", "case_bucket": "scope", "source_criterion": "Moderate to severe COPD (post-bronchodilator forced expiratory volume in 1 s (FEV1) 30-79%predicted); Resting functional residual capacity (FRC) >120% predicted; Clinically stable and on stable triple therapy with an ICS/LABA and tiotropium; Symptomatic: Baseline Dyspnea Index =8 and answer \"in the morning\" when asked about what time of day their COPD symptoms are worst.", "candidate_expression": "((30-79%predicted) AND (=8) AND (>120% predicted) AND (Baseline Dyspnea Index) AND (COPD) AND (Clinically stable) AND (ICS/LABA) AND (Moderate to severe) AND (Resting functional residual capacity (FRC)) AND (forced expiratory volume in 1 s (FEV1)) AND (in the morning) AND (post-bronchodilator) AND (stable triple therapy) AND (tiotropium) AND (what time of day their COPD symptoms are worst))"}
{"candidate_id": "LLM03715", "doc_id": "NCT03400735_exc", "case_bucket": "or", "source_criterion": "Pregnancy or breastfeeding Allergy against to penicillin or cephalosporins Renal impairment Active hepatic disease Antibiotic use except study drugs Immunosuppressive therapy before 6 months of study initiation Use of probenecid like drugs", "candidate_expression": "((Allergy) AND (Antibiotic) AND (Immunosuppressive therapy before 6 months of study initiation) AND (Pregnancy) AND (Renal impairment) AND (breastfeeding) AND (cephalosporins) AND (hepatic disease Active) AND (penicillin) AND (probenecid like drugs) AND (probenecid probenecid like) AND NOT (study drugs))"}
{"candidate_id": "LLM03716", "doc_id": "NCT00989261_inc", "case_bucket": "or", "source_criterion": "1. Males and females age ≥18 years in second relapse or refractory. 2. Males and females age ≥60 years in first relapse or refractory. 3. Must have baseline bone marrow sample taken. 4. Morphologically documented primary AML or AML secondary to myelodysplastic syndrome (MDS with ≥20% bone marrow or peripheral blasts), as defined by the World Health Organization (WHO) criteria, confirmed by pathology review at treating institution. 5. Able to swallow the liquid study drug. 6. ECOG performance status of 0 to 2 7. In the absence of rapidly progressing disease, the interval from prior treatment to time of AC220 administration will be at least 2 weeks for cytotoxic agents or at least 5 half-lives for noncytotoxic agents. The use of chemotherapeutic or antileukemic agents other than hydroxyurea is not permitted during the study with the possible exception of intrathecal (IT) therapy at the discretion of the Investigator and with the agreement of the Sponsor. 8. Persistent chronic clinically significant non-hematological toxicities from prior treatment must be ≤Grade 1. 9. Prior therapy with FLT3 inhibitors is permitted, except previous treatment with AC220. 10. Serum creatinine ≤1.5 × ULN and glomerular filtration rate (GFR) > 30 mL/min 11. Serum potassium, magnesium, and calcium levels should be at least within institutional normal limits. 12. Total serum bilirubin ≤1.5 × ULN 13. Serum aspartate transaminase (AST) and/or alanine transaminase (ALT) ≤2.5 × ULN 14. Females of childbearing potential must have a negative pregnancy test (urine β-hCG). 15. Females of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study. 16. Written informed consent must be provided.", "candidate_expression": "((0 to 2) AND (> 30 mL/min) AND (AC220) AND (Able to swallow the liquid study drug.) AND (ECOG performance status) AND (FLT3 inhibitors) AND (Females) AND (Females of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study.) AND (Females of childbearing potential must have a negative pregnancy test (urine β-hCG).) AND (MDS) AND (Males) AND (Morphologically documented) AND (Serum calcium) AND (Serum creatinine) AND (Serum magnesium) AND (Serum potassium) AND (Total serum bilirubin) AND (World Health Organization (WHO) criteria) AND (Written informed consent must be provided.) AND (age) AND (at least within institutional normal limits) AND (baseline) AND (bone marrow sample) AND (childbearing potential) AND (clinically significant) AND (except) AND (females) AND (first) AND (from prior treatment) AND (glomerular filtration rate (GFR)) AND (myelodysplastic syndrome) AND (negative) AND (non-hematological) AND (pathology review) AND (permitted) AND (pregnancy test) AND (primary) AND (prior) AND (second) AND (therapy) AND (toxicities) AND (treatment) AND (urine β-hCG) AND (≤1.5 × ULN) AND (≤2.5 × ULN) AND (≤Grade 1) AND (≥18 years) AND (≥20%) AND (≥60 years) AND ((Males) OR (females)) AND ((AML)) AND ((bone marrow) OR (peripheral blasts)) AND ((refractory) OR (relapse)) AND ((Serum aspartate transaminase (AST)) OR (alanine transaminase (ALT))))"}
{"candidate_id": "LLM03717", "doc_id": "NCT02316886_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Symptomatic or asymptomatic coronary artery disease patients MLA(minimal luminal area)<4mm2 plaque burden>70% Lipid-rich plaque on NIRS(Intracoronary Near-Infrared Spectroscopy) (defined as maxLCBI4mm>315) 2 target vulnerable lesions Eligible for percutaneous coronary intervention with Absorb Bioresorbable Vascular Scaffold or Everolimus Eluting Stent Willing and able to provide informed written consent Reference vessel diameter 2.75-4.0 Lesion length = 40", "candidate_expression": "((Absorb Bioresorbable Vascular Scaffold) AND (Age 18 years or older Symptomatic asymptomatic) AND (Everolimus Eluting Stent) AND (Intracoronary Near-Infrared Spectroscopy) AND (Lesion length = 40) AND (Lipid-rich plaque) AND (MLA <4mm2) AND (NIRS) AND (Reference vessel diameter 2.75-4.0) AND (Willing and able to provide informed written consent) AND (coronary artery disease) AND (maxLCBI4mm >315) AND (minimal luminal area) AND (percutaneous coronary intervention Eligible for) AND (plaque burden >70%) AND (target vulnerable lesions 2))"}
{"candidate_id": "LLM03718", "doc_id": "NCT01728194_exc", "case_bucket": "or", "source_criterion": "Psychotic depression by DSM-IV, i.e., presence of delusions with a SCID-R score higher than 2; High suicide risk, i.e. intent or plan to attempt suicide in near future; Presence of any Axis I psychiatric disorder (other than unipolar major depression) or substance abuse; History of psychiatric disorders other than unipolar major depression or generalized anxiety disorder (bipolar disorder, hypomania, and dysthymia are exclusion criteria); Dementia: Diagnosis of dementia by DSM-IV; Mild Cognitive Impairment (MCI); Acute or severe medical illness, i.e., delirium, metastatic cancer, decompensated cardiac, liver or kidney failure, major surgery, stroke or myocardial infarction during the three months prior to entry; or use of drugs known to cause depression, e.g., reserpine, alpha-methyl-dopa, steroids, sympathomimetics withdrawal; Neurological brain disease and/or history of electroconvulsive therapy; History of any use of citalopram or escitalopram during the current episode or need for drugs that may interact with these agents, i.e. drug metabolized by the 2D6 P450 isoenzyme system; Current involvement in psychotherapy; Contraindications to MRI scanning including cardiac pacemaker, metallic objects and metallic implants contraindicating MRI, cardiac stent, claustrophobia; Inability to speak English; Corrected visual acuity < 20/70; Color blindness.", "candidate_expression": "((< 20/70;) AND (Axis I) AND (Contraindications) AND (Corrected) AND (DSM-IV) AND (Dementia) AND (High) AND (Inability to speak English) AND (MCI) AND (MRI) AND (Mild Cognitive Impairment) AND (Neurological) AND (Psychotic depression) AND (SCID-R score) AND (agents) AND (attempt suicide) AND (current) AND (decompensated) AND (delusions) AND (depression) AND (drugs) AND (entry) AND (episode) AND (higher than 2) AND (in near future) AND (other than) AND (psychiatric disorder) AND (psychiatric disorders) AND (psychotherapy) AND (substance abuse) AND (suicide risk) AND (three months prior to entry) AND (unipolar major depression) AND ((generalized anxiety disorder) OR (unipolar major depression)) AND ((bipolar disorder) OR (dysthymia) OR (hypomania)) AND ((Acute) OR (severe)) AND ((delirium) OR (major surgery) OR (metastatic cancer) OR (myocardial infarction) OR (stroke)) AND ((cardiac failure) OR (kidney failure) OR (liver failure)) AND ((drugs) OR (medical illness)) AND ((alpha-methyl-dopa) OR (reserpine) OR (steroids) OR (sympathomimetics withdrawal)) AND ((brain disease) OR (electroconvulsive therapy)) AND ((citalopram) OR (escitalopram)) AND ((cardiac pacemaker) OR (cardiac stent) OR (claustrophobia) OR (metallic implants) OR (metallic objects)) AND ((intent) OR (plan to)) AND ((Color blindness) OR (visual acuity)))"}
{"candidate_id": "LLM03719", "doc_id": "NCT02015494_inc", "case_bucket": "other", "source_criterion": "Males and females aged 18-40 years of age at the time of vaccination in good health as determined by medical history, physical exam, laboratory assessments and the clinical judgment of the Principal Investigator Able to provide informed consent indicating that they understand the purpose of this study and are willing to adhere to the procedures described in this protocol If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential. Willing to receive the unlicensed vaccine given as an IM injection Willing to provide multiple blood specimens collected by venipuncture", "candidate_expression": "((18-40 years) AND (IM injection) AND (If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential.) AND (Males) AND (age) AND (aged) AND (at the time of vaccination) AND (females) AND (good health) AND (laboratory assessments) AND (medical history) AND (physical exam) AND (the clinical judgment of the Principal Investigator) AND (time of vaccination) AND (vaccine))"}
{"candidate_id": "LLM03720", "doc_id": "NCT02546856_exc", "case_bucket": "or", "source_criterion": "Contraindications for BB. Living in a nursing home. Life expectancy < 6 months. Unable to self-care or mental disease without caregiver. Unable to weight Without phone Unable to go to clinic visit.", "candidate_expression": "((< 6 months) AND (BB) AND (Contraindications) AND (Life expectancy) AND (Living) AND (Unable) AND (Without) AND (go to clinic visit) AND (nursing home) AND (phone) AND (weight) AND (without caregiver) AND ((Unable to self-care) OR (mental disease)))"}
{"candidate_id": "LLM03721", "doc_id": "NCT01642875_exc", "case_bucket": "or", "source_criterion": "Metastatic tumor Locally unresectable tumor Previous gastric resection ASA IV-V Age under 18 years Preoperative complete parenteral or enteral feeding Immunosuppressive therapy before operation Severe malnutrition Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia", "candidate_expression": "((ASA) AND (Age) AND (IV-V) AND (Immunosuppressive therapy) AND (Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia) AND (Locally unresectable) AND (Metastatic) AND (Preoperative) AND (Previous) AND (Severe) AND (before operation) AND (complete enteral feeding) AND (complete parenteral feeding) AND (gastric resection) AND (malnutrition) AND (operation) AND (tumor) AND (under 18 years))"}
{"candidate_id": "LLM03722", "doc_id": "NCT02201316_inc", "case_bucket": "or", "source_criterion": "Male and females aged between 18 and 65 years of age inclusive, at the time of signing the informed consent. Healthy as determined by a responsible and experienced physician, based on a medical evaluation including medical history, physical examination, laboratory tests and cardiac monitoring. A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedures. Body weight >= 50 kilogram (kg) and body mass index within the range 19 - 24.9 kg/m^2 (inclusive). A female subject is eligible to participate if she is of: Non-childbearing potential defined as pre-menopausal females with a documented tubal ligation or hysterectomy for this definition, \"documented\" refers to the outcome of the investigator's/designee's review of the subject's medical history for study eligibility, as obtained via a verbal interview with the subject or from the subject's medical records; or postmenopausal defined as 12 months of spontaneous amenorrhea [in questionable cases a blood sample with simultaneous follicle stimulating hormone (FSH) > 40 milli-international units per milliliter (MlU/mL) and estradiol < 40 picograms per mililiter (pg/mL) [<147 picomole per liter] is confirmatory]. Females on hormone replacement therapy (HRT) and whose menopausal status is in doubt will be required to use one of the contraception methods if they wish to continue their HRT during the study. Otherwise, they must discontinue HRT to allow confirmation of post-menopausal status prior to study enrollment. For most forms of HRT, at least 2-4 weeks will elapse between the cessation of therapy and the blood draw; this interval depends on the type and dosage of HRT. Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point. Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle. Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol. This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit. Capable of giving written informed consent, which includes compliance with the requirements and restrictions listed in the consent form Alanine aminotransferase, alkaline phosphatase and bilirubin <=1.5x upper limit of normal (ULN) (isolated bilirubin >1.5xULN is acceptable if bilirubin is fractionated and direct bilirubin <35%). Based on single or averaged corrected QT interval (QTc) values of triplicate electrocardiograms obtained over a brief recording period: QTcF < 450 msec", "candidate_expression": "((12 months) AND (< 40 picograms per mililiter (pg/mL)) AND (< 450 msec) AND (<147 picomole per liter) AND (<=1.5x upper limit of normal (ULN)) AND (> 40 milli-international units per milliliter (MlU/mL)) AND (>1.5xULN) AND (>= 50 kilogram (kg)) AND (A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedur) AND (Alanine aminotransferase) AND (Body weight) AND (Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle.) AND (Females) AND (Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point.) AND (Healthy) AND (Male) AND (Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol.) AND (Non) AND (QTcF) AND (This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit.) AND (age) AND (aged) AND (alkaline phosphatase) AND (as determined by a responsible and experienced physician) AND (at the time of signing the informed consent) AND (averaged) AND (between 18 and 65 years) AND (bilirubin) AND (body mass index) AND (cardiac monitoring) AND (childbearing potential) AND (clinical abnormality) AND (corrected QT interval (QTc)) AND (direct bilirubin) AND (electrocardiograms) AND (estradiol) AND (female) AND (females) AND (follicle stimulating hormone (FSH)) AND (hormone replacement therapy (HRT)) AND (hysterectomy) AND (in doubt) AND (laboratory parameter) AND (laboratory tests) AND (medical evaluation) AND (medical history) AND (menopausal status) AND (outside the reference range) AND (over a brief recording period) AND (physical examination) AND (postmenopausal) AND (pre-menopausal) AND (signing the informed consent) AND (single) AND (spontaneous amenorrhea) AND (tubal ligation) AND (within the range 19 - 24.9 kg/m^2))"}
{"candidate_id": "LLM03723", "doc_id": "NCT02386800_exc", "case_bucket": "other", "source_criterion": "Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy. Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up.", "candidate_expression": "((Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy) AND (Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test.) AND (Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up))"}
{"candidate_id": "LLM03724", "doc_id": "NCT02668978_inc", "case_bucket": "or", "source_criterion": "Patients over the age of 18 years who are able to give their informed consent Lobar and sublobar resections Open, video-assisted thoracoscopic or robotic surgeries Diagnostic or therapeutic procedures", "candidate_expression": "((Diagnostic procedures) AND (Lobar resections) AND (able to give their informed consent) AND (over the age of 18 years) AND (robotic surgeries) AND (sublobar resections) AND (therapeutic procedures) AND (thoracoscopic surgeries))"}
{"candidate_id": "LLM03725", "doc_id": "NCT02957305_exc", "case_bucket": "or", "source_criterion": "patients who do not wish to participate in the project; patients with ectopic pregnancy; patients with comorbidities (heart failure congestive, chronic obstructive pulmonary disease); patients with hypovolemic shock; patients with cervical incompetence; patients with infected miscarriage/abortion (presence of fever, pus from the cervix, leukocytosis [> 14000]); patients with twin pregnancy; patients with Marfan syndrome; patients allergic to misoprostol; patients with coagulopathy; patients with opening of cervical internal os (4 mm of dilatation at the time of consultation); patients with previous surgery of the cervix (conization); patients with concomitant use of IUDs.", "candidate_expression": "((IUDs) AND (Marfan syndrome) AND (abortion) AND (allergic) AND (cervical incompetence) AND (chronic obstructive pulmonary disease) AND (coagulopathy) AND (comorbidities) AND (conization) AND (ectopic pregnancy) AND (fever) AND (heart failure congestive) AND (hypovolemic shock) AND (leukocytosis > 14000) AND (miscarriage) AND (misoprostol) AND (opening of cervical internal os 4 mm of dilatation) AND (patients who do not wish to participate in the project) AND (pregnancy twin) AND (pus from the cervix) AND (surgery cervix))"}
```
