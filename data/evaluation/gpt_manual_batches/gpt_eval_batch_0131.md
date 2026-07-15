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
{"candidate_id": "LLM03251", "doc_id": "NCT00625742_exc", "case_bucket": "or", "source_criterion": "1. Have dementia or delirium (as determined by the palliative care specialist) at study entry. 2. Are pregnant 3. Have been taking corticosteroids for longer than 48 hours. 4. Have pulmonary edema, ascites or pitting edema on clinical examination. 5. Are unable to walk. 6. Have a history of serious adverse gastrointestinal events (i.e., bleeding or perforation),history of a coagulopathy or current anti-coagulant use. 7. Have an ALT/AST>3x upper limit of normal. 8. Patients on methotrexate. 9. Patients taking melatonin receptor agonists (such as Rozerem® [ramelteon]).", "candidate_expression": "((>3x upper limit of normal) AND (ALT/AST) AND (Rozerem) AND (at study entry) AND (corticosteroids) AND (current) AND (history) AND (longer than 48 hours) AND (melatonin receptor agonists) AND (methotrexate) AND (pregnant) AND (ramelteon) AND (serious) AND (unable to walk) AND ((adverse gastrointestinal events) OR (anti-coagulant) OR (coagulopathy)) AND ((bleeding) OR (perforation)) AND ((delirium) OR (dementia)) AND ((ascites) OR (pitting edema) OR (pulmonary edema)))"}
{"candidate_id": "LLM03252", "doc_id": "NCT02369211_exc", "case_bucket": "or", "source_criterion": "Chronic opiate use Liver disease (known history of hepatitis B or C, cirrhosis, nonalcoholic steatohepatitis, history of alcoholism, ALT/AST greater than 3 times upper limit of normal in the past 3 months) Allergy/hypersensitivity to acetaminophen Patients with baseline dementia Chronic diathesis Chronic kidney disease", "candidate_expression": "((Liver disease) AND (acetaminophen) AND (dementia baseline) AND (diathesis Chronic) AND (kidney disease Chronic) AND (opiate Chronic) AND ((ALT/AST greater than 3 times upper limit of normal in the past 3 months) OR (alcoholism history) OR (cirrhosis) OR (nonalcoholic steatohepatitis)) AND ((Allergy) OR (hypersensitivity)) AND ((hepatitis B) OR (hepatitis C)))"}
{"candidate_id": "LLM03253", "doc_id": "NCT03536520_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((Allergy) AND (active) AND (other) AND (regular) AND (relevant for) AND (tolerance) AND (treatment) AND ((altitude exposure) OR (hypoxia)) AND ((acetazolamide) OR (sulfonamides)) AND ((cardiovascular disease) OR (disease) OR (respiratory disease)))"}
{"candidate_id": "LLM03254", "doc_id": "NCT03034837_inc", "case_bucket": "other", "source_criterion": "generally healthy grade 1-2 school children with written parental consent with at least 1 sound and fully erupted permanent first molar", "candidate_expression": "((children) AND (generally healthy) AND (grade 1-2 school) AND (permanent first molar at least 1 sound fully erupted) AND (with written parental consent))"}
{"candidate_id": "LLM03255", "doc_id": "NCT03134378_exc", "case_bucket": "or", "source_criterion": "Patients refuse to follow the research Patient has had previous eradication therapy of Helicobacter pylori infection. The patient is pregnant or breastfeeding Patients have a history of allergy to one component of triple therapy regimen (proton pump inhibitor, penicillin, and / or macrolide) before. Patients are known to have impaired liver function, evidenced by ALT values within normal limits, and no previous liver disease. Patients were found to have arrhythmias or obtained QT wave elongation on electrocardiographic", "candidate_expression": "((ALT values within normal limits) AND (Helicobacter pylori infection) AND (QT wave elongation) AND (allergy history) AND (arrhythmias) AND (breastfeeding) AND (component of triple therapy regimen) AND (electrocardiographic) AND (eradication therapy previous) AND (liver function impaired) AND (macrolide) AND (penicillin) AND (pregnant) AND (proton pump inhibitor) AND (refuse to follow the research) AND NOT (liver disease previous))"}
{"candidate_id": "LLM03256", "doc_id": "NCT03317197_exc", "case_bucket": "or", "source_criterion": "Pregnant women and young children aged <18 years; Patients with underlying disease cases without the possibility of resuscitation (e.g., terminal cancer); Patients with do-not-resuscitate (DNR) status; Death by excessive bleeding (e.g., abdominal main artery rupture); Patients who have experienced in-hospital CA; Patients previously treated with steroid, anti-cancer medicine, or immunosuppression treatment before CA; Patients already been registered with other studies; or Patients from whom informed consent cannot be obtained", "candidate_expression": "((<18 years) AND (CA) AND (Death by excessive bleeding) AND (Patients already been registered with other studies; or) AND (Patients from whom informed consent cannot be obtained) AND (abdominal) AND (aged) AND (before CA) AND (do-not-resuscitate (DNR) status) AND (hospital) AND (in-hospital) AND (main artery rupture) AND (previously) AND (terminal cancer) AND (underlying disease) AND (without the possibility of resuscitation) AND (women) AND (young children) AND ((anti-cancer medicine) OR (steroid)) AND ((immunosuppression treatment) OR (treated)))"}
{"candidate_id": "LLM03257", "doc_id": "NCT03648021_inc", "case_bucket": "or", "source_criterion": "18-year or older patients Patient hospitalized in neuro-critical care for: Arachnoid hemorrhage Intra parenchymatous hematoma stroke Acute brain Severe injury Post-operative complication of an act of neurosurgery or programmed neuroradiology Sedation and mechanical ventilation planned > 2 days Monitoring of intracranial temperature and pressure by intraparenchymal sensor (Sophysa®) Brain temperature > 38.5°C for more than 30 minutes", "candidate_expression": "((18-year or older) AND (> 2 days) AND (> 38.5°C) AND (Acute brain Severe injury) AND (Arachnoid hemorrhage) AND (Brain temperature) AND (Intra parenchymatous) AND (Post-operative complication) AND (Sedation) AND (Sophysa®) AND (for more than 30 minutes) AND (hematoma) AND (hospitalized) AND (intraparenchymal sensor) AND (mechanical ventilation) AND (neuro-critical care) AND (neuroradiology) AND (neurosurgery) AND (old) AND (planned) AND (stroke) AND ((of an act of neurosurgery) OR (of an act of programmed neuroradiology)) AND ((intracranial pressure) OR (intracranial temperature)))"}
{"candidate_id": "LLM03258", "doc_id": "NCT03118232_inc", "case_bucket": "or", "source_criterion": "Nursing homes will be eligible to participate if they meet the following criteria: Licensed nursing home in Orange County or Southern Los Angeles County serving adults Minimal use of chlorhexidine bathing* Minimal use of nasal decolonization* *Minimal use defined as <15% of residents receiving at least one chlorhexidine bath or nasal decolonization treatment during their nursing home stay.", "candidate_expression": "((<15%) AND (Licensed nursing home) AND (Minimal use) AND (Nursing homes) AND (Orange County) AND (Southern Los Angeles County) AND (at least one) AND (chlorhexidine) AND (chlorhexidine bath) AND (chlorhexidine bathing) AND (during their nursing home stay) AND (nasal decolonization) AND (nasal decolonization treatment) AND (residents receiving at least one chlorhexidine bath) AND (serving adults))"}
{"candidate_id": "LLM03259", "doc_id": "NCT02785549_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03260", "doc_id": "NCT03560310_inc", "case_bucket": "or", "source_criterion": "Written informed consent Age =18 years Has undergone first time isolated CABG due to an episode of acute coronary syndrome (STEMI, NSTEMI, unstable angina) within 6 weeks before surgery", "candidate_expression": "((Age =18 years) AND (NSTEMI) AND (STEMI) AND (Written informed consent) AND (acute coronary syndrome) AND (isolated CABG first time) AND (unstable angina within 6 weeks before surgery))"}
{"candidate_id": "LLM03261", "doc_id": "NCT01793831_inc", "case_bucket": "or", "source_criterion": "Moderate to severe CD define as HBI score > 4. Montreal classification: no limitation, except age> 6.", "candidate_expression": "((> 4) AND (CD) AND (HBI score) AND (Moderate) AND (severe))"}
{"candidate_id": "LLM03262", "doc_id": "NCT03445949_exc", "case_bucket": "or", "source_criterion": "indications to dual antiplatelet therapy other than atrial fibrillation or left atrial appendage occlusion at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. coronary artery disease) indications to anticoagulation at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. pulmonary embolism) known allergy to clopidogrel or acetylsalicylic acid precluding its administration as specified by the protocol any known inborn or acquired coagulation disorders poor tolerance of or technical difficulties with performing transesophageal echocardiography peridevice leak >5mm on transesophageal echocardiography study preceding enrollment left atrial thrombus on transesophageal echocardiography study performed after successful left atrial appendage closure but before enrollment life expectancy of less than 18months participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months chronic kidney disease stage IV and V women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women", "candidate_expression": "((>5mm) AND (acetylsalicylic acid) AND (after successful left atrial appendage closure) AND (allergy) AND (anticoagulation) AND (at the time of enrollment) AND (atrial fibrillation) AND (before enrollment) AND (breast feeding) AND (chronic kidney disease) AND (clopidogrel) AND (coagulation disorders) AND (coronary artery disease) AND (dual antiplatelet therapy) AND (enrollment) AND (indications) AND (left atrial appendage closure) AND (left atrial appendage occlusion) AND (left atrial thrombus) AND (less than 18months) AND (life expectancy) AND (other than) AND (participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months) AND (peridevice leak) AND (poor tolerance) AND (predicted appearance) AND (pregnant) AND (pulmonary embolism) AND (stage IV) AND (stage V) AND (successful) AND (successful left atrial appendage closure) AND (technical difficulties) AND (transesophageal echocardiography) AND (transesophageal echocardiography study) AND (within the duration of the trial) AND (women) AND (women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women))"}
{"candidate_id": "LLM03263", "doc_id": "NCT02299947_inc", "case_bucket": "other", "source_criterion": "Elective surgery for thoracic aneurysm", "candidate_expression": "((Elective surgery) AND (thoracic aneurysm))"}
{"candidate_id": "LLM03264", "doc_id": "NCT03099408_inc", "case_bucket": "or", "source_criterion": "Women be at least 18 years of age Have symptoms of vaginal odor and or/discharge Meet the clinical (Amsel) criteria for BV Willing to participate in research", "candidate_expression": "((Amsel criteria) AND (BV) AND (Willing to) AND (Women) AND (age) AND (at least 18 years) AND (criteria clinical) AND (participate in research) AND (symptoms of) AND (vaginal discharge) AND (vaginal odor))"}
{"candidate_id": "LLM03265", "doc_id": "NCT02557412_inc", "case_bucket": "or", "source_criterion": "Diagnosis of dyslipidemia: The existence of a previous clinical diagnostic of dyslipidemia associated with lipid-lowering therapy. It is also considered patients who have an altered analytical, using the following cutoffs: total cholesterol = 200 mg / dl, triglycerides = 180 mg / dl, HDL-cholesterol = 40 mg / dl or LDL-cholesterol = 150 mg / dl. Lipid-lowering treatment and diet, stable in the last month. A concentration of LDL-cholesterol above 100 mg / dl, in the month prior to inclusion. An apnea-hypopnea index between 5-30 h-1", "candidate_expression": "((= 150 mg / dl) AND (= 180 mg / dl) AND (= 200 mg / dl) AND (= 40 mg / dl) AND (HDL-cholesterol) AND (LDL-cholesterol) AND (Lipid-lowering diet) AND (Lipid-lowering treatment) AND (above 100 mg / dl) AND (altered analytical) AND (apnea-hypopnea index) AND (between 5-30 h-1) AND (dyslipidemia) AND (in the last month) AND (in the month prior to inclusion) AND (inclusion) AND (lipid-lowering therapy) AND (stable) AND (total cholesterol) AND (triglycerides))"}
{"candidate_id": "LLM03266", "doc_id": "NCT02678962_exc", "case_bucket": "or", "source_criterion": "Preexisting ocular diseases or conditions other than age related cataracts, have contraindications for cataract surgery; Preexisting systemic diseases or conditions that may confound the results of the study; Previous ocular surgery history or ocular trauma that may confound the results of the study; Require combined surgery that may confound the results of the study; Previous participation in other clinical trial within 30 days of this study start; Systemic or ocular medications that may confound the outcome of the intervention Pregnant, lactating, or planning to become pregnant during the course of the trial;", "candidate_expression": "((cataract surgery) AND (combined surgery Require may confound the results of the study) AND NOT (cataracts age related) AND ((conditions may confound the results of the study) OR (systemic diseases Preexisting)) AND ((ocular surgery Previous) OR (ocular trauma)) AND ((Systemic medications) OR (ocular medications)) AND ((Pregnant) OR (lactating) OR (pregnant planning to become)) AND ((conditions) OR (contraindications) OR (ocular diseases Preexisting)))"}
{"candidate_id": "LLM03267", "doc_id": "NCT02366819_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed locally advanced gastric (primary endpoint includes proximal and mid-body stomach) or esophagogastric adenocarcinoma; distal gastric (antral) adenocarcinomas are eligible for enrolment but will not be included in the primary analysis Locally advanced disease as determined by endoscopic ultrasound (EUS) stage > primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx) All patients must have diagnostic laparoscopy with diagnostic washings for cytology; both cytology positive and negative patients are eligible for enrolment, but only cytology negative patients will be included in the primary analyses; gross peritoneal disease is not eligible Eastern Cooperative Oncology Group (ECOG) performance status =< 1 Eligible for surgery with curative intent Absolute neutrophil count (ANC) >= 1250/ul Hemoglobin >= 9 g/dL Platelets >= 100,000/ul Total bilirubin < 1.5 x upper limit of normal Serum glutamic oxaloacetic transaminase (SGOT) and serum glutamate pyruvate transaminase (SGPT) < 2.5 x upper limit of normal for patients without liver metastases OR SGOT and SGPT < 5 x upper limit of normal for patients with liver metastases Creatinine =< 1.5 x upper limit of normal Measurable or non-measurable disease by Response Evaluation Criteria in Solid Tumor (RECIST) 1.1 will be allowed Women of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately Patients taking substrates, inhibitors, or inducers of cytochrome P450, family 3, subfamily A, polypeptide 4 (CYP3A4) should be encouraged to switch to alternative drugs whenever possible, given the potential for drug-drug interactions with irinotecan Signed informed consent", "candidate_expression": "((1.1) AND (< 1.5 x upper limit of normal) AND (< 2.5 x upper limit of normal) AND (< 5 x upper limit of normal) AND (=< 1) AND (=< 1.5 x upper limit of normal) AND (> primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx)) AND (>= 100,000/ul) AND (>= 1250/ul) AND (>= 9 g/dL) AND (ANC) AND (Absolute neutrophil count) AND (Creatinine) AND (ECOG) AND (EUS) AND (Eastern Cooperative Oncology Group performance status) AND (Hemoglobin) AND (Locally advanced) AND (Platelets) AND (RECIST) AND (Response Evaluation Criteria in Solid Tumor) AND (SGOT) AND (SGPT) AND (Serum glutamic oxaloacetic transaminase) AND (Signed informed consent) AND (Total bilirubin) AND (adenocarcinoma gastric) AND (adenocarcinomas) AND (antral) AND (curative) AND (cytology) AND (diagnostic) AND (disease) AND (distal gastric) AND (endoscopic ultrasound) AND (esophagogastric adenocarcinoma) AND (laparoscopy) AND (liver metastases) AND (locally advanced) AND (mid-body stomach) AND (negative) AND (omen of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately) AND (positive) AND (proximal stomach) AND (serum glutamate pyruvate transaminase) AND (surgery) AND (washings for cytology) AND (without))"}
{"candidate_id": "LLM03268", "doc_id": "NCT02330705_inc", "case_bucket": "or", "source_criterion": "Mild male factor infertility or unexplained infertility.", "candidate_expression": "((male factor infertility Mild) AND (unexplained infertility))"}
{"candidate_id": "LLM03269", "doc_id": "NCT01996436_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent from patient or patients kin Pregnant women less than 18 years of age of more than 80 years of age Hunt Hess Grade 5 SAH", "candidate_expression": "((5) AND (Hunt Hess Grade) AND (Inability to obtain consent from patient or patients kin) AND (Pregnant women) AND (SAH) AND (age) AND (less than 18 years) AND (more than 80 years))"}
{"candidate_id": "LLM03270", "doc_id": "NCT02715466_inc", "case_bucket": "or", "source_criterion": "Male or female patients = 18 and = 85 years of age Women of child bearing potential must test negative on standard pregnancy test (urine or serum) Patients with body weight = 55 kg and = 140 kg and body mass index (BMI) = 18 kg/m2 Patients diagnosed severe sepsis / septic shock at admission on Intensive Care Unit who can be enrolled within 90 min after admission OR patients diagnosed severe sepsis / septic shock during Intensive Care Unit stay who can be enrolled within 90 min after diagnosis Patients where antibiotic therapy has already been started (prior to randomization) Patient who are fluid responsive. Fluid responsiveness is defined as increase of > 10% in mean arterial pressure (MAP) after passive leg raising (PLR) Signed informed consent by patient, legal representative or authorized person or deferred consent", "candidate_expression": "((= 18 and = 85 years) AND (= 18 kg/m2) AND (= 55 kg and = 140 kg) AND (> 10%) AND (Signed informed consent by patient, legal representative or authorized person or deferred consent) AND (Women) AND (admission on Intensive Care Unit) AND (after passive leg raising (PLR)) AND (age) AND (antibiotic therapy) AND (at admission on Intensive Care Unit) AND (body mass index (BMI)) AND (body weight) AND (child bearing potential) AND (fluid responsive) AND (mean arterial pressure (MAP)) AND (negative) AND (prior to randomization) AND (randomization) AND (standard pregnancy test) AND ((Male) OR (female)) AND ((serum) OR (urine)) AND ((septic shock) OR (severe sepsis)))"}
{"candidate_id": "LLM03271", "doc_id": "NCT02531724_exc", "case_bucket": "other", "source_criterion": "Ongoing treatment with inotropic drugs (not norepinephrine) Central venous oxygen saturation (ScvO2) < 60% despite optimization of hematocrit and volume status Need of renal replacement therapy Ongoing bleeding Patient or next of kin does not consent with study participation", "candidate_expression": "((< 60%) AND (Central venous oxygen saturation (ScvO2)) AND (Need) AND (Ongoing) AND (Patient or next of kin does not consent with study participation) AND (bleeding) AND (despite) AND (inotropic drugs) AND (norepinephrine) AND (not) AND (optimization of hematocrit) AND (renal replacement therapy) AND (treatment) AND (volume status))"}
{"candidate_id": "LLM03272", "doc_id": "NCT02141061_inc", "case_bucket": "other", "source_criterion": "1. Speak, read, and understand English or Spanish and is willing and able to provide written informed consent on an IRB-approved form prior to the initiation of any study procedures; 2. Healthy, premenopausal female age 18-47; 3. History of menstrual events that occur in regular cycles 4. Agreement not to attempt to become pregnant 5. Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication. Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide; 6. Has a negative pregnancy test at the Screening visit. An exception for the pregnancy test requirement will be granted for subjects reporting surgical sterilization in medical history 7. Normal laboratory values or clinically insignificant findings at screening as determined by the Investigator; 8. Subject is willing to remain in the clinic overnight for PK assessment on Days 0 and 8 9. Ability to complete the study procedures in compliance with the protocol.", "candidate_expression": "((18-47) AND (Ability to complete the study procedures in compliance with the protocol.) AND (Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide;) AND (Agreement not to attempt to become pregnant) AND (Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication.) AND (Healthy) AND (History) AND (Normal) AND (Normal laboratory values) AND (Screening visit) AND (age) AND (as determined by the Investigator) AND (at screening) AND (at the Screening visit) AND (clinically insignificant) AND (female) AND (findings) AND (laboratory) AND (menstrual events that occur in regular cycles) AND (negative) AND (pregnancy test) AND (premenopausal) AND (screening))"}
{"candidate_id": "LLM03273", "doc_id": "NCT02838810_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or AFP >2 ULN or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients with a previous use of IFN anti hepatitis B virus treatment or have NAs drug resistance. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((AFP >2 ULN) AND (HIV infection concomitant) AND (Hepatocellular Carcinoma) AND (IFN anti hepatitis B virus) AND (NAs drug) AND (Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (antineoplastic therapy) AND (autoimmune diseases) AND (complications serious) AND (congenital immune deficiency diseases) AND (diabetes) AND (gastrointestinal bleeding) AND (hepatic encephalopathy) AND (hepatorenal syndrome) AND (immunomodulatory therapy) AND (infection) AND (liver cirrhosis) AND (liver diseases) AND (malignancies) AND (organ dysfunctions important) AND (resistance))"}
{"candidate_id": "LLM03274", "doc_id": "NCT02390973_inc", "case_bucket": "or", "source_criterion": "BMI = 35 type 2 diabetes HbA1c = 6,5 % or fasting glycemia =7mmol/l or non-fasting glycemia =11mmol/l able to consent", "candidate_expression": "((= 35) AND (= 6,5 %) AND (=11mmol/l) AND (=7mmol/l) AND (BMI) AND (HbA1c) AND (able to consent) AND (fasting glycemia) AND (non-fasting glycemia) AND (type 2 diabetes))"}
{"candidate_id": "LLM03275", "doc_id": "NCT03231982_exc", "case_bucket": "or", "source_criterion": "The difference in blood pressure between the selected arm versus non-selected arm is = 20 mmHg for siSBP and = 10 mmHg for siDBP at Visit 1 (screening). Blood pressure taken at screening and randomization is = 180 mmHg for siSBP or = 110 mmHg for siDBP. Diagnosed with secondary hypertension or suspected of secondary hypertension [e.g., renovascular disease, adrenal medullary and cortical hyperfunction, coarctation of the aorta, hyperaldosteronism, unilateral or bilateral renal artery stenosis, Cushing's syndrome, pheochromocytoma, polycystic kidney disease, etc.] Patients with symptomatic orthostatic hypertension (the difference in the blood pressures between measured at supine position and measured at standing position is = 20 mmHg for siSBP and = 10 mmHg for siDBP) Diagnosis of type 1 diabetes mellitus (DM) or uncontrolled DM (patients on insulin therapy or with HbA1c > 9%) Patients with severe cardiac conditions: heart failure (NYHA Class 3 or 4), history of ischemic cardiac disease (unstable angina, myocardial infarction), peripheral vascular diseases, percutaneous transluminal angioplasty or coronary artery bypass graft within recent 6 months. Patients with clinically significant ventricular tachycardia, atrial fibrillation, atrial flutter or other clinically significant arrhythmia at the discretion of the investigator Patients with hypertrophic occlusive myocardiopathy, severe occlusive coronary artery disease, aortic stenosis, hemodynamically significant aortic valve or mitral valve stenosis History of cardiogenic shock Presence of severe cerebrovascular disorders (diagnosis of stroke, cerebral infarction or cerebral hemorrhage within recent 6 months) History or current evidence of wasting, autoimmune (such as rheumatoid arthritis and systemic lupus erythematosus) or connective tissue diseases Known diagnosis of moderate or malignant retinopathy (including retinal hemorrhage, visual disturbance and retinal microaneurysm within 6 months) Patients with surgical or medical intestinal diseases or having received surgeries that could interfere with drug absorption distribution, metabolism and elimination History of malignancy including leukemia and lymphoma within recent 5 years except for localized basal cell carcinoma of the skin) Patients with any inflammatory diseases requiring chronic anti-inflammatory therapy Renal failure on dialysis AST or ALT >2 x upper limit of normal (ULN) Serum creatinine > 1.5 x ULN Serum potassium < 3.5 mmol/L or >5.5 mmol/L Needs for co-administration of non-study antihypertensive agents or contraindicated medications during the study History of hypersensitivity to ARBs or dihydropyridines History of angioedema to treatment with ACE inhibitors or ARBs Pregnant or lactating women and female volunteers of childbearing potential (except for women who are surgically sterile) who are not willing to use an adequate method of contraception (oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening. History of drug or alcohol abuse within recent 1 year Patients having received any other investigational product within recent 12 weeks Conditions which render a subject ineligible for the study at the discretion of the investigator", "candidate_expression": "(((oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening.) AND (= 10 mmHg) AND (= 110 mmHg) AND (= 180 mmHg) AND (= 20 mmHg) AND (> 1.5 x ULN) AND (> 9%) AND (>2 x upper limit of normal (ULN)) AND (Blood pressure) AND (Class 3 or 4) AND (History) AND (History of) AND (NYHA) AND (Renal failure) AND (Serum creatinine) AND (Serum potassium) AND (adequate method of contraception) AND (angioedema) AND (anti-inflammatory therapy) AND (arrhythmia) AND (at Visit 1) AND (at randomization) AND (at screening) AND (cardiac conditions) AND (cardiogenic shock) AND (cerebrovascular disorders) AND (childbearing potential) AND (chronic) AND (clinically significant) AND (co-administration during the study) AND (dialysis) AND (difference in blood pressure) AND (difference in the blood pressures) AND (except for) AND (hemodynamically significant) AND (history) AND (hypersensitivity) AND (inflammatory diseases) AND (localized basal cell carcinoma of the skin) AND (malignancy) AND (measured at supine position and measured at standing position) AND (non-study) AND (not) AND (orthostatic hypertension) AND (other investigational product) AND (retinopathy) AND (secondary) AND (selected arm versus non-selected arm) AND (severe) AND (siDBP) AND (siSBP) AND (suspected) AND (symptomatic) AND (treatment) AND (uncontrolled) AND (willing to) AND (within 6 months) AND (within recent 1 year) AND (within recent 12 weeks) AND (within recent 5 years) AND (within recent 6 months) AND ((malignant) OR (moderate)) AND ((retinal hemorrhage) OR (retinal microaneurysm) OR (visual disturbance)) AND ((intestinal diseases) OR (surgeries)) AND ((medical) OR (surgical)) AND ((could interfere with drug absorption distribution) OR (could interfere with drug elimination) OR (could interfere with drug metabolism)) AND ((leukemia) OR (lymphoma)) AND ((siDBP) OR (siSBP)) AND ((ALT) OR (AST)) AND ((< 3.5 mmol/L) OR (>5.5 mmol/L)) AND ((antihypertensive agents) OR (contraindicated medications)) AND ((ARBs) OR (dihydropyridines)) AND ((ACE inhibitors) OR (ARBs)) AND ((hypertension)) AND ((Pregnant) OR (lactating)) AND ((female) OR (women)) AND ((alcohol abuse) OR (drug abuse)) AND ((bilateral) OR (unilateral)) AND ((Cushing's syndrome) OR (adrenal medullary hyperfunction) OR (coarctation of the aorta) OR (cortical hyperfunction) OR (hyperaldosteronism) OR (pheochromocytoma) OR (polycystic kidney disease) OR (renal artery stenosis) OR (renovascular disease)) AND ((DM) OR (type 1 diabetes mellitus (DM))) AND ((HbA1c) OR (insulin therapy)) AND ((heart failure) OR (ischemic cardiac disease)) AND ((myocardial infarction) OR (peripheral vascular diseases) OR (unstable angina)) AND ((coronary artery bypass graft) OR (percutaneous transluminal angioplasty)) AND ((atrial fibrillation) OR (atrial flutter) OR (ventricular tachycardia)) AND ((aortic stenosis) OR (hypertrophic occlusive myocardiopathy) OR (occlusive coronary artery disease)) AND ((aortic valve stenosis) OR (mitral valve stenosis)) AND ((cerebral hemorrhage) OR (cerebral infarction) OR (stroke)) AND ((History) OR (current)) AND ((autoimmune diseases) OR (connective tissue diseases) OR (wasting)) AND ((rheumatoid arthritis) OR (systemic lupus erythematosus)))"}
```
