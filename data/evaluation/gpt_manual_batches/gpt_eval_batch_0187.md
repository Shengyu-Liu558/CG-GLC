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
{"candidate_id": "LLM04651", "doc_id": "NCT00356148_inc", "case_bucket": "scope", "source_criterion": "Women at any age with early stage breast cancer (stage I-II) and American Society of Anesthesiologists (ASA) score of I-II.", "candidate_expression": "((American Society of Anesthesiologists (ASA) score) AND (I-II) AND (Women) AND (any age) AND (breast cancer) AND (early) AND (stage))"}
{"candidate_id": "LLM04652", "doc_id": "NCT02256943_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04653", "doc_id": "NCT01907230_inc", "case_bucket": "or", "source_criterion": "Age : from 20 to 90 y/o. HBsAg-positive for more than 6 months and HBV DNA < 2000 IU/ml (Subgroup 1)or HBsAg-negative but anti-HBc positive with HBV DNA < 2000 IU/ml (Subgroup 2). Inflammatory arthritis patients who plan to treat with biological agents, including Humira or Enbrel or Simponi or Orencia or Mabthera or Actemra; as first line biologic treatment is indicated.", "candidate_expression": "((Actemra) AND (Age 20 to 90 y/o) AND (Enbrel) AND (HBV DNA < 2000 IU/ml) AND (HBsAg negative) AND (HBsAg positive more than 6 months) AND (Humira) AND (Inflammatory arthritis) AND (Mabthera) AND (Orencia) AND (Simponi) AND (anti-HBc positive) AND (biological agents))"}
{"candidate_id": "LLM04654", "doc_id": "NCT03156855_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04655", "doc_id": "NCT00312429_inc", "case_bucket": "or", "source_criterion": "Diagnosis reviewed at transplant center and confirmed to fit the criterion for high risk blood disease or cancer, as defined for the study Estimated life expectancy of at least 6 weeks following study entry Cancer and Leukemia Group B (CALGB) performance status less than or equal to 2 White blood cell count, platelet, hematocrit, tuberculosis, aspartate aminotransferase (AST), alanine aminotransferase (ALT), alkaline phosphatase, creatinine, and HIV test results reviewed by transplant center Multiple gated acquisition (MUGA), echocardiogram, cardiac MRI, and/or pulmonary function tests (PFT) performed and reviewed by transplant center (for individuals with an ejection fraction and diffusing capacity [DLCO] of 40-50%, the appropriate cardiology or pulmonary consultations should be considered if the individual has severe heart or lung disease at the initiation of therapy) Sufficient number of umbilical cord blood units available for transplantation If female, willing to use contraception throughout the study", "candidate_expression": "((Cancer and Leukemia Group B (CALGB) performance status) AND (Estimated life expectancy) AND (HIV test results) AND (Multiple gated acquisition (MUGA)) AND (Sufficient number) AND (White blood cell count) AND (alanine aminotransferase (ALT)) AND (alkaline phosphatase) AND (aspartate aminotransferase (AST)) AND (at least 6 weeks following study entry) AND (cancer) AND (cardiac MRI) AND (contraception) AND (creatinine) AND (echocardiogram) AND (female) AND (for transplantation) AND (hematocrit) AND (high risk blood disease) AND (less than or equal to 2) AND (platelet) AND (pulmonary function tests (PFT)) AND (reviewed by transplant center) AND (throughout the study) AND (transplantation) AND (tuberculosis) AND (umbilical cord blood units available))"}
{"candidate_id": "LLM04656", "doc_id": "NCT03228238_inc", "case_bucket": "scope", "source_criterion": "Subject must be at least 30 years of age. Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure. Subject must have symptoms that are consistent with vasospastic angina with planned Coronary angiography and Provocation test.", "candidate_expression": "((Coronary angiography) AND (Provocation test) AND (Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure) AND (age) AND (at least 30 years) AND (planned) AND (symptoms) AND (vasospastic angina))"}
{"candidate_id": "LLM04657", "doc_id": "NCT02823808_inc", "case_bucket": "other", "source_criterion": "Type 2 Diabetes Mellitus patients Patient who had been diagnosed within the previous 12 months with HbA1c levels of 8.0-12.0%, did not have a medical history related to diabetes, and did not display proliferative retinopathy", "candidate_expression": "((8.0-12.0%) AND (HbA1c) AND (Type 2 Diabetes Mellitus) AND (medical history related to diabetes) AND (not) AND (previous 12 months) AND (proliferative retinopathy))"}
{"candidate_id": "LLM04658", "doc_id": "NCT02692651_inc", "case_bucket": "other", "source_criterion": "Patients 18 years of age or older with >3 unformed stools/24 hours with positive stool test for C. difficile. Patients receiving = 1 high or medium risk antibiotic for treatment of an infection other than CDI, for an anticipated duration of = 5 days from the time of enrollment.", "candidate_expression": "((age or older 18 years) AND (stool test positive C. difficile) AND (unformed stools >3 24 hours))"}
{"candidate_id": "LLM04659", "doc_id": "NCT02649114_exc", "case_bucket": "other", "source_criterion": "current suicidal risk current psychosis ongoing trauma (e.g. current involvement in an abusive relationship).", "candidate_expression": "((current) AND (involvement in an abusive relationship) AND (ongoing) AND (psychosis) AND (suicidal risk) AND (trauma))"}
{"candidate_id": "LLM04660", "doc_id": "NCT02872090_inc", "case_bucket": "other", "source_criterion": "patients with FEV1 / FVC <70%", "candidate_expression": "((<70%) AND (FEV1 / FVC))"}
{"candidate_id": "LLM04661", "doc_id": "NCT00050349_exc", "case_bucket": "or", "source_criterion": "Patients with symptomatic CNS metastases or leptomeningeal involvement Patients with known brain metastases, unless these metastases have been treated and/or have been stable for at least six months prior to study start. Subjects with a history of brain metastases must have a head CT with contrast to document either response or progression. Patients with bone metastases as the only site(s) of measurable disease Patients with hepatic artery chemoembolization within the last 6 months (one month if there are other sites of measurable disease) Patients who have been previously treated with radioactive directed therapies Patients who have been previously treated with epothilone Patients with any peripheral neuropathy or unresolved diarrhea greater than Grade 1 Patients with severe cardiac insufficiency patients taking Coumadin or other warfarin-containing agents with the exception of low dose warfarin (1 mg or less) for the maintenance of in-dwelling lines or ports Patients taking any experimental therapies history of another malignancy within 5 years prior to study entry except curatively treated non-melanoma skin cancer, prostate cancer, or cervical cancer in situ Patients with active or suspected acute or chronic uncontrolled infection including abcesses or fistulae Patients with a medical or psychiatric illness that would preclude study or informed consent and/or history of noncompliance to medical regimens or inability or unwillingness to return for all scheduled visits HIV+ patients Pregnant or lactating females.", "candidate_expression": "((Grade greater than 1) AND (HIV +) AND (HIV+) AND (another malignancy history of within 5 years prior to study entry) AND (bone metastases only site(s) of measurable disease) AND (brain metastases) AND (epothilone previously) AND (head CT with contrast) AND (hepatic artery chemoembolization) AND (history of) AND (radioactive directed therapies previously) AND (severe cardiac insufficiency) AND (uncontrolled infection) AND NOT (warfarin low dose 1 mg or less) AND ((CNS metastases symptomatic) OR (leptomeningeal involvement symptomatic)) AND ((one month other sites of measurable disease) OR (within the last 6 months)) AND ((peripheral neuropathy) OR (unresolved diarrhea)) AND ((Coumadin) OR (warfarin-containing agents)) AND ((in-dwelling lines) OR (in-dwelling ports)) AND ((cervical cancer in situ) OR (non-melanoma skin cancer) OR (prostate cancer)) AND ((abcesses) OR (fistulae)) AND ((active) OR (suspected)) AND ((acute) OR (chronic)) AND ((medical illness) OR (psychiatric illness)) AND ((inability to return for all scheduled visits) OR (informed consent) OR (noncompliance to medical regimens) OR (preclude study) OR (unwillingness to return for all scheduled visit)) AND ((been stable for at least six months prior to study start) OR NOT (treated)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM04662", "doc_id": "NCT03208244_inc", "case_bucket": "scope", "source_criterion": "Recipient is Age = 18 years Serum ALT within normal limits with no history of liver disease Lack of sensitization (i.e. PRA < 20%) that would be expected to result in a high likelihood of needing aggressive immunosuppression to treat rejection", "candidate_expression": "((< 20%) AND (= 18 years) AND (Age) AND (Lack of) AND (PRA) AND (Serum ALT) AND (history) AND (liver disease) AND (no) AND (sensitization) AND (within normal limits))"}
{"candidate_id": "LLM04663", "doc_id": "NCT03589105_exc", "case_bucket": "or", "source_criterion": "Diagnosis of primary progressive MS Inability to complete an MRI (contraindications for MRI include but are not restricted to weight =140 kg, pacemaker, cochlear implants, presence of foreign substances in the eye, intracranial vascular clips, surgery within 6 weeks of entry into the study, coronary stent implanted within 8 weeks prior to the time of the intended MRI, etc…) Gadolinium intolerance History of ischemic cerebrovascular disorders (e.g., stroke, transient ischemic attack) or ischemia of the spinal cord History or known presence of central nervous system (CNS) or spinal cord tumor (e.g., meningioma, glioma) History or known presence of potential metabolic causes of myelopathy (e.g., untreated vitamin B12 deficiency) History or known presence of infectious causes of myelopathy (e.g., syphilis, Lyme disease, human T-lymphotropic virus 1 (HTLV-1), herpes zoster myelopathy) History of genetically inherited progressive CNS degenerative disorder (e.g., hereditary paraparesis; MELAS [mitochondrial myopathy, encephalopathy, lactic acidosis, stroke] syndrome) Neuromyelitis optica History or known presence of systemic autoimmune disorders potentially causing progressive neurologic disease (e.g., lupus, anti-phospholipid antibody syndrome, Sjogren's syndrome, Behçet's disease, sarcoidosis) History of severe, clinically significant brain or spinal cord trauma (e.g., cerebral contusion, spinal cord compression) Vulnerable patients (Patient referred to in Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code)", "candidate_expression": "((Behçet's disease) AND (Gadolinium) AND (Lyme disease) AND (MELAS syndrome) AND (MRI) AND (MRI Inability to complete) AND (MRI intended) AND (Neuromyelitis optica) AND (Sjogren's syndrome) AND (Vulnerable patients Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code) AND (anti-phospholipid antibody syndrome) AND (brain trauma) AND (central nervous system (CNS) tumor) AND (cerebral contusion) AND (cochlear implants) AND (contraindications) AND (coronary stent) AND (encephalopathy) AND (foreign substances in the eye) AND (glioma) AND (hereditary paraparesis) AND (herpes zoster myelopathy) AND (human T-lymphotropic virus 1 (HTLV-1)) AND (implanted within 8 weeks prior to the time of the intended MRI) AND (infectious causes) AND (intolerance) AND (intracranial vascular clips) AND (ischemia of the spinal cord) AND (ischemic cerebrovascular disorders) AND (lactic acidosis) AND (lupus) AND (meningioma) AND (metabolic causes) AND (mitochondrial myopathy) AND (myelopathy) AND (pacemaker) AND (progressive CNS degenerative disorder genetically inherited) AND (progressive MS primary) AND (progressive neurologic disease potentially causing) AND (sarcoidosis) AND (spinal cord compression) AND (spinal cord trauma) AND (spinal cord tumor) AND (stroke) AND (surgery within 6 weeks of entry into the study) AND (syphilis) AND (systemic autoimmune disorders) AND (transient ischemic attack) AND (vitamin B12 deficiency untreated) AND (weight =140 kg))"}
{"candidate_id": "LLM04664", "doc_id": "NCT02550028_inc", "case_bucket": "or", "source_criterion": "Male or female term baby with gestational >37 weeks and postnatal age < or= 28 days Birthweight >2500g Written informed consent of parent or guardian", "candidate_expression": "((< or= 28 days) AND (>2500g) AND (>37 weeks) AND (Birthweight) AND (Male) AND (Written informed consent of parent or guardian) AND (baby) AND (female) AND (gestational) AND (postnatal age) AND (term))"}
{"candidate_id": "LLM04665", "doc_id": "NCT01320579_exc", "case_bucket": "or", "source_criterion": "History of other significant skin disease, or skin manifestations of allergic illness or other dermatologic condition, except chronic moderate or severe atopic dermatitis, that would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator Present symptoms of other skin diseases, except chronic atopic dermatitis, that could disturb the study assessment and evaluation of the skin Current use of any active systemic medication for chronic atopic dermatitis within one month Current use of active topical medication in the planned investigational area for chronic atopic dermatitis within two weeks History of a sunny holiday, UV-light therapy or solarium use within one month before beginning of study treatments, or planning such during the study or within 7 days after the study Allergy to cis-UCA, or any constituents of the placebo emulsion cream or any constituents of Protopic® ointment History of any skin-related cancer Congenital or acquired immunodeficiency or ongoing therapy that cause immunosuppression Earlier participation in a clinical study performed with cis-UCA Any clinically significant laboratory test result Suspected current drug or alcohol abuse Clinically significant illness during the 4 weeks prior to the first dose administration Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient Unwillingness or doubtful capacity to comply with the protocol Doubtful availability to complete the study", "candidate_expression": "((Allergy during the study within 7 days after the study) AND (Any clinically significant laboratory test result) AND (Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient) AND (Clinically significant illness during the 4 weeks prior to the first dose administration) AND (Doubtful availability to complete the study) AND (History) AND (Protopic® ointment) AND (UV-light therapy) AND (Unwillingness or doubtful capacity to comply with the protocol) AND (acquired immunodeficiency) AND (alcohol abuse) AND (allergic illness) AND (chronic atopic dermatitis within one month) AND (chronic atopic dermatitis within two weeks) AND (cis-UCA) AND (dermatologic condition chronic moderate) AND (drug abuse) AND (illness Clinically significant during the 4 weeks prior to the first dose administration) AND (immunodeficiency Congenital) AND (immunosuppression) AND (laboratory test clinically significant) AND (placebo emulsion cream) AND (skin disease significant) AND (skin diseases could disturb the study assessment and evaluation of the skin) AND (skin manifestations) AND (skin-related cancer) AND (solarium use beginning of study treatments) AND (sunny holiday) AND (systemic medication active) AND (therapy that cause immunosuppression ongoing that cause immunosuppression) AND (topical medication active) AND (would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator) AND NOT (chronic atopic dermatitis) AND NOT (atopic dermatitis severe))"}
{"candidate_id": "LLM04666", "doc_id": "NCT02564471_inc", "case_bucket": "or", "source_criterion": "Provide signed and dated informed consent form. Willing to comply with all study procedures and be available for the duration of the study. Male or female, aged = 18 to = 60 years on day of inclusion. In good general health based on medical history and physical exam", "candidate_expression": "((Male) AND (Willing to comply with all study procedures and be available for the duration of the study.) AND (aged = 18 to = 60 years) AND (female) AND (good general health medical history) AND (physical exam))"}
{"candidate_id": "LLM04667", "doc_id": "NCT02867618_exc", "case_bucket": "or", "source_criterion": "1. Prior Therapy Exposure to chemotherapy or radiotherapy within 2 weeks prior to entering the study or those who have not recovered from adverse events due to agents administered more than 2 weeks earlier. Systemic steroids that have not been stabilized (≥ 5 days) to the equivalent of ≤10 mg/day prednisone prior to the start of the study drugs. No other investigational agents are allowed. 2. History of allergic reactions to TGR-1202 or carfilzomib 3. Uncontrolled inter-current illness 4. Pregnant women 5. Nursing women 6. Current malignancy or history of a prior malignancy 7. Patient known to be Human Immunodeficiency Virus (HIV)-positive 8. Active Hepatitis A, Hepatitis B, or Hepatitis C infection", "candidate_expression": "((Hepatitis A) AND (Hepatitis B) AND (Hepatitis C) AND (Human Immunodeficiency Virus (HIV) positive) AND (Nursing) AND (Pregnant) AND (Systemic steroids stabilized) AND (TGR-1202) AND (adverse events) AND (agents more than 2 weeks earlier) AND (allergic reactions History) AND (carfilzomib Uncontrolled inter-current) AND (chemotherapy) AND (due to) AND (inter-current illness) AND (malignancy Current) AND (malignancy history of a prior) AND (other investigational agents) AND (prednisone ≤10 mg/day) AND (radiotherapy) AND (women) AND NOT (recovered))"}
{"candidate_id": "LLM04668", "doc_id": "NCT02260700_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI; weight [kilogram(kg)]/height^2 [meter square (m^2)]) between 18 and 30 kg/m^2, (inclusive) Be healthy for their age group with or without medication on the basis of physical examination, medical history, vital signs, and 12-lead electrocardiogram (ECG) performed at Screening or admission. Minor deviations in ECG, which are not considered to be of clinical significance to the investigator, are acceptable Be healthy on the basis of clinical laboratory tests performed at Screening. If the results of the serum chemistry panel [including liver enzymes], hematology, or urinalysis are outside the normal reference ranges, the participant may be included only if the investigator judges the abnormalities or deviations from normal to be not clinically significant. This determination must be recorded in the participants' source documents and initialed by the investigator Men who are sexually active with a woman of childbearing potential and have not had a vasectomy must agree to use a barrier method of birth control for example, either condom with spermicidal foam/gel/film/cream/suppository or partner with occlusive cap (diaphragm or cervical/vault caps) with spermicidal foam/gel/film/cream/suppository, and all men must also not donate sperm during the study and for 3 months after receiving the last dose of study drug. In addition, their female partners should also use an appropriate method of birth control for at least the same duration Participants' must have signed an informed consent document indicating that they understand the purpose of and procedures required for the study and are willing to participate in the study", "candidate_expression": "((BMI) AND (Body mass index between 18 and 30 kg/m^2) AND (ECG) AND (Participants' must have signed an informed consent document indicating that they understand the purpose of and procedures required for the study and are willing to participate in the study) AND (clinical laboratory tests performed at Screening) AND (deviations in ECG which are not considered to be of clinical significance to the investigator Screening admission) AND (healthy) AND (hematology) AND (liver enzymes) AND (medical history) AND (not clinically significant) AND (physical examination) AND (serum chemistry panel) AND (the investigator judges) AND (urinalysis) AND (vital signs performed at Screening or admission) AND (weight [kilogram(kg)]/height^2 [meter square (m^2)]) AND (which are not considered to be of clinical significance to the investigator))"}
{"candidate_id": "LLM04669", "doc_id": "NCT02550028_exc", "case_bucket": "or", "source_criterion": "Babies who have been close to death Seizure occurred by metabolic factors (hypoglycemia, hypocalcemia, electrolyte disorder) Babies who have received phenobarbitone or any other anticonvulsive medication before hospitalization Abnormal renal function", "candidate_expression": "((Abnormal) AND (Abnormal renal function) AND (Babies) AND (Seizure) AND (any other) AND (before hospitalization) AND (close to death) AND (have been) AND (hospitalization) AND (metabolic factors) AND (renal function) AND ((anticonvulsive medication) OR (phenobarbitone)) AND ((electrolyte disorder) OR (hypocalcemia) OR (hypoglycemia)))"}
{"candidate_id": "LLM04670", "doc_id": "NCT03193684_exc", "case_bucket": "or", "source_criterion": "eGFR <60 T2DM patients on insulin, GLP-1 RA or SGLT2 treatment Major organ disease type 1 diabetes", "candidate_expression": "((Major organ disease) AND (T2DM) AND (eGFR <60) AND (type 1 diabetes) AND ((GLP-1) OR (RA) OR (SGLT2) OR (insulin)))"}
{"candidate_id": "LLM04671", "doc_id": "NCT02562456_exc", "case_bucket": "or", "source_criterion": "severe behavioral issues presence of fistula or abscess near the selected tooth presence of pulp exposure in the selected tooth presence of mobility in the selected tooth", "candidate_expression": "((abscess) AND (behavioral issues) AND (fistula) AND (mobility) AND (near the selected tooth) AND (pulp exposure) AND (selected tooth) AND (severe))"}
{"candidate_id": "LLM04672", "doc_id": "NCT02035800_inc", "case_bucket": "other", "source_criterion": "Patients aged of 18 and over, Satisfying the 1987 American College of Rheumatology (ACR) criteria for RA Receiving a prescription of Adalimumab 40 mg subcutaneous every two weeks.", "candidate_expression": "((18 and over) AND (1987 American College of Rheumatology (ACR) criteria) AND (40 mg every two weeks) AND (Adalimumab) AND (RA) AND (aged) AND (subcutaneous))"}
{"candidate_id": "LLM04673", "doc_id": "NCT02638935_inc", "case_bucket": "or", "source_criterion": "Female Age ≥18 years Patients with a lesion > 0.5 cm in largest diameter size, initially scored BI-RADS® 3, 4a, 4b or 4c in B-mode ultrasound Informed consent about histological examination (core cut biopsy (CCB), vacuum-assisted biopsy (VAB), fine needle aspiration (FNA) or surgery) has already been given in the course of clinical routine Signed informed consent of study participation", "candidate_expression": "((3, 4a, 4b or 4c) AND (> 0.5 cm) AND (Age) AND (B-mode ultrasound) AND (BI-RADS®) AND (Female) AND (Informed consent) AND (Signed informed consent of study participation) AND (core cut biopsy (CCB)) AND (fine needle aspiration (FNA)) AND (histological examination) AND (largest diameter size) AND (lesion) AND (surgery) AND (vacuum-assisted biopsy (VAB)) AND (≥18 years))"}
{"candidate_id": "LLM04674", "doc_id": "NCT03011476_inc", "case_bucket": "or", "source_criterion": "Parkinson disease diagnosed by United Kingdom Parkinson's disease Society Brain Bank Criteria Postural instability and gait disturbance phenotype Hoehn and Yahr stage = 3 Mini-Mental status examination = 24", "candidate_expression": "((Hoehn and Yahr stage = 3) AND (Mini-Mental status examination = 2) AND (Parkinson disease) AND (United Kingdom Parkinson's disease Society Brain Bank Criteria) AND ((Postural instability) OR (gait disturbance)))"}
{"candidate_id": "LLM04675", "doc_id": "NCT03193684_exc", "case_bucket": "or", "source_criterion": "eGFR <60 T2DM patients on insulin, GLP-1 RA or SGLT2 treatment Major organ disease type 1 diabetes", "candidate_expression": "((<60) AND (GLP-1) AND (Major organ disease) AND (RA) AND (SGLT2) AND (T2DM) AND (eGFR) AND (insulin) AND (type 1 diabetes))"}
```
