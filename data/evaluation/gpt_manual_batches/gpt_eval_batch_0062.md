# GPT Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT 评估指南

本指南用于让大模型对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

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

## 给 Codex 或 GPT 的输入模板

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
- 如果输出行数不是 25 行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM01526", "doc_id": "NCT02765217_inc", "case_bucket": "or", "source_criterion": "Children receiving amoxicilline-clavulanic acid (50-90 mg/kg/day, twice daily) due to acute otitis media or acute sinusitis", "candidate_expression": "((50-90 mg/kg/day) AND (Children) AND (acute otitis media) AND (acute sinusitis) AND (amoxicilline-clavulanic acid) AND (twice daily))"}
{"candidate_id": "LLM01527", "doc_id": "NCT02876484_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB. Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake). Cholecystectomy", "candidate_expression": "((Cholecystectomy) AND (Complications) AND (RYGB) AND (dumping severe) AND (reactive hypoglycaemia) AND ((Fasting plasma glucose > 7,0 mM) OR (HbA1c > 48 mmol/mol)) AND ((antithyroid treatment) OR (thyroid diseases Dysregulated)) AND ((Late diabetic complications) OR (pancreatitis previous)) AND ((neuropathy) OR (renal insufficiency) OR (retinopathy)) AND ((abdominal pain severe after food intake) OR (diarrhea) OR (vomiting)))"}
{"candidate_id": "LLM01528", "doc_id": "NCT02186782_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulation/oligoovulation. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Metabolic or hormonal abnormalities.", "candidate_expression": "((Age) AND (BMI) AND (Body mass index) AND (cytotoxic drugs) AND (infertility factor) AND (pelvic irradiation) AND ((anovulation) OR (oligoovulation)) AND ((ovarian surgery) OR (surgical removal ovary)) AND ((< 20) OR (> 35 years)) AND ((Metabolic abnormalities) OR (hormonal abnormalities)) AND ((< 18.5 kg/m2) OR (> 25 kg/m2)))"}
{"candidate_id": "LLM01529", "doc_id": "NCT02592980_exc", "case_bucket": "or", "source_criterion": "Patients will not be included if they have reached a stable dose of warfarin, liver dysfunction, alcoholism, use of another anticoagulant, use of chemotherapy, or if they do not meet the inclusion criteria", "candidate_expression": "((alcoholism) AND (another) AND (anticoagulant) AND (chemotherapy) AND (if they do not meet the inclusion criteria) AND (liver dysfunction) AND (stable dose) AND (warfarin))"}
{"candidate_id": "LLM01530", "doc_id": "NCT01320579_exc", "case_bucket": "or", "source_criterion": "History of other significant skin disease, or skin manifestations of allergic illness or other dermatologic condition, except chronic moderate or severe atopic dermatitis, that would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator Present symptoms of other skin diseases, except chronic atopic dermatitis, that could disturb the study assessment and evaluation of the skin Current use of any active systemic medication for chronic atopic dermatitis within one month Current use of active topical medication in the planned investigational area for chronic atopic dermatitis within two weeks History of a sunny holiday, UV-light therapy or solarium use within one month before beginning of study treatments, or planning such during the study or within 7 days after the study Allergy to cis-UCA, or any constituents of the placebo emulsion cream or any constituents of Protopic® ointment History of any skin-related cancer Congenital or acquired immunodeficiency or ongoing therapy that cause immunosuppression Earlier participation in a clinical study performed with cis-UCA Any clinically significant laboratory test result Suspected current drug or alcohol abuse Clinically significant illness during the 4 weeks prior to the first dose administration Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient Unwillingness or doubtful capacity to comply with the protocol Doubtful availability to complete the study", "candidate_expression": "((Allergy) AND (Any clinically significant laboratory test result) AND (Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient) AND (Clinically significant) AND (Clinically significant illness during the 4 weeks prior to the first dose administration) AND (Doubtful availability to complete the study) AND (History) AND (Suspected) AND (Unwillingness or doubtful capacity to comply with the protocol) AND (active) AND (atopic dermatitis) AND (beginning of study treatments) AND (chronic atopic dermatitis) AND (clinically significant) AND (could disturb the study assessment and evaluation of the skin) AND (current) AND (during the 4 weeks prior to the first dose administration) AND (except) AND (illness) AND (immunosuppression) AND (laboratory test) AND (ongoing) AND (planning) AND (significant) AND (skin diseases) AND (skin-related cancer) AND (systemic medication) AND (that cause immunosuppression) AND (the first dose administration) AND (topical medication) AND (within one month) AND (within one month before beginning of study treatments) AND (within two weeks) AND (would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator) AND ((skin disease) OR (skin manifestations)) AND ((chronic moderate) OR (severe)) AND ((UV-light therapy) OR (solarium use) OR (sunny holiday)) AND ((during the study) OR (within 7 days after the study)) AND ((Protopic® ointment) OR (cis-UCA) OR (placebo emulsion cream)) AND ((allergic illness) OR (dermatologic condition)) AND ((acquired immunodeficiency) OR (immunodeficiency Congenital) OR (therapy that cause immunosuppression)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM01531", "doc_id": "NCT00391690_exc", "case_bucket": "or", "source_criterion": "Prior treatment with a bisphosphonate Abnormal renal function as evidenced by a calculated creatinine clearance < 30 ml/minute. Corrected (adjusted for serum albumin) serum calcium concentration < 8.0 mg/dl (2.00 mmol/L) or ≥ 12.0 mg/dl (3.00 mmol/L). Patients with clinically symptomatic brain metastases History of diseases with influence on bone metabolism such as Paget's disease and primary hyperparathyroidism Severe physical or psychological concomitant diseases that might impair compliance with the provisions of the study protocol or that might impair the assessment of drug or patient safety, e.g. clinically significant ascites, cardiac failure, NYHA III or IV, clinically relevant pathologic findings in ECG Known hypersensitivity to zoledronic acid or other bisphosphonates Use of other investigational drugs 30 days prior to the date of randomization Known history or present abuse of alcohol or drugs Subjects who, in the opinion of the investigator, are unlikely to cooperate fully during the study Current active dental problems including infection of the teeth or jawbone (maxilla or mandibular); dental or fixture trauma, or a current or prior diagnosis of osteonecrosis of the jaw (ONJ), of exposed bone in the mouth, or of slow healing after dental procedures. Recent (within 6 weeks) or planned dental or jaw surgery (e.g. extraction, implants) Other protocol defined inclusion/exclusion criteria may apply.", "candidate_expression": "((Corrected serum calcium concentration < 8.0 mg/dl 2.00 mmol/L ≥ 12.0 mg/dl 3.00 mmol/L) AND (ECG clinically relevant pathologic findings) AND (History) AND (NYHA III or IV) AND (Paget's disease) AND (abuse of alcohol) AND (abuse of drugs) AND (ascites clinically significant) AND (bisphosphonate Prior) AND (brain metastases clinically symptomatic) AND (calculated creatinine clearance < 30 ml/minute) AND (cardiac failure) AND (dental problems Current) AND (dental surgery) AND (dental trauma current prior) AND (diseases with influence on bone metabolism) AND (exposed bone in the mouth) AND (extraction) AND (fixture trauma) AND (history present) AND (hypersensitivity) AND (implants) AND (infection of the jawbone) AND (infection of the mandibular) AND (infection of the maxilla) AND (infection of the teeth) AND (jaw surgery) AND (osteonecrosis of the jaw (ONJ)) AND (other bisphosphonates) AND (other investigational drugs 30 days prior to the date of randomization) AND (physical diseases) AND (planned) AND (primary hyperparathyroidism) AND (psychological diseases) AND (renal function Abnormal) AND (slow healing after dental procedures Recent within 6 weeks) AND (zoledronic acid))"}
{"candidate_id": "LLM01532", "doc_id": "NCT03389061_inc", "case_bucket": "other", "source_criterion": "Patients with SOF/VEL treatment for the treatment of chronic HCV genotype 1 through 6. Patient is at least 18 at the day of screening. Patient is able and willing to sign the Informed Consent Form. Patient is able and willing to follow protocol requirements.", "candidate_expression": "((HCV genotype chronic 1 through 6 at least 18 at the day of screening) AND (Patient is able and willing to follow protocol requirements) AND (Patient is able and willing to sign the Informed Consent Form) AND (SOF/VEL treatment))"}
{"candidate_id": "LLM01533", "doc_id": "NCT03125057_exc", "case_bucket": "or", "source_criterion": "Therapy area located outside of head and neck; Other skin diseases that might interfere with the efficacy evaluation; Therapy area was previously received isotope or PDT or other treatment which might interfere with the efficacy evaluation; Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Immunocompromised conditions; Electrocardiographic abnormalities or organic heart diseases; Coagulation disorders; Hepatic or renal functions abnormal (alanine aminotransferase or aspartate transaminase or total bilirubin > 1.5 upper limit of normal [ULN], or serum creatinine or blood urea nitrogen > 1.5 ULN); Psychiatric diseases; Severe endocrinopathies; Previous therapy of PWS within the last 4 weeks; Participation in any clinical studies within the last 4 weeks; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((> 1.5 ULN) AND (> 1.5 upper limit of normal [ULN]) AND (Allergy) AND (Coagulation disorders) AND (Electrocardiographic) AND (Immunocompromised conditions) AND (PWS) AND (Participation in any clinical studies) AND (Previous) AND (Psychiatric diseases) AND (Scar diathesis) AND (Severe) AND (abnormal) AND (endocrinopathies) AND (interfere with the efficacy evaluation) AND (might interfere with the efficacy evaluation) AND (organic) AND (skin diseases) AND (therapy) AND (treatment) AND (within the last 4 weeks) AND ((analogues) OR (porphyrins)) AND ((Allergic constitution) OR (Photosensitivity) OR (Porphyria)) AND ((Electrocardiographic abnormalities) OR (heart diseases)) AND ((Hepatic functions) OR (renal functions)) AND ((alanine aminotransferase) OR (aspartate transaminase) OR (total bilirubin)) AND ((blood urea nitrogen) OR (serum creatinine)) AND ((PDT) OR (isotope)))"}
{"candidate_id": "LLM01534", "doc_id": "NCT02818816_inc", "case_bucket": "other", "source_criterion": "Males aged 18 years and above Patients with a diagnosis of prostatic carcinoma requiring prostate surgery", "candidate_expression": "((18 years and above) AND (Males) AND (aged) AND (prostate surgery) AND (prostatic carcinoma))"}
{"candidate_id": "LLM01535", "doc_id": "NCT02678728_inc", "case_bucket": "other", "source_criterion": "Patients undergoing thoracic aorta surgery with hypothermic circulatory arrest, over 20-of age", "candidate_expression": "((age) AND (hypothermic circulatory arrest) AND (over 20) AND (surgery) AND (thoracic aorta))"}
{"candidate_id": "LLM01536", "doc_id": "NCT02573597_exc", "case_bucket": "or", "source_criterion": "<37 weeks gestation, H/o Cesarean Section, Multiple Gestation, Pre-eclampsia, Narcotics within 3 hours prior to labor epidural placement, Chronic Pain (as defined by chronic opiate consumption), Women who are participating in another study that will impact protocol", "candidate_expression": "((<37 weeks) AND (H/o) AND (Women who are participating in another study that will impact protocol) AND (chronic) AND (gestation) AND (labor epidural placement) AND (opiate) AND (within 3 hours prior to labor epidural placement) AND ((Cesarean Section) OR (Chronic Pain) OR (Multiple Gestation) OR (Narcotics) OR (Pre-eclampsia)))"}
{"candidate_id": "LLM01537", "doc_id": "NCT01857167_inc", "case_bucket": "or", "source_criterion": "1. Fasting glucose > 7.0 or have diabetes medication; 2. Male, 35-80 years; female, postmenopausal to 80 years; 3. Agree to participant in the trial.", "candidate_expression": "((35-80 years) AND (> 7.0) AND (Agree to participant in the trial.) AND (Male) AND (diabetes) AND (female) AND (postmenopausal) AND (to 80 years) AND ((Fasting glucose) OR (diabetes medication)))"}
{"candidate_id": "LLM01538", "doc_id": "NCT02546856_inc", "case_bucket": "other", "source_criterion": "Patient with \"de novo\" heart Failure and LVEF <= 40% admitted in hospital, without contraindications for BB prescription with cardiologist up-titration prescription and without having achieved BB target dose previous discharge and signing informed consent.", "candidate_expression": "((<= 40%) AND (BB) AND (LVEF) AND (admitted) AND (contraindications) AND (de novo) AND (heart Failure) AND (hospital) AND (without))"}
{"candidate_id": "LLM01539", "doc_id": "NCT03004261_inc", "case_bucket": "or", "source_criterion": "Any allogeneic stem cell transplant recipient = 14 years of age and = 60 years of age Bilirubin/ SGOT/SGPT < 5 × upper normal limits. Creatinine < 2 × upper normal limits. Ejection fraction = 50%, no severe arrhythmia. Estimated life expectancy = 6 months. Patients' CMV-DNA = 1000cp/ml in treatment group and being negative in prophylactic group.", "candidate_expression": "((Bilirubin < 5 × upper normal limits) AND (CMV-DNA) AND (Creatinine < 2 × upper normal limits) AND (Estimated life expectancy = 6 months) AND (SGOT < 5 × upper normal limits) AND (SGPT < 5 × upper normal limits) AND (age = 14 years) AND (age = 60 years) AND (allogeneic stem cell transplant) AND ((Ejection fraction = 50%) OR NOT (arrhythmia severe)) AND ((prophylactic group negative) OR (treatment group = 1000cp/ml)))"}
{"candidate_id": "LLM01540", "doc_id": "NCT00183885_inc", "case_bucket": "other", "source_criterion": "Unresectable, histologically confirmed hepatocellular carcinoma with evident disease limited to liver. Tissue from tumor must be available. This may be paraffin embedded tissue from previous biopsy/resection or if it is not available, a repeat biopsy must be performed. The requirement for biopsy may be waived if alpha-fetoprotein is greater than 500 ng/mL and in the investigators opinion not explained by a concurrent hepatic inflammatory process. Patients must agree to have a 20 cc blood sample drawn in addition to routine labs with each cycle of chemotherapy. Patients must have measurable disease. If prior radiation therapy was administered, measurable disease must be outside the radiation field. Patients must have a Zubrod performance status of 0-2. Patients must have a predicted life expectancy of at least 12 weeks. Patients must have a pre-treatment granulocyte count (i.e., segmented neutrophils + bands) of greater than or equal to 1,500/mm3, a hemoglobin level of greater than or equal to 9 gm/dl, and platelet count greater than or equal to 50,000/mm3. The granulocyte requirement may be waived if in the investigator's opinion the lower count reflects hypersplenism with adequate bone marrow reserves. Patients must have adequate renal function as documented by a calculated creatinine clearance ≥ 60. Patients must have adequate hepatic function as documented by a serum bilirubin less than or equal to 2x the institutional upper limit of normal, regardless of whether patients have liver involvement secondary to tumor. Patients may not have ascites or the ascites must be responsive to diuretics.", "candidate_expression": "((Zubrod performance status 0-2) AND (agree to) AND (alpha-fetoprotein greater than 500 ng/mL) AND (ascites responsive to diuretics) AND (biopsy) AND (blood sample drawn 20 cc) AND (calculated creatinine clearance ≥ 60) AND (granulocyte count greater than or equal to 1,500/mm3) AND (hemoglobin level greater than or equal to 9 gm/dl) AND (hepatic function adequate) AND (hepatocellular carcinoma Unresectable disease limited to liver) AND (histologically confirmed) AND (platelet count greater than or equal to 50,000/mm3) AND (predicted life expectancy at least 12 weeks) AND (radiation therapy measurable disease measurable disease) AND (renal function adequate) AND (routine labs) AND (segmented neutrophils + bands) AND (serum bilirubin less than or equal to 2x the institutional upper limit of normal) AND NOT (ascites))"}
{"candidate_id": "LLM01541", "doc_id": "NCT02788045_exc", "case_bucket": "or", "source_criterion": "Has chronic hepatitis B (measured by hepatitis B surface antigen test) or active hepatitis C (measured by hepatitis C virus [HCV] Ab test; if positive, HCV ribonucleic acid [RNA] PCR test will be used to confirm active versus past HCV infection), active syphilis infection, chlamydia, gonorrhea, or trichomonas . Active syphilis documented by serology unless positive serology is due to past treated infection Has had a thyroidectomy or active thyroid disease requiring medication during the last 12 months (not excluded: a stable thyroid supplementation) Has had major psychiatric illness and/or substance abuse problems during the past 12 months (including hospitalization or periods of work disability) that in the opinion of the investigator would preclude participation Has been in receipt of any licensed vaccine within 14 days prior to the first dose of study vaccine/placebo, plans to receive within 14 days after the first study vaccination, or plans to receive within 14 days before or after the second, third or fourth vaccination Is a recipient of a prophylactic or therapeutic HIV vaccine candidate at any time, or a recipient of other experimental vaccine(s) within the last 12 months. For participants who received an experimental vaccine (except HIV vaccine) more than 12 months ago, documentation of the identity of the experimental vaccine must be provided to the sponsor, who will determine eligibility on a case-by-case basis", "candidate_expression": "((Active) AND (HCV ribonucleic acid [RNA] PCR test) AND (HIV vaccine) AND (active) AND (at any time) AND (case-by-case basis) AND (during the last 12 months) AND (during the past 12 months) AND (except) AND (experimental vaccine) AND (first study vaccination) AND (hepatitis B surface antigen test) AND (hepatitis C virus [HCV] Ab test) AND (in the opinion of the investigator) AND (licensed vaccine) AND (major) AND (medication) AND (more than 12 months ago) AND (not excluded) AND (placebo) AND (positive) AND (psychiatric illness) AND (second, third or fourth vaccination) AND (stable) AND (study vaccination) AND (study vaccine) AND (substance abuse) AND (the first dose of study vaccine/placebo) AND (thyroid supplementation) AND (treated infection) AND (unless) AND (vaccination) AND (within the last 12 months) AND ((serology)) AND ((thyroid disease) OR (thyroidectomy)) AND ((active hepatitis C) OR (chlamydia) OR (chronic hepatitis B) OR (gonorrhea) OR (syphilis) OR (syphilis infection) OR (trichomonas)) AND ((hospitalization) OR (work disability)) AND ((within 14 days after) OR (within 14 days before or after) OR (within 14 days prior)) AND ((HIV vaccine candidate) OR (other experimental vaccine(s))) AND ((prophylactic) OR (therapeutic)))"}
{"candidate_id": "LLM01542", "doc_id": "NCT00312429_exc", "case_bucket": "or", "source_criterion": "Undergoing Interleukin-2 (IL-2) therapy within 8 weeks of study entry Diagnosed with a medical or psychiatric illness that may interfere with study participation Pregnant", "candidate_expression": "((Interleukin-2 (IL-2) therapy) AND (Pregnant) AND (illness that may interfere with study participation medical) AND (psychiatric illness that may interfere with study participation) AND (within 8 weeks of study entry))"}
{"candidate_id": "LLM01543", "doc_id": "NCT02632760_exc", "case_bucket": "or", "source_criterion": "Pregnancy Known hypersensitivity to study drug (ferric carboxymaltose or equivalent) or its excipients Known or suspected haemoglobinopathy/thalassaemia Bone marrow disease Haemochromatosis Renal dialysis Erythropoietin or IV iron in the previous 4 weeks", "candidate_expression": "((Bone marrow disease) AND (Haemochromatosis) AND (Pregnancy) AND (Renal dialysis in the previous 4 weeks) AND (ferric carboxymaltose) AND (hypersensitivity) AND (study drug) AND ((Erythropoietin) OR (IV iron)) AND ((haemoglobinopathy) OR (thalassaemia)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM01544", "doc_id": "NCT01824537_inc", "case_bucket": "other", "source_criterion": "Couple must have been in a new relationship that started no more than six months prior to study entry Both partners plan on remaining in Montreal for at least 1 year Plan on having continued sexual contact with partner Be willing to comply with study procedures", "candidate_expression": "((Be willing to comply with study procedures) AND (having continued sexual contact with partner Plan on) AND (new relationship no more than six months prior to study entry) AND (remaining in Montreal plan on for at least 1 year))"}
{"candidate_id": "LLM01545", "doc_id": "NCT03477851_inc", "case_bucket": "other", "source_criterion": "Patients with foot fracture scheduled for surgical repair in spinal anesthesia Informed consent", "candidate_expression": "((Informed consent) AND (foot fracture) AND (scheduled for) AND (spinal anesthesia) AND (surgical repair))"}
{"candidate_id": "LLM01546", "doc_id": "NCT02489045_exc", "case_bucket": "or", "source_criterion": "Females who are pregnant or nursing. Patients not scheduled for trans-jugular liver biopsy Patients who have received an investigational drug in the 30 days before study drug administration, or will receive one within 72 h afterwards,. Patients with known or suspected right-to-left, bi-directional, or transient right-to-left cardiac shunts Patients with pulmonary hypertension or unstable cardiopulmonary conditions Patients currently on chemotherapy or with other primary cancers requiring systemic or hepatic loco-regional treatment. Patients who are medically unstable, patients who are seriously or terminally ill, and patients whose clinical course is unpredictable. For example: Patients on life support or in a critical care unit. Patients with unstable occlusive disease (e.g., crescendo angina) Patients with clinically unstable cardiac arrhythmias, such as recurrent ventricular tachycardia. Patients with uncontrolled congestive heart failure (NYHA Class IV) Patients with recent cerebral hemorrhage. Patients who have undergone surgery within 24 hours prior to the study sonographic examination. Patients with a history of anaphylactic allergy to eggs or egg products, manifested by one or more of the following symptoms: generalized urticaria, difficulty in breathing, swelling of the mouth and throat, hypotension, or shock. (Subjects with nonanaphylactic allergies to eggs or egg products may be enrolled in the study, but must be watched carefully for 1 h following the administration of SONAZOID). Patients with congenital heart defects. Patients with severe emphysema, pulmonary vasculitis, or a history of pulmonary emboli. Patients with respiratory distress syndrome Patients with thrombosis within the hepatic, portal, or mesenteric veins.", "candidate_expression": "((Females) AND (NYHA Class IV) AND (anaphylactic allergy) AND (cardiac arrhythmias clinically unstable) AND (cerebral hemorrhage recent) AND (congenital heart defects) AND (congestive heart failure uncontrolled) AND (critical care unit) AND (life support) AND (respiratory distress syndrome) AND (sonographic examination) AND (surgery within 24 hours prior to the study sonographic examination) AND (thrombosis) AND (trans-jugular liver biopsy scheduled) AND (unstable occlusive disease) AND (ventricular tachycardia recurrent) AND ((known) OR (suspected)) AND ((pulmonary hypertension) OR (unstable cardiopulmonary conditions)) AND ((chemotherapy) OR (primary cancers other)) AND ((hepatic loco-regional treatment) OR (systemic loco-regional treatment)) AND ((clinical course is unpredictable) OR (medically unstable) OR (seriously ill) OR (terminally ill)) AND ((nursing) OR (pregnant)) AND ((egg products) OR (eggs)) AND ((difficulty in breathing) OR (generalized urticaria) OR (hypotension) OR (shock) OR (swelling of the mouth) OR (swelling of the throat)) AND ((emphysema severe) OR (pulmonary emboli) OR (pulmonary vasculitis)) AND ((hepatic veins) OR (mesenteric veins) OR (portal veins)) AND ((bi-directional cardiac shunts) OR (right-to-left cardiac shunts) OR (transient right-to-left cardiac shunts)))"}
{"candidate_id": "LLM01547", "doc_id": "NCT02137369_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18-60 years. Primary psychiatric diagnosis of Major Depressive Disorder, without psychotic features, confirmed via SCID-IV structured diagnostic interview. Screening Hamilton Depression Rating Scale (HAMD) = 18; and Baseline HAMD = 15. If the patient is a woman of child-bearing potential, she must agree to use an acceptable form of birth control for duration of study participation. Able to understand and provide informed consent for participation.", "candidate_expression": "((18-60 years) AND (= 15) AND (= 18) AND (Able to understand and provide informed consent for participation) AND (Baseline) AND (HAMD) AND (If the patient is a woman of child-bearing potential, she must agree to use an acceptable form of birth control for duration of study participation) AND (Major Depressive Disorder) AND (Men or women aged 18-60 years.) AND (Primary) AND (Screening Hamilton Depression Rating Scale) AND (aged) AND (psychotic features) AND (without) AND ((Men) OR (women)))"}
{"candidate_id": "LLM01548", "doc_id": "NCT02112734_exc", "case_bucket": "or", "source_criterion": "Infants who have already received postnatal vitamin D supplementation prematurity (<37 weeks)/low birthweight <2500 g poor health due to a current or past significant disease state or congenital abnormality.", "candidate_expression": "((<2500 g) AND (Infants) AND (birthweight) AND (congenital abnormality) AND (current) AND (low birthweight) AND (past) AND (poor health) AND (postnatal vitamin D supplementation) AND (prematurity) AND (significant disease state) AND (vitamin D))"}
{"candidate_id": "LLM01549", "doc_id": "NCT02231892_inc", "case_bucket": "or", "source_criterion": "Subjects must: 1. Be able to give valid informed consent 2. Be 18 55 years of age. 1. Justification: Many neural processes change with age, and these changes could introduce unwanted variability in both behavioral and MRI signals. In addition, the risk of difficult-to-detect medical abnormalities such as silent cerebral infarcts increases with age. 2. Screening tool: History. Government-issued forms of identification (e.g. driver s license, birth certificate) will be required when participant appears to be out of age range. 3. Be in good health. 1. Justification: Many illnesses may alter neural functioning as well as fMRI signals. 2. Screening tools: Medical Assessment, Medical History and Physical Examination. Medical assessments include: Vital Signs, EKG, oral HIV test, height/weight measurements, urinalysis and blood sample. Tests on the blood sample include CBC, complete metabolic profile, TSH, ESR, STS and HIV (if needed to confirm a positive salivary test for HIV). The following individual laboratory results will independently disqualify individuals: Cholesterol >250 mg/dl, Hemoglobin < 10.5 g/dl, WBC < 2400/microl, LFTs > 3Xnormal, HCG positive, Casual serum glucose > 200 mg/dl, Urine protein > 1+. The MAI will retain discretion to exclude at less extreme values, depending on the clinical presentation. (Serum glucose over 140 mg/dl will be followed up with a fasting serum glucose assessment. Those with fasting glucose below 100 mg/dl may be considered for the protocol. Others will be rejected and referred for work-up.) MAI will make the final judgment on any questionable lab results. 4. Right-handed. 1. Justification: Using right-handed individuals will reduce variability in BOLD MRI data. 2. Screening tool: Edinburgh Handedness Inventory. 5. Estimated IQ greater than or equal to 85 1. Justification: Subjects must be able to perform a cognitively challenging task to a high standard. 2. Screening tool: Wechsler Abbreviated Scale of Intelligence.", "candidate_expression": "((Be able to give valid informed consent) AND (CBC) AND (EKG) AND (ESR) AND (Edinburgh Handedness Inventory) AND (Estimated IQ greater than or equal to 85) AND (HIV) AND (History) AND (Medical Assessment) AND (Medical History) AND (Physical Examination) AND (Right-handed) AND (STS) AND (Serum glucose over 140 mg/dl) AND (TSH) AND (The MAI will retain discretion to exclude at less extreme values, depending on the clinical presentation.) AND (Vital Signs) AND (Wechsler Abbreviated Scale of Intelligence) AND (age 18 55 years) AND (blood sample) AND (complete metabolic profile) AND (fasting serum glucose assessment) AND (good health) AND (height measurement) AND (oral HIV test) AND (salivary test for HIV positive) AND (urinalysis) AND (weight measurement) AND ((Cholesterol >250 mg/dl) OR (HCG positive) OR (Hemoglobin < 10.5 g/dl) OR (LFTs > 3Xnormal) OR (Urine protein > 1+) OR (WBC < 2400/microl) OR (serum glucose > 200 mg/dl)))"}
{"candidate_id": "LLM01550", "doc_id": "NCT01850147_inc", "case_bucket": "or", "source_criterion": "Histologic or cytologic diagnosis of stage IIIB/IV NSCLC ECOG PS: 0,1 Unidimensional or bi-dimensional measurable disease Receive prior treatment including first-line platinum-based chemotherapy, standard second-line chemotherapy and 1 EGF/EGFR inhibitor Evidence of disease progression Life expectancy >12 weeks Neutrophils > 1.5 109/l, Platelets > 100 109/l, Hemoglobin > 9g/dl, Total bilirubin < 1.5 UNL, AST (SGOT) and ALT (SGPT) < 2.5 UNL, Alkaline phosphatases < 5 UNL, Creatinine < 1 UNL", "candidate_expression": "((0,1) AND (1 EGF/EGFR inhibitor) AND (< 1 UNL) AND (< 1.5 UNL) AND (< 2.5 UNL) AND (< 5 UNL) AND (> 1.5 109/l) AND (> 100 109/l) AND (> 9g/dl) AND (>12 weeks) AND (ALT (SGPT)) AND (AST (SGOT)) AND (Alkaline phosphatases) AND (Creatinine) AND (ECOG PS) AND (Evidence) AND (Evidence of disease progression) AND (Hemoglobin) AND (Histologic) AND (Life expectancy) AND (NSCLC) AND (Neutrophils) AND (Platelets) AND (Total bilirubin) AND (cytologic) AND (disease progression) AND (measurable) AND (platinum-based chemotherapy) AND (second-line chemotherapy) AND (stage IIIB/IV) AND (standard) AND (treatment))"}
```
