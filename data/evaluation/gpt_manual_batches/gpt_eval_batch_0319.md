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
{"candidate_id": "LLM07951", "doc_id": "NCT00931983_exc", "case_bucket": "other", "source_criterion": "Other neuromuscular disease Contraindication to weight bearing on lower extremities Pressure sores where harness would be applied Uncontrollable hypotension when upright Lower limb contractures impeding range of motion necessary for ambulation Prior enrolment in a BWATT program Unable to commit to intervention for duration of protocol", "candidate_expression": "((Contraindication weight bearing on lower extremities) AND (Lower limb contractures range of motion necessary for ambulation) AND (Pressure sores) AND (Unable to commit to intervention for duration of protocol) AND (harness) AND (hypotension Uncontrollable when upright) AND (neuromuscular disease))"}
{"candidate_id": "LLM07952", "doc_id": "NCT03256864_exc", "case_bucket": "or", "source_criterion": "Patients who are recipients of multiple solid organ or islet cell tissue transplants, or have previously received an organ or tissue transplant. Patients who have a combined liver-kidney transplant. History of malignancy of any organ system (other than localized basal cell carcinoma of the skin), treated or untreated, within the past 5 years, regardless of whether there is evidence of local recurrence or metastases. Existence of any surgical, medical or mental conditions, other than the current transplantation, which, in the opinion of the investigator, might interfere with the objectives of the study. Pregnant or nursing (lactating) women.", "candidate_expression": "((Pregnant) AND (combined liver-kidney transplant) AND (islet cell tissue transplants) AND (lactating) AND (malignancy History any organ system within the past 5 years) AND (medical conditions) AND (mental conditions) AND (nursing) AND (organ transplant) AND (solid organ transplants) AND (surgical conditions) AND (tissue transplant) AND (women) AND NOT (localized basal cell carcinoma of the skin treated untreated) AND NOT (transplantation current))"}
{"candidate_id": "LLM07953", "doc_id": "NCT02350439_inc", "case_bucket": "scope", "source_criterion": "1. Age 18-80 years 2. Patients with at least 1 ≥50% stenosis in a coronary vessel, subjected to FFR assessment, who exhibit variation in Pd / Pa ratio ≥ 0.05 (e.g. difference of max Pd/Pa minus min Pd/Pa) during steady state hyperaemia (determined by visual assessment). 3. Written informed consent", "candidate_expression": "((Age 18-80 years) AND (FFR assessment) AND (Pd / Pa ratio ≥ 0.05) AND (hyperaemia steady state) AND (max Pd/Pa) AND (min Pd/Pa) AND (stenosis in a coronary vessel at least 1 ≥50%) AND (variation in Pd / Pa ratio) AND (visual assessment))"}
{"candidate_id": "LLM07954", "doc_id": "NCT01742117_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07955", "doc_id": "NCT03397914_inc", "case_bucket": "or", "source_criterion": "Age between one year and 18 years Sepsis due to MDR or minimally susceptible gram-negative bacteria History of MDR gram-negative infection or sepsis due to organisms sensitive to colistin. Culture result consistent with MDR gram negative for this febrile neutropenic episode. Patient in sepsis and colistin was administered empirically to increase antibiotic coverage.", "candidate_expression": "((Age) AND (MDR) AND (Sepsis) AND (administered empirically) AND (between one year and 18 years) AND (colistin) AND (gram negative) AND (gram-negative infection) AND (minimally susceptible gram-negative bacteria) AND (organisms) AND (sensitive to colistin) AND (sepsis))"}
{"candidate_id": "LLM07956", "doc_id": "NCT00356148_exc", "case_bucket": "or", "source_criterion": "Ductal carcinoma in situ (DCIS; stage 0 cancer), Advanced or distant metastatic stage, Receiving any neoadjuvant therapy, History of receiving any antibiotics within prior 3 months, History of immunodeficiency, Having a remote infection, History of reaction to study antibiotics, Denial of signing the consent form.", "candidate_expression": "((0) AND (Advanced metastatic) AND (DCIS) AND (Denial of) AND (Ductal carcinoma in situ) AND (History) AND (antibiotics) AND (cancer) AND (distant metastatic) AND (immunodeficiency) AND (neoadjuvant therapy) AND (reaction) AND (remote infection) AND (signing the consent form) AND (stage) AND (study antibiotics) AND (within prior 3 months))"}
{"candidate_id": "LLM07957", "doc_id": "NCT03088904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07958", "doc_id": "NCT01994382_exc", "case_bucket": "or", "source_criterion": "Richter's syndrome, Burkitt's lymphoma, or Burkitt-like Lymphoma (transformed DLBCL from Follicular NHL are eligible). Prior transplant with stem cell infusion 90 days or active graft-versus-host treatment within 8 weeks of Day 1. Prior therapy with SYK inhibitors. Chronic treatment with strong CYP3A4 inhibitor/ inducer, acid reducing agent, Proton pump inhibitors Known lymphomatous involvement of the CNS. Persistent, unresolved NCI CTCAE v4.0 ≥ Grade 2, previous drug-related toxicity (except alopecia, erectile impotence, hot flashes, libido, neuropathy). Prior monoclonal antibody, radioimmunoconjugate, antibody drug conjugate, phototherapy, radiotherapy, chemotherapy, immunotherapy, immunosuppressive therapy, or any test agent within 3 weeks or for alemtuzumab 8 weeks of Day 1. For CTCL: (TSEBT) within 12 weeks, or initiation of topical steroid, nitrogen mustard, or topical retinoid within 2 weeks. (Stable topical ≥ 4 weeks prior to Day 1 allowed). Known carrier or infection for HIV/Hep B or C. HCV ab+ must be PCR-. HBV ab+ must be HBsAg- or undetectable DNA Active infection requiring systemic treatment, Significant GI disease, previous major gastric/bowel surgery, difficulty swallowing or malabsorption syndrome. Major surgery within 4 weeks Previous malignancies within 2 yrs. unless relapse risk is small (< 5%). Current use of systemic steroids >20 mg QD prednisone (or equivalent) Breastfeeding or pregnant (intention to become) females or participation in other clinical trials", "candidate_expression": "((8 weeks of Day 1) AND (90 days of Day 1) AND (>20 mg QD) AND (CTCL) AND (Day 1) AND (GI disease) AND (HBsAg-) AND (Major) AND (NCI CTCAE v4.0) AND (PCR-) AND (Prior) AND (SYK inhibitors) AND (Significant) AND (TSEBT) AND (active) AND (antibody drug conjugate) AND (chemotherapy) AND (drug-related toxicity) AND (except) AND (females) AND (immunosuppressive therapy) AND (immunotherapy) AND (infection) AND (initiation) AND (lymphomatous involvement of the CNS) AND (major) AND (malignancies) AND (monoclonal antibody) AND (phototherapy) AND (prednisone) AND (previous) AND (radioimmunoconjugate) AND (radiotherapy) AND (requiring systemic treatment) AND (stem cell infusion) AND (surgery) AND (systemic steroids) AND (systemic treatment) AND (therapy) AND (undetectable DNA) AND (unless relapse risk is small (< 5%)) AND (within 12 weeks) AND (within 2 weeks) AND (within 2 yrs.) AND (within 4 weeks) AND (within 8 weeks of Day 1) AND (≥ 4 weeks prior to Day 1) AND (≥ Grade 2) AND ((graft-versus-host treatment) OR (transplant)) AND ((Proton pump inhibitors) OR (acid reducing agent) OR (strong CYP3A4 inducer) OR (strong CYP3A4 inhibitor)) AND ((Burkitt's lymphoma) OR (Burkitt-like Lymphoma) OR (DLBCL) OR (Follicular NHL) OR (Richter's syndrome)) AND ((alopecia) OR (erectile impotence) OR (hot flashes) OR (libido) OR (neuropathy)) AND ((alemtuzumab) OR (within 3 weeks of Day 1)) AND ((nitrogen mustard) OR (topical retinoid) OR (topical steroid)) AND ((Hep B infection for) OR (Hep C infection for) OR (infection for HIV)) AND ((HBV ab+) OR (HCV ab+)) AND ((bowel surgery) OR (gastric surgery)) AND ((difficulty swallowing) OR (malabsorption syndrome)) AND ((Breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM07959", "doc_id": "NCT01491763_inc", "case_bucket": "or", "source_criterion": "Patients with Ph (BCR/ABL) positive de novo < 55 years old (it is advisable to include patients over 55 years LAL07OPH protocol). Performance status 0-2 (Appendix B) may include patients with performance status > 2 attributable to LAL. Patients without functional impairment of organs: liver function: total bilirubin, AST, ALT, alfa-GT and alkaline phosphatase less than 3 times the upper limit of normal laboratory renal function: serum creatinine < 2 mg/dL or clearance creatinine > 30 ml/min (except renal function attributable to LAL) cardiac function (Appendix B) normal: ventricular EF > 50%, absence of severe chronic respiratory disease. In the event that alterations are secondary to the disease is at the discretion of the investigator to determine if the patient can be included in the trial.", "candidate_expression": "((ALT) AND (AST) AND (Performance status 0-2) AND (Ph (BCR/ABL) positive de novo) AND (alfa-GT) AND (alkaline phosphatase) AND (cardiac function normal) AND (old < 55 years) AND (total bilirubin) AND (ventricular EF > 50%) AND NOT (functional impairment of organs) AND NOT (severe chronic respiratory disease) AND ((clearance creatinine > 30 ml/min) OR (serum creatinine < 2 mg/dL)))"}
{"candidate_id": "LLM07960", "doc_id": "NCT03126214_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension (defined as average SBP = 160 mmHg [2 readings taken at time of screening]). End stage renal disease (CrCl < 15 ml/min) Valvular Heart Disease including those with prosthetic valve, mitral stenosis (moderate to severe) or valve repair. Excess alcohol intake (males: = 28 units/week, females: = 21 units/week. One unit of alcohol = 8 oz beer, 1 oz hard liquor or 4 oz wine). Intracranial bleed at any point. History of \"Major Bleeding\" at any point (defined as overt bleeding at a critical site including intracranial, intraspinal, intraocular, pericardial, or retroperitoneal; or bleed requiring hospitalization). Foreshortened life-expectancy or severe comorbidities precluding study follow-up period Unable to read/understand English Severe cognitive impairment (defined as score = 5 on the Short Portable Mental Status Questionnaire)", "candidate_expression": "((CrCl < 15 ml/min) AND (End stage renal disease) AND (Intracranial bleed at any point) AND (Major Bleeding History at any point) AND (Short Portable Mental Status Questionnaire = 5) AND (Valvular Heart Disease) AND (alcohol intake Excess) AND (average SBP = 160 mmHg 2 readings at time of screening) AND (bleed intraocular pericardial retroperitoneal) AND (cognitive impairment Severe) AND (females = 21 units/week) AND (hospitalization) AND (hypertension Uncontrolled) AND (life-expectancy Foreshortened) AND (males = 28 units/week) AND (mitral stenosis moderate severe) AND (overt bleeding critical site intracranial intraspinal) AND (prosthetic valve) AND (severe comorbidities) AND (valve repair))"}
{"candidate_id": "LLM07961", "doc_id": "NCT02203019_inc", "case_bucket": "or", "source_criterion": "Men and women 18-89 years old with the diagnosis of sepsis (as specified below) within the previous 24 hours who require mechanical ventilation, and provide informed consent either personally or by an authorized representative.", "candidate_expression": "((Men) AND (mechanical ventilation) AND (old 18-89 years) AND (provide informed consent either personally or by an authorized representative) AND (sepsis within the previous 24 hours) AND (women))"}
{"candidate_id": "LLM07962", "doc_id": "NCT02167022_exc", "case_bucket": "other", "source_criterion": "1. Diagnosis: Diagnosis of CP secondary to neuronal migration. 2. Co-morbidities: Medical conditions that may prevent the administration of rehabilitation therapies at the intensity required by the study, or that may compromise the study ability to maintain blindness, or that have a co-morbidity not typically associated with CP (i.e. cancer, cystic fibrosis). 3. Co-interventions: Anticipated pharmacological intervention or procedure or participation in other studies that may interfere with this study.", "candidate_expression": "((CP secondary to neuronal migration) AND (Co-interventions: Anticipated pharmacological intervention or procedure or participation in other studies that may interfere with this study.))"}
{"candidate_id": "LLM07963", "doc_id": "NCT02905734_inc", "case_bucket": "other", "source_criterion": "Arrestees examined by a physician during detention in police cells aged 18 or older smoking at least 10 cigarettes per day giving written consent to participate in the study health status compatible with detention in police cells", "candidate_expression": "((Arrestees) AND (aged 18 or older) AND (examined by a physician during detention in police cells) AND (giving written consent to participate in the study) AND (health status compatible with detention in police cells) AND (smoking at least 10 cigarettes per day))"}
{"candidate_id": "LLM07964", "doc_id": "NCT02893293_exc", "case_bucket": "or", "source_criterion": "Contraindications for magnetic resonance imaging Hemosiderosis/hemochromatosis ( patients can still be included in the non-ferumoxytol arm)", "candidate_expression": "((Contraindications) AND (magnetic resonance imaging) AND ((Hemosiderosis) OR (hemochromatosis)))"}
{"candidate_id": "LLM07965", "doc_id": "NCT02277067_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((Women) AND (after 37 weeks) AND (cesarean section) AND (gestation) AND (singleton pregnancy))"}
{"candidate_id": "LLM07966", "doc_id": "NCT03134378_inc", "case_bucket": "or", "source_criterion": "18 years or older patients who are proven to be infected by Helicobacter pylori based on positive in Urea Breath Test or positive in histopathologic examination of biopsy in antrum and corpus of gaster through esophagoduodenoscopy.", "candidate_expression": "((18 years or older) AND (antrum of gaster) AND (corpus of gaster) AND (histopathologic examination of biopsy) AND (infected by Helicobacter pylori) AND (old) AND (positive) AND ((Urea Breath Test) OR (esophagoduodenoscopy)))"}
{"candidate_id": "LLM07967", "doc_id": "NCT03351608_exc", "case_bucket": "or", "source_criterion": "Has any clinically significant condition or situation (eg, anatomical malformation that complicates intubation) other than the condition being studied that, in the opinion of the investigator, would interfere with the trial evaluations or optimal participation in the trial. Has a neuromuscular disorder that may affect NMB and/or trial assessments. Is dialysis-dependent or has (or is suspected of having) severe renal insufficiency (defined as estimated glomerular filtration rate (eGFR) <30 ml/min). Has or is suspected of having a family or personal history of malignant hyperthermia. Has or is suspected of having an allergy to study treatments or its/their excipients, to opioids/opiates, muscle relaxants or their excipients, or other medication(s) used during general anesthesia. Has received or is planned to receive toremifene and/or fusidic acid via IV administration within 24 hours before or within 24 hours after administration of study treatment. Has been previously treated with sugammadex or has participated in a sugammadex clinical trial. Is currently participating in or has participated in an interventional clinical trial with an investigational compound or device within 30 days of signing the informed consent/assent for this current trial.", "candidate_expression": "((<30 ml/min) AND (IV administration) AND (administration of study treatment) AND (affect NMB) AND (affect trial assessments) AND (allergy) AND (anatomical malformation) AND (clinically significant) AND (condition) AND (currently participating in an interventional clinical trial) AND (device) AND (dialysis-dependent) AND (during general anesthesia) AND (estimated glomerular filtration rate (eGFR)) AND (excipients) AND (family) AND (fusidic acid) AND (general anesthesia) AND (has participated in an interventional clinical trial) AND (interfere with optimal participation) AND (interfere with the trial evaluations) AND (investigational compound) AND (malignant hyperthermia) AND (medication) AND (muscle relaxants) AND (neuromuscular disorder) AND (opiates) AND (opioids) AND (other) AND (other than) AND (participated in clinical trial) AND (personal history) AND (planned to) AND (previously) AND (severe renal insufficiency) AND (signing the informed assent) AND (signing the informed consent) AND (situation) AND (study treatments) AND (sugammadex) AND (the condition being studied) AND (toremifene) AND (within 24 hours after administration of study treatment) AND (within 24 hours before administration of study treatment) AND (within 30 days of signing the informed assent) AND (within 30 days of signing the informed consent))"}
{"candidate_id": "LLM07968", "doc_id": "NCT02077556_exc", "case_bucket": "or", "source_criterion": "Pregnancy Tuberculosis Hepatitis B or C carrier status Human immunodeficiency virus-positive status Retransplantation or multiorgan transplantation History of rheumatoid arthritis Use of drugs that might have enhanced or inhibited CYP3A4 or P-gp activity", "candidate_expression": "((Human immunodeficiency virus) AND (Pregnancy) AND (Tuberculosis) AND (multiorgan) AND (positive) AND (rheumatoid arthritis) AND ((Hepatitis B carrier) OR (Hepatitis C carrier)) AND ((Retransplantation) OR (transplantation)))"}
{"candidate_id": "LLM07969", "doc_id": "NCT03541980_exc", "case_bucket": "or", "source_criterion": "Patient with fever (38C or 100.4F) Patient less than age 4 years Patient greater than age 16 years Patient with hypersensitivity/allergy to either morphine, NSAIDs, or acetaminophen Patient received acetaminophen within the past 4 hours Patient with known liver disease or renal disease Patient not requiring IV morphine (pain score 5/10 or less) Patient enrolled in the study within the past 72 hours", "candidate_expression": "((IV morphine requiring) AND (acetaminophen within the past 4 hours) AND (age greater than 16 years) AND (age less than 4 years) AND (enrolled in the study within the past 72 hours) AND (fever) AND (pain score 5/10 or less) AND ((allergy) OR (hypersensitivity)) AND ((NSAIDs) OR (acetaminophen) OR (morphine)) AND ((liver disease) OR (renal disease)) AND ((100.4F) OR (38C)))"}
{"candidate_id": "LLM07970", "doc_id": "NCT03372304_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07971", "doc_id": "NCT02764476_inc", "case_bucket": "or", "source_criterion": "Adults 18-65 years, who are diagnosed with functional neurologic symptom or conversion disorder. If diagnosis of seizure type then video EEG with diagnosis confirmed by board-certified neurologist with subspecialty training in epilepsy and clinical neurophysiology using the criteria of the International Classification of the Epilepsies is required. If diagnosis of motor type, documented and clinically established levels of diagnostic certainty (Williams,1995) confirmed by 2 neurologists is required. Participants must have at least one symptom per month in the month prior to enrollment Fluency in English spoken language", "candidate_expression": "((18-65 years 18-65 years) AND (Adults) AND (criteria of the International Classification of the Epilepsies) AND (motor type) AND (seizure type) AND (symptom at least one per month in the month prior to enrollment) AND (video EEG) AND ((conversion disorder) OR (functional neurologic symptom)))"}
{"candidate_id": "LLM07972", "doc_id": "NCT02743598_inc", "case_bucket": "other", "source_criterion": "HIV controlled on therapy for at least 12 weeks Viral load < 200 copies BMI >27 to 45 Diagnosis of DM type 2 with A1-C >7 to 15 Participants must be willing to comply with all study related procedures", "candidate_expression": "((< 200 copies) AND (>27 to 45) AND (>7 to 15) AND (A1-C) AND (BMI) AND (DM type 2) AND (HIV) AND (Participants must be willing to comply with all study related procedures) AND (Viral load) AND (at least 12 weeks) AND (controlled))"}
{"candidate_id": "LLM07973", "doc_id": "NCT03080493_exc", "case_bucket": "or", "source_criterion": "Current use of gabapentin or pregabalin Allergy to gabapentin, acetaminophen, codeine, or ibuprofen Self reported renal disease (severe impaired renal function) Self reported current or chronic narcotic use (typical daily use) Women with any issue that, in the opinion of the investigator, would interfere with study participation or generating accurate study data", "candidate_expression": "((Allergy) AND (acetaminophen) AND (codeine) AND (gabapentin) AND (ibuprofen) AND (impaired renal function severe current) AND (narcotic use Self reported daily use chronic) AND (pregabalin) AND (renal disease Self reported))"}
{"candidate_id": "LLM07974", "doc_id": "NCT02003339_exc", "case_bucket": "or", "source_criterion": "Invasive hepatocellular carcinoma without any isolated tumor Disease needing 2 injections of Therasphere Thrombosis extending into the porta(thrombosis of one of left or right branch authorized), extra hepatic metastasis Previous treatment by chemoembolization, radiofrequency less than 3 months before radioembolization No antiangiogenic concomitant treatment, 15 days before and 15 days after radioembolization, including Sorafenib Associated disease which could prevent patient from receiving treatment RMI contre-indication(particle or metal prosthesis, pacemaker, claustrophobia) or contrast product contre-indication (allergy) Patient already participating in an other therapeutic trial with an experimental drug Pregnant or childbearing potential women or breastfeeding women minors, persons deprived of liberty or protected adults (maintenance of justice, guardianship or supervision) Unable to comply with trial medical follow-up for geographical, social or psychological reasons Unable to sign an informed consent", "candidate_expression": "((15 days after radioembolization) AND (15 days before radioembolization) AND (Associated disease) AND (Invasive) AND (No) AND (RMI) AND (RMI contre-indication) AND (Sorafenib) AND (Unable to sign an informed consent) AND (antiangiogenic treatment) AND (authorized) AND (could prevent patient from receiving treatment) AND (extending into the porta) AND (extra hepatic metastasis) AND (hepatocellular carcinoma) AND (isolated tumor) AND (less than 3 months before radioembolization) AND (minors) AND (radioembolization) AND (without) AND (women) AND ((chemoembolization) OR (radiofrequency)) AND ((Pregnant) OR (breastfeeding) OR (childbearing potential)) AND ((Thrombosis) OR (thrombosis)) AND ((left branch) OR (right branch)))"}
{"candidate_id": "LLM07975", "doc_id": "NCT02337764_exc", "case_bucket": "or", "source_criterion": "The participant has Modified Hoehn & Yahr stage 5 (or stage 5 at eather on-time or off-time for the participant with wearing off phenomenon). The participant has severe dyskinesia. The participant has unstable systemic disease. The participant has a Mini-Mental State Examinations (MMSE) score of <= 24. psychiatric disease. The participant has a history of clinically significant hypertension or other reactions associated with ingestion of tyramine-rich food. The participant has received neurosurgical intervention for Parkinson's disease (e.g., pallidotomy, thalamotomy, deep brain stimulation). The participant has received transcranial magnetic stimulation within 6 months.The participant has received selegiline, pethidine, tramadol, reserpine or methyldopa within 90 days. The participant has received levodopa monotherapy, any psychoneurotic agent or antiemetic medication of dopamine agonist within 14 days. However, the participant has been receiving quetiapine or domperidone with a stable dose regimen for >= 14 days may be included in the study. The participant is required to take any of the excluded medications or treatments. The participant with laboratory data meeting any of the following: Creatinine >= 2 x upper limit of normal (ULN) Total bilirubin >= 2 x ULN ALT or AST >= 1.5 x ULN ALP >= 3 x ULN The participant has received any of the excluded medications or treatments during.", "candidate_expression": "((ALP >= 3 x ULN) AND (ALT) AND (AST) AND (Creatinine >= 2 x upper limit of normal (ULN)) AND (Mini-Mental State Examinations (MMSE) <= 24) AND (Modified Hoehn & Yahr stage 5 at on-time at off-time) AND (Parkinson's disease) AND (The participant has received any of the excluded medications or treatments during.) AND (The participant is required to take any of the excluded medications or treatments.) AND (Total bilirubin >= 2 x ULN) AND (antiemetic medication of dopamine agonist) AND (clinically significant) AND (deep brain stimulation) AND (domperidone) AND (dyskinesia severe) AND (hypertension clinically significant) AND (levodopa) AND (levodopa monotherapy) AND (methyldopa) AND (neurosurgical intervention) AND (pallidotomy) AND (pethidine) AND (psychiatric disease) AND (psychoneurotic agent) AND (quetiapine) AND (reactions associated with ingestion of tyramine-rich food) AND (reserpine) AND (selegiline) AND (systemic disease unstable) AND (thalamotomy) AND (tramadol) AND (transcranial magnetic stimulation within 6 months) AND (unstable) AND (wearing off phenomenon stage 5))"}
```
