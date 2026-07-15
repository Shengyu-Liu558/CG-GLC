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
{"candidate_id": "LLM02951", "doc_id": "NCT02489045_exc", "case_bucket": "or", "source_criterion": "Females who are pregnant or nursing. Patients not scheduled for trans-jugular liver biopsy Patients who have received an investigational drug in the 30 days before study drug administration, or will receive one within 72 h afterwards,. Patients with known or suspected right-to-left, bi-directional, or transient right-to-left cardiac shunts Patients with pulmonary hypertension or unstable cardiopulmonary conditions Patients currently on chemotherapy or with other primary cancers requiring systemic or hepatic loco-regional treatment. Patients who are medically unstable, patients who are seriously or terminally ill, and patients whose clinical course is unpredictable. For example: Patients on life support or in a critical care unit. Patients with unstable occlusive disease (e.g., crescendo angina) Patients with clinically unstable cardiac arrhythmias, such as recurrent ventricular tachycardia. Patients with uncontrolled congestive heart failure (NYHA Class IV) Patients with recent cerebral hemorrhage. Patients who have undergone surgery within 24 hours prior to the study sonographic examination. Patients with a history of anaphylactic allergy to eggs or egg products, manifested by one or more of the following symptoms: generalized urticaria, difficulty in breathing, swelling of the mouth and throat, hypotension, or shock. (Subjects with nonanaphylactic allergies to eggs or egg products may be enrolled in the study, but must be watched carefully for 1 h following the administration of SONAZOID). Patients with congenital heart defects. Patients with severe emphysema, pulmonary vasculitis, or a history of pulmonary emboli. Patients with respiratory distress syndrome Patients with thrombosis within the hepatic, portal, or mesenteric veins.", "candidate_expression": "((Class IV) AND (Females) AND (NYHA) AND (anaphylactic allergy) AND (bi-directional cardiac shunts) AND (cardiac arrhythmias) AND (cerebral hemorrhage) AND (chemotherapy) AND (clinical course is unpredictable) AND (clinically unstable) AND (congenital heart defects) AND (congestive heart failure) AND (critical care unit) AND (currently) AND (difficulty in breathing) AND (egg products) AND (eggs) AND (emphysema) AND (generalized urticaria) AND (hepatic loco-regional treatment) AND (hepatic veins) AND (hypotension) AND (known) AND (life support) AND (medically unstable) AND (mesenteric veins) AND (not) AND (nursing) AND (other) AND (portal veins) AND (pregnant) AND (primary cancers) AND (pulmonary emboli) AND (pulmonary hypertension) AND (pulmonary vasculitis) AND (recent) AND (recurrent) AND (respiratory distress syndrome) AND (right-to-left cardiac shunts) AND (scheduled) AND (seriously ill) AND (severe) AND (shock) AND (sonographic examination) AND (surgery) AND (suspected) AND (swelling of the mouth) AND (swelling of the throat) AND (systemic loco-regional treatment) AND (terminally ill) AND (the study sonographic examination) AND (thrombosis) AND (trans-jugular liver biopsy) AND (transient right-to-left cardiac shunts) AND (uncontrolled) AND (unstable cardiopulmonary conditions) AND (unstable occlusive disease) AND (ventricular tachycardia) AND (within 24 hours prior to the study sonographic examination))"}
{"candidate_id": "LLM02952", "doc_id": "NCT01888965_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential, who are biologically able to conceive, not employing two forms of highly effective contraception or who are pregnant. Women who are breast-feeding Fertile males unwilling to use contraception Patients with brain metastases or any history of brain metastases Patients who have undergone major surgery (e.g., intra-thoracic, -abdominal, or -pelvic) </= 4 weeks prior to starting study treatment or who have not recovered from such therapy Patients with a history of pulmonary embolism, or untreated deep vein thrombosis within the past 6 months Impairment of gastrointestinal (GI) function or GI disease that may significantly alter the absorption of dovitinib The subject has had another active malignancy within the past 5 years except for cervical cancer in situ, in situ carcinoma of the bladder or non-melanoma carcinoma of the skin. Patients who have received the last administration of an anticancer therapy including chemotherapy, immunotherapy, hormonal therapy and monoclonal antibodies </= 2 weeks prior to starting the study drug, or who have not recovered from the side effects of such therapy Cirrhosis, chronic active hepatitis or chronic persistent hepatitis Patients who are currently receiving prasugrel No concurrent use of isoniazid, labetolol, trovafloxacin, tolcapone, and felbamate No concurrent use of other investigational drugs or antineoplastic therapies. Patients with impaired cardiac function or clinically significant cardiac diseases.", "candidate_expression": "((Cirrhosis) AND (Fertile) AND (Fertile males unwilling to use contraception) AND (GI disease) AND (Impairment of gastrointestinal (GI) function) AND (Women) AND (active malignancy within the past 5 years) AND (anticancer therapy </= 2 weeks prior to starting the study drug) AND (antineoplastic therapies) AND (biologically able to conceive) AND (brain metastases) AND (brain metastases history) AND (breast-feeding) AND (cardiac diseases clinically significant) AND (cervical cancer in situ) AND (chemotherapy) AND (child-bearing potential) AND (chronic active hepatitis) AND (chronic persistent hepatitis) AND (clinically significant) AND (deep vein thrombosis untreated) AND (felbamate) AND (hormonal therapy) AND (immunotherapy) AND (impaired cardiac function) AND (in situ carcinoma of the bladder) AND (intra -abdominal) AND (intra -pelvic) AND (intra-thoracic) AND (isoniazid) AND (labetolol) AND (major surgery) AND (major surgery </= 4 weeks prior to starting study treatment) AND (males) AND (monoclonal antibodies) AND (non-melanoma carcinoma of the skin) AND (other investigational drugs) AND (prasugrel) AND (pregnant) AND (pulmonary embolism) AND (recovered from such therapy) AND (recovered from the side effects of such therapy) AND (tolcapone) AND (trovafloxacin) AND (unwilling to use contraception) AND NOT (highly effective contraception two) AND NOT (recovered from such therapy))"}
{"candidate_id": "LLM02953", "doc_id": "NCT03351972_exc", "case_bucket": "other", "source_criterion": "dysphagia severe gastroparesis requiring endoscopic placement of capsule small bowel obstruction pregnancy", "candidate_expression": "((capsule) AND (dysphagia) AND (endoscopic placement requiring) AND (gastroparesis severe) AND (pregnancy) AND (small bowel obstruction))"}
{"candidate_id": "LLM02954", "doc_id": "NCT01711801_inc", "case_bucket": "or", "source_criterion": "Healthy male volunteers, 18 to 45 years of age, inclusive. Healthy status is defined by absence of evidence of any active or chronic disease following a detailed medical and surgical history, a complete physical examination including vital signs, 12-lead ECG, hematology, blood chemistry, serology and urinalysis Body mass index (BMI) 18 to 30 kg/m2 inclusive Male subjects (whether surgically sterilized or not) with female partners of child-bearing potential must use two forms of contraception, one of which must be a barrier method, for the duration of the study and for 77 days after the last dose", "candidate_expression": "((12-lead ECG) AND (Body mass index (BMI) 18 to 30 kg/m2 inclusive) AND (Healthy) AND (Male) AND (age 18 to 45 years , inclusive) AND (barrier method) AND (blood chemistry) AND (child-bearing potential) AND (female) AND (forms of contraception two for the duration of the study for 77 days after the last dose) AND (hematology) AND (male) AND (medical history) AND (physical examination) AND (serology) AND (surgical history) AND (surgically sterilized) AND (urinalysis) AND (vital signs) AND NOT (surgically sterilized) AND NOT (evidence of any active or chronic disease))"}
{"candidate_id": "LLM02955", "doc_id": "NCT03350815_inc", "case_bucket": "or", "source_criterion": "Understand and communicate with the investigator, comply with the requirements of the study and give a written, signed and dated informed consent Male or non-pregnant, non-lactating female patients at least 18 years of age Diagnosis of moderate to severe Ankylosing Spondylitis (AS) with prior documented radiologic evidence fulfilling the Modified New York criteria for AS Active AS assessed by total Bath Ankylosing Spondylitis Disease Activity index (BASDAI) = 4 (0-10) at baseline Spinal pain as measured by BASDAI question #2 = 4 cm (0-10 cm) at baseline Total back pain as measured by visual analog scale (VAS) = 40 mm (0-100 mm) at baseline Patients should have been on non-steroidal anti-inflammatory drugs (NSAIDs) at the maximum tolerated dose for at least 4 weeks prior to their Baseline Visit, with an inadequate response or for less than 4 weeks if withdrawn for intolerance, toxicity or contraindications Stable dose of NSAIDs including Cyclooxygenase-1 (COX-1) or Cyclooxygenase-2 (COX-2) inhibitors for at least 2 weeks before their Baseline Visit Patients who have been on a tumor necrosis factor alpha (TNFa) inhibitor (not more than one) must have experienced an inadequate response to previous or current treatment given at an approved dose for at least 3 months prior to baseline or had been intolerant upon administration of an anti-TNFa agent Total ankylosis of the spine Use of other investigational drugs within 5 half-lives of enrollment, or within 4 weeks before the Baseline Visit, whichever is longer. History of hypersensitivity to any of the study drugs or its excipients or to drugs of similar chemical classes. Chest x-ray, computerized tomography (CT) scan, or chest magnetic resonance imaging (MRI) with evidence of ongoing infectious or malignant process, obtained within 3 months prior to screening and evaluated by a qualified physician. Previous exposure to secukinumab or any other biologic drug directly targeting Interleukin-17 (IL-17), Interleukin-12/23 (IL-12/23), or the IL-17 receptor, or any other biologic immunomodulating agent, except those targeting TNFa Patients who have taken more than one anti-TNFa agent Any intramuscular or intravenous corticosteroid injection within 2 weeks before baseline Any therapy by intra-articular injections (e.g. corticosteroid) within 4 weeks before baseline Previous treatment with any cell-depleting therapies Patients taking high potency opioid analgesics (e.g., methadone, hydromorphone, morphine)", "candidate_expression": "((AS Active) AND (Ankylosing Spondylitis (AS)) AND (BASDAI question #2 = 4 cm at baseline) AND (Male or non-pregnant, non-lactating female patients at least 18 years of age) AND (Modified New York criteria for AS fulfilling) AND (Spinal pain) AND (Total ankylosis of the spine) AND (Total back pain) AND (Understand and communicate with the investigator, comply with the requirements of the study and give a written, signed and dated informed consent) AND (Use of other investigational drugs within 5 half-lives of enrollment, or within 4 weeks before the Baseline Visit, whichever is longer.) AND (anti-TNFa agent) AND (anti-TNFa agent more than one) AND (cell-depleting therapies Previous) AND (corticosteroid) AND (corticosteroid injection within 2 weeks before baseline) AND (excipients) AND (high potency opioid analgesics) AND (hypersensitivity) AND (inadequate response for less than 4 weeks) AND (intra-articular injections within 4 weeks before baseline) AND (non-steroidal anti-inflammatory drugs (NSAIDs) maximum tolerated dose for at least 4 weeks prior to their Baseline Visit) AND (radiologic) AND (radiologic evidence prior) AND (targeting) AND (total Bath Ankylosing Spondylitis Disease Activity index (BASDAI) = 4 at baseline) AND (treatment approved dose) AND (tumor necrosis factor alpha (TNFa) inhibitor not more than one) AND (visual analog scale (VAS) = 40 mm at baseline) AND NOT (TNFa) AND ((moderate) OR (severe)) AND ((contraindications) OR (withdrawn for intolerance) OR (withdrawn for toxicity)) AND ((Cyclooxygenase-2 (COX-2) inhibitors) OR (NSAIDs) OR (inhibitors Cyclooxygenase-1 (COX-1))) AND ((inadequate response) OR (intolerant)) AND ((current) OR (previous)) AND ((drugs of similar chemical classes) OR (study drugs)) AND ((Chest x-ray) OR (chest magnetic resonance imaging (MRI)) OR (computerized tomography (CT) scan)) AND ((infectious) OR (malignant process)) AND ((biologic drug other) OR (secukinumab)) AND ((IL-17 receptor) OR (Interleukin-12/23 (IL-12/23)) OR (Interleukin-17 (IL-17)) OR (biologic immunomodulating agent)) AND ((intramuscular) OR (intravenous)) AND ((hydromorphone) OR (methadone) OR (morphine)))"}
{"candidate_id": "LLM02956", "doc_id": "NCT00305097_exc", "case_bucket": "or", "source_criterion": "Any condition/illness that may affect the study outcomes or would make participation potentially harmful such as pregnancy or breastfeeding, diabetes mellitus, heart disease, stroke, hypertension, malabsorption syndromes, GERD, a history of ulcer, according to a detailed medical history. Abnormal hepatic function (liver function test > twice the normal range), abnormal renal function (creatinine > 1.1 mg/dl), fasting plasma glucose in the diabetic range (>/= 126 mg/dl), or blood pressure > 140/90 mmHg. Present alcoholism or drug abuse or use of medications that could interfere with the treatment including bronchodilators, quinolone antibiotics, monoamine oxidase inhibitors, anxiolytics, ranitidine, corticosteroids, growth hormone, antihypertensives.", "candidate_expression": "((> 1.1 mg/dl) AND (> 140/90 mmHg) AND (> twice the normal range) AND (>/= 126 mg/dl) AND (Abnormal) AND (abnormal) AND (bronchodilators) AND (creatinine) AND (history of) AND (in the diabetic range) AND (liver function test) AND (medical history) AND ((illness that may affect the study outcomes) OR (illness that would make participation potentially harmful)) AND ((blood pressure) OR (fasting plasma glucose) OR (hepatic function) OR (renal function)) AND ((alcoholism) OR (drug abuse) OR (medications that could interfere with the treatment)) AND ((antihypertensives) OR (anxiolytics) OR (corticosteroids) OR (growth hormone) OR (monoamine oxidase inhibitors) OR (quinolone antibiotics) OR (ranitidine)) AND ((GERD) OR (breastfeeding) OR (diabetes mellitus) OR (heart disease) OR (hypertension) OR (malabsorption syndromes) OR (pregnancy) OR (stroke) OR (ulcer)))"}
{"candidate_id": "LLM02957", "doc_id": "NCT01082549_inc", "case_bucket": "or", "source_criterion": "Eligible patients must meet the following criteria to be enrolled in the study: 1. Newly diagnosed, stage IV squamous cell lung cancer. This includes patients who present with disseminated metastases, and those with a malignant pleural or pericardial effusion (i.e., formerly stage IIIB in the 6th TNM staging system). 2. Patients who have received prior adjuvant therapy for early-stage lung cancer are eligible if at least 12 months have elapsed from that treatment. 3. Histologically confirmed squamous cell bronchogenic carcinoma. Patients whose tumors contain mixed non-small cell histologies are eligible, as long as squamous carcinoma is the predominant histology. Mixed tumors with small cell anaplastic elements are not eligible. Cytologic specimens obtained by brushings, washings, or needle aspiration of the defined lesion are acceptable. 4. Patients with previous radiotherapy as definitive therapy for locally advanced non-small cell lung cancer are eligible, as long as the recurrence is outside the original radiation therapy port. Radiation therapy must have been completed >4 weeks prior to the initiation of study treatment. Patients who have received chemo/radiation for locally advanced NSCLC are not eligible. Patients who have received palliative radiation therapy for symptomatic metastases must have completed treatment >14 days prior the initiation of the study treatment. 5. Presence of evaluable (measureable or non-measurable) disease. 6. ECOG Performance Status of 0 or 1. 7. Laboratory values as follows: Absolute neutrophil count (ANC) >1,500/microL and platelets >100,000/microL (≤72 hours prior to initial treatment). Hemoglobin >9 g/dL (Note: Patients may be transfused or receive erythropoietin to maintain or exceed this level). Bilirubin < ULN. Alanine aminotransferase (ALT) and aspartate aminotransferase (AST) ≤2.5 times the upper limit of normal if no liver involvement or ≤5 times the upper limit of normal with liver involvement. Creatinine <2.0 mg/dL, or creatinine clearance >40 mL/min (as calculated by the Cockcroft-Gault method. 8. Women of childbearing potential must have a negative serum pregnancy test performed within 7 days prior to start of treatment. Women of childbearing potential or men with partners of childbearing potential must use effective birth control measures during treatment and at least 6 months after the last dose of the study treatment. If a woman becomes pregnant or suspects she is pregnant while participating in this study, she must agree to inform her treating physician immediately. Sexually active men must agree to use a medically acceptable form of birth control during treatment and at least 6 months after the last dose. If a female partner becomes pregnant during the course of the study the treating physician should be informed immediately. 9. >18 years of age. 10. Ability to understand the nature of this study, give written informed consent, and comply with study requirements. 11. Patients entering this study must be willing to provide tissue from a previous tumor biopsy (if available) for correlative testing. An exception to this is when the national/local regulations prohibits some of the key activities of this research like the export of samples to third countries, storage of coded samples or global gene expression profiling without a pre-specified list of target genes. If tissue is not available, a patient will still be eligible for enrollment into the study.", "candidate_expression": "((0 or 1) AND (6th TNM staging system) AND (8. Women of childbearing potential must have a negative serum pregnancy test performed within 7 days prior to start of treatment. Women of childbearing potential or men with partners of childbearing potential must use effective birth control measures during treatment and at least 6 months after the last dose of the study treatment. If a woman becomes pregnant or suspects she is pregnant while participating in this study, she must agree to inform her treating physician immediately. Sexually active men must agree to use a medically acceptable form of birth control during treatment and at least 6 months after the last dose. If a female partner becomes pregnant during the course of the study the treating physician should be informed immediately.) AND (< ULN) AND (<2.0 mg/dL) AND (>1,500/microL) AND (>100,000/microL) AND (>14 days prior the initiation of the study treatment) AND (>18 years) AND (>4 weeks prior to the initiation of study treatment) AND (>40 mL/min) AND (>9 g/dL) AND (Ability to understand the nature of this study, give written informed consent, and comply with study requirements.) AND (Absolute neutrophil count (ANC)) AND (Alanine aminotransferase (ALT)) AND (Bilirubin) AND (Cockcroft-Gault method) AND (ECOG Performance Status) AND (Hemoglobin) AND (Histologically) AND (IV) AND (Mixed tumors) AND (NSCLC) AND (Newly) AND (Newly diagnosed) AND (Patients entering this study must be willing to provide tissue from a previous tumor biopsy (if available) for correlative testing. An exception to this is when the national/local regulations prohibits some of the key activities of this research like the export of samples to third countries, storage of coded samples or global gene expression profiling without a pre-specified list of target genes. If tissue is not available, a patient will still be eligible for enrollment into the study) AND (Radiation therapy) AND (adjuvant therapy) AND (age) AND (aspartate aminotransferase (AST)) AND (at least 12 months have elapsed from that treatment) AND (confirmed) AND (disseminated) AND (early-stage lung cancer) AND (initial treatment) AND (locally advanced) AND (malignant) AND (metastases) AND (mixed non-small cell histologies) AND (no) AND (non-small cell lung cancer) AND (not) AND (palliative radiation therapy) AND (platelets) AND (predominant histology) AND (previous) AND (radiotherapy) AND (small cell anaplastic elements) AND (squamous carcinoma) AND (squamous cell bronchogenic carcinoma) AND (squamous cell lung cancer) AND (stage) AND (stage IIIB) AND (stage IV) AND (symptomatic) AND (symptomatic metastases) AND (that treatment) AND (the initiation of study treatment) AND (the initiation of the study treatment) AND (treatment) AND (≤2.5 times the upper limit of normal) AND (≤5 times the upper limit of normal) AND (≤72 hours prior to initial treatment) AND ((pericardial effusion) OR (pleural effusion)) AND ((chemo) OR (radiation)) AND ((liver involvement) OR (liver involvement.)) AND ((Creatinine) OR (creatinine clearance)))"}
{"candidate_id": "LLM02958", "doc_id": "NCT03056391_exc", "case_bucket": "or", "source_criterion": "1. Patient or relatives unable or unwilling to give informed consent 2. Contraindication or allergy to paracetamol or artesunate therapy 3. Known cirrhosis, or >6 standard alcoholic drinks/day 4. Pregnancy", "candidate_expression": "((>6 standard alcoholic drinks/day) AND (Contraindication) AND (Patient or relatives unable or unwilling to give informed consent) AND (Pregnancy) AND (allergy) AND (artesunate) AND (cirrhosis) AND (paracetamol))"}
{"candidate_id": "LLM02959", "doc_id": "NCT03555526_inc", "case_bucket": "other", "source_criterion": "H pylori infection failed after at least two eradication therapies aged 20 years or greater willingness to receive rescue therapy", "candidate_expression": "((H pylori infection) AND (aged 20 years or greater) AND (eradication therapies failed at least two) AND (rescue therapy willingness))"}
{"candidate_id": "LLM02960", "doc_id": "NCT02573909_exc", "case_bucket": "or", "source_criterion": "Planned surgery under regional anesthesia contraindication to the study drug contraindication to the lumbar puncture Contraindication to oxycodone Pregnancy or lactation no informed consent", "candidate_expression": "((Contraindication) AND (Pregnancy) AND (contraindication) AND (lactation) AND (lumbar puncture) AND (oxycodone) AND (regional anesthesia) AND (study drug) AND (surgery Planned))"}
{"candidate_id": "LLM02961", "doc_id": "NCT03134196_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02962", "doc_id": "NCT03424733_exc", "case_bucket": "or", "source_criterion": "prior allergic reaction to interferon products, congestive heart failure, elevated liver enzymes", "candidate_expression": "((allergic reaction prior) AND (congestive heart failure) AND (elevated liver enzymes) AND (interferon products))"}
{"candidate_id": "LLM02963", "doc_id": "NCT03445949_inc", "case_bucket": "scope", "source_criterion": "successful left atrial appendage occlusion with Amulet device within 37 days prior to randomization. treatment with dual antiplatelet therapy (clopidogrel and acetylsalicylic acid) between left atrial appendage closure and randomization participant's age 18 years or older at the time of signing the informed consent form participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable participant is willing to sign the study informed consent form", "candidate_expression": "((18 years or older) AND (Amulet device) AND (acetylsalicylic acid) AND (age) AND (at the time of signing the informed consent form) AND (between left atrial appendage closure and randomization) AND (clopidogrel) AND (dual antiplatelet therapy) AND (left atrial appendage closure) AND (left atrial appendage occlusion) AND (participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable) AND (participant is willing to sign the study informed consent form) AND (randomization) AND (signing the informed consent form) AND (successful) AND (within 37 days prior to randomization))"}
{"candidate_id": "LLM02964", "doc_id": "NCT02526823_inc", "case_bucket": "or", "source_criterion": "Primary B-NHL, PTCL (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma were excluded) or HL patients confirmed by histopathology; Ages =18 years old, < 80 years old; ECOG (Eastern Cooperative Oncology Group)score: 0-2 At least one measurable lesion; Expected survival time=3 months; Liver function: transaminase=2.5× upper limit of normal value,bilirubin=1.5×upper limit of normal value; Renal function: serum creatinine is 44-133 mmol/L; Routine blood test:WBC=3.0×109/L,Neutrophils=1.5×109/L,Hb=100g/L,Platelet=80×109/L; LVEF=50%; New York Heart Association (NYHA) heart function classification is I-II grade signed informed consent.", "candidate_expression": "((Ages =18 years old, < 80 years old) AND (ECOG (Eastern Cooperative Oncology Group)score 0-2) AND (Expected survival time= 3 months) AND (HL) AND (Hb =100g/L) AND (LVEF =50%) AND (NYHA) AND (Neutrophils =1.5×109/L) AND (New York Heart Association heart function classification I-II grade) AND (PTCL) AND (Platelet =80×109/L) AND (Primary B-NHL) AND (bilirubin =1.5×upper limit of normal value) AND (lesion At least one) AND (serum creatinine 44-133 mmol/L) AND (signed informed consent) AND (test:WBC =3.0×109/L) AND (transaminase =2.5× upper limit of normal value) AND NOT (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma))"}
{"candidate_id": "LLM02965", "doc_id": "NCT01314898_exc", "case_bucket": "or", "source_criterion": "Subjects with a supine BP >140 mm Hg systolic or >90 mm Hg diastolic or <100 mm Hg systolic or <60 mm Hg diastolic based on the average of the triplicate Serum potassium >=5.1 mmol/L or <3.5 mmol/L at screening, confirmed by a single repeat if deemed necessary. Estimated GFR <60 mL/min/1.73 m2 using the Cockcroft-Gault formula measurement of the individual parameters following at least 5 minutes of rest at Screening.", "candidate_expression": "((<60 mL/min/1.73 m2) AND (Cockcroft-Gault formula) AND (Estimated GFR) AND (Serum potassium) AND (at screening) AND (supine BP) AND ((<100 mm Hg systolic) OR (<60 mm Hg diastolic) OR (>140 mm Hg systolic) OR (>90 mm Hg diastolic)) AND ((<3.5 mmol/L) OR (>=5.1 mmol/L)))"}
{"candidate_id": "LLM02966", "doc_id": "NCT03216967_exc", "case_bucket": "or", "source_criterion": "Known proved BKV nephropathy Hypersensitivity to everolimus, sirolimus or excipient Concomitant treatment by leflunomide, cidofovir, sirolimus, Millepertuis (Hypericum Perforatum) Pregnant or lactating women Women of child bearing potential unless they are using a birth control method", "candidate_expression": "((BKV nephropathy proved) AND (Hypericum Perforatum) AND (Hypersensitivity) AND (Millepertuis) AND (Pregnant) AND (Women) AND (child bearing potential) AND (cidofovir) AND (everolimus) AND (excipient) AND (lactating) AND (leflunomide) AND (sirolimus) AND (women) AND NOT (birth control method))"}
{"candidate_id": "LLM02967", "doc_id": "NCT02445339_inc", "case_bucket": "or", "source_criterion": "English or Spanish speaking* Emergency Department patient Aged 18-80 Have had >4 emergency department visits within 12 months for 2 consecutive 12-month periods. Period of time can be extended by up to 6 months if incarcerated or institutionalized for ≥ 6 months. Meet Diagnostic and Statistical Manual version IV (DSM-IV) criteria for alcohol dependence or & DSM-V criteria for alcohol use disorder, severe. Have ≥2 days/week of heavy drinking (>4 drinks/day) Capable of giving informed consent.", "candidate_expression": "((Aged 18-80) AND (Emergency Department) AND (alcohol dependence Diagnostic and Statistical Manual version IV (DSM-IV) criteria) AND (alcohol use disorder DSM-V criteria severe) AND (drinks/day >4) AND (emergency department visits >4 within 12 months 12-month periods) AND (heavy drinking ≥2 days/week) AND (informed consent Capable of giving) AND ((English speaking) OR (Spanish speaking)) AND ((incarcerated) OR (institutionalized)))"}
{"candidate_id": "LLM02968", "doc_id": "NCT01490034_inc", "case_bucket": "or", "source_criterion": "Weight stable (<3 kg weight change within last 3 months) Constant habitual activity patterns (no deviation > 1x/wk at 30 min/session within last 3 months) Constant habitual diet patterns within last 3 months Willingness to eat a chocolate-flavored snack at test sessions and two week training period No allergies to any test foods Not planning to change use of medications known to influence appetite or metabolism Not diabetic No history of GI pathology Non-smoker for one year or more", "candidate_expression": "((Constant habitual activity patterns) AND (Constant habitual diet patterns within last 3 months) AND (Weight stable within last 3 months <3 kg weight change) AND (Willingness to eat a chocolate-flavored snack at two week training period at test sessions) AND (medications known to influence appetite) AND (medications known to influence metabolism) AND (no deviation > 1x/wk at 30 min/session within last 3 months) AND NOT (allergies test foods) AND NOT (diabetic) AND NOT (GI pathology history) AND NOT (smoker for one year or more))"}
{"candidate_id": "LLM02969", "doc_id": "NCT02456532_inc", "case_bucket": "other", "source_criterion": "DSM-5 diagnosis of insomnia", "candidate_expression": "(insomnia DSM-5)"}
{"candidate_id": "LLM02970", "doc_id": "NCT01770340_exc", "case_bucket": "or", "source_criterion": "IIEF < 21 Operations in the past 6 months which could limit the erectile function Erectile dysfunction in the history or current medication for erectile dysfunction Current involvement in another comparable study.", "candidate_expression": "((< 21) AND (Current involvement in another comparable study.) AND (Erectile dysfunction) AND (IIEF) AND (Operations) AND (current) AND (erectile dysfunction) AND (history) AND (in the past 6 months) AND (limit the erectile function) AND (medication))"}
{"candidate_id": "LLM02971", "doc_id": "NCT00576173_exc", "case_bucket": "or", "source_criterion": "Patients who have taken either morphine with daily dose more than 120mg or Fentanyl with daily dose more than 50ug/hr Patients with significant abnormalities in hepatic or renal function which would, in the opinion of the investigator, prevent the patients involvement in the study Patients with significant clinical abnormalities in CNS, respiratory or cardiovascular function, which in the investigators judgement prevents participation in the study Patients who have taken antidepressants or anti-epileptic drugs, sedative hypnotics, selective serotonin reuptake inhibitor, short-acting analgesics, topical medications and anesthetics and/or muscle relaxants when taking Tramadol/Acetaminophen", "candidate_expression": "((daily dose more than 120mg) AND (daily dose more than 50ug/hr) AND (taking Tramadol/Acetaminophen) AND (when taking Tramadol/Acetaminophen) AND ((anesthetics) OR (anti-epileptic drugs) OR (antidepressants) OR (muscle relaxants) OR (sedative hypnotics) OR (selective serotonin reuptake inhibitor) OR (short-acting analgesics) OR (topical medications)) AND ((Acetaminophen) OR (Tramadol)) AND ((Fentanyl) OR (morphine)) AND ((abnormalities in hepatic function) OR (abnormalities in renal function)) AND ((abnormalities in CNS) OR (abnormalities in cardiovascular function) OR (abnormalities in respiratory function)))"}
{"candidate_id": "LLM02972", "doc_id": "NCT03296488_inc", "case_bucket": "or", "source_criterion": "Male or female who is among 20 to 80 years of age at screening. Scheduled to electively undergo open-laparotomy. American Society of Anesthesiology Physical Class 1-3. Ability and willingness to provide informed consent", "candidate_expression": "((Ability and willingness to provide informed consent) AND (American Society of Anesthesiology Physical Class 1-3) AND (age 20 to 80 years at screening) AND (open-laparotomy Scheduled electively) AND ((Male) OR (female)))"}
{"candidate_id": "LLM02973", "doc_id": "NCT02992938_inc", "case_bucket": "other", "source_criterion": "Patients scheduled for thyroidectomy with general anesthesia in the University of Chile Clinical Hospital", "candidate_expression": "((University of Chile Clinical Hospita) AND (general anesthesia) AND (thyroidectomy scheduled for))"}
{"candidate_id": "LLM02974", "doc_id": "NCT02958566_inc", "case_bucket": "or", "source_criterion": "Males or females above the age of 18 Patients undergoing laparoscopic or robotic colorectal resections", "candidate_expression": "((age above the age of 18) AND (colorectal resections) AND ((Males) OR (females)) AND ((laparoscopic) OR (robotic)))"}
{"candidate_id": "LLM02975", "doc_id": "NCT03337503_inc", "case_bucket": "or", "source_criterion": "Written informed consent Adult patients (older than 18 years of age), male and female, with chronic non-cancer and cancer pain (at least 3 months in duration) Patients experiencing an average weekly pain intensity score greater than 4 on a 11 points NRS Subject agreed to follow the protocol Naïve cannabis patients with chronic non-cancer and cancer pain (not used cannabis in any presentation in the last 12 weeks) Patients receiving opioids and other concomitant pain medications should have a stable dose for the last 15 days. Normal cognitive status according to MiniCog Normal liver function (defined as aspartate aminotransferase 10-40 U/L and alanine aminotransferase 7-56 U/L) Normal renal function (defined as serum creatinine level <133 µmol/L and Estimated Glomerular Filtration Rate (eGFR) greater than or equal to 60) Negative result on ßhuman chorionic gonadotropin pregnancy test (if applicable) Ability to read and respond to questions in French or English. A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.", "candidate_expression": "((10-40 U/L) AND (7-56 U/L) AND (<133 µmol/L) AND (A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.) AND (Adult) AND (Estimated Glomerular Filtration Rate (eGFR)) AND (MiniCog) AND (Naïve cannabis) AND (Negative) AND (Normal cognitive status) AND (Normal liver function) AND (Normal renal function) AND (Subject agreed to follow the protocol) AND (Written informed consent) AND (age) AND (alanine aminotransferase) AND (aspartate aminotransferase) AND (at least 3 months in duration) AND (average weekly pain intensity score on a 11 points NRS) AND (cancer) AND (cannabis) AND (chronic) AND (female) AND (for the last 15 days) AND (greater than 4) AND (greater than or equal to 60) AND (in the last 12 weeks) AND (male) AND (non-cancer) AND (not) AND (older than 18 years) AND (opioids) AND (other) AND (pain) AND (pain medications) AND (serum creatinine level) AND (stable dose) AND (ßhuman chorionic gonadotropin pregnancy test))"}
```
