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
{"candidate_id": "LLM06951", "doc_id": "NCT02365870_inc", "case_bucket": "other", "source_criterion": "Diagnosis of DSM 5 Anxiety Disorder Stable medical history and general health On stable anti-parkinsonian therapy for 2 weeks before enrollment", "candidate_expression": "((DSM 5 Anxiety Disorder) AND (Stable general health) AND (Stable medical history) AND (anti-parkinsonian therapy) AND (before enrollment) AND (for 2 weeks) AND (stable))"}
{"candidate_id": "LLM06952", "doc_id": "NCT02833116_exc", "case_bucket": "or", "source_criterion": "Patients with high intracranial pressure. Patients with Multiple Sclerosis. Patients with Guillain-Barré syndrome radiculopathy of vascular origin. Patients with previous lumbar surgery. Patients pregnant or lactating. Patients with allergy or intolerance to any of the drugs used. Patients with severe cognitive impairment. Patients with intrathecal injectio radiculalgia. Patients with poorly controlled major psychiatric pathology. Patients with type I diabetes or poorly controlled type II diabetes (Hb1Ac>8.5). Patients with glaucoma. Patients with caudal equine syndrome. Patients with pre-treatment with steroid injections/or local anesthetics. Patients with central canal stenosis. patients with chronic treatment with oral corticosteroids without stabilized pattern.", "candidate_expression": "((>8.5) AND (Guillain-Barré syndrome radiculopathy) AND (Hb1Ac) AND (Multiple Sclerosis) AND (Patients pregnant or lactating) AND (allergy) AND (caudal equine syndrome) AND (central canal stenosis) AND (cognitive impairment) AND (drugs) AND (glaucoma) AND (high) AND (intolerance) AND (intracranial pressure) AND (intrathecal injectio radiculalgia) AND (local anesthetics) AND (lumbar surgery.) AND (major) AND (oral corticosteroids) AND (poorly controlled) AND (psychiatric pathology) AND (severe) AND (steroid injections) AND (type I diabetes) AND (type II diabetes) AND (vascular))"}
{"candidate_id": "LLM06953", "doc_id": "NCT02488057_exc", "case_bucket": "other", "source_criterion": "pregnant 30 min or more of moderate to vigorous activity more than 3 times per week cardiovascular disease physical limitations that might be aggravated by moderate physical activity planning to move in next 12-24 months diabetic", "candidate_expression": "((30 min or more) AND (aggravated by physical activity) AND (cardiovascular disease) AND (diabetic) AND (in next 12-24 months) AND (moderate) AND (moderate to vigorous activity) AND (more than 3 times per week) AND (physical limitations) AND (planning to move) AND (pregnant))"}
{"candidate_id": "LLM06954", "doc_id": "NCT02601157_inc", "case_bucket": "other", "source_criterion": "Patients with de novo stenotic lesions who are suitable for coronary stenting with drug-eluting stent", "candidate_expression": "((coronary stenting suitable) AND (drug-eluting stent) AND (stenotic lesions de novo))"}
{"candidate_id": "LLM06955", "doc_id": "NCT02746900_inc", "case_bucket": "other", "source_criterion": "18-50 ages Singleton pregnancy Cervical length <=25mm between 18(0) and 23(6) weeks", "candidate_expression": "((18-50) AND (<=25mm) AND (Cervical length) AND (Singleton pregnancy) AND (ages) AND (between 18(0) and 23(6) weeks))"}
{"candidate_id": "LLM06956", "doc_id": "NCT03336801_inc", "case_bucket": "other", "source_criterion": "Scheduled back surgery", "candidate_expression": "(back surgery Scheduled)"}
{"candidate_id": "LLM06957", "doc_id": "NCT03097068_exc", "case_bucket": "or", "source_criterion": "History of anti-vascular endothelial growth factor treatment in the past 12 months Any diabetic macular edema treatment in the past 4 months Heart attack, stroke, transient ischemic attack or acute congestive heart failure within 4 months", "candidate_expression": "((Heart attack) AND (acute congestive heart failure within 4 months) AND (anti-vascular endothelial growth factor in the past 12 months) AND (diabetic macular edema) AND (stroke) AND (transient ischemic attack) AND (treatment in the past 4 months))"}
{"candidate_id": "LLM06958", "doc_id": "NCT02652637_exc", "case_bucket": "or", "source_criterion": "Emergency surgery needed Bowel obstruction Colonoscopy scheduled to be undertaken peroperatively Other reason indicating mechanical preparation or contradicting it Allergy to used drugs (PEG, neomycin, metronidazole)", "candidate_expression": "((Allergy) AND (Bowel obstruction) AND (Colonoscopy) AND (Emergency surgery) AND (contradicting) AND (drugs) AND (mechanical preparation) AND (needed) AND (peroperatively) AND (scheduled) AND (undertaken) AND ((PEG) OR (metronidazole) OR (neomycin)))"}
{"candidate_id": "LLM06959", "doc_id": "NCT02609048_inc", "case_bucket": "or", "source_criterion": "1. Must have given written informed consent (signed and dated) and any authorizations required by local law 2. 18 to 75 years old (inclusive) 3. Male or female with a diagnosis of PBC, by at least two of the following criteria: History of AP above ULN for at least six months Positive Anti-Mitochondrial Antibodies (AMA) titers (>1/40 on immunofluorescence or M2 positive by enzyme linked immunosorbent assay (ELISA) or positive PBC-specific antinuclear antibodies Documented liver biopsy result consistent with PBC 4. On a stable and recommended dose of UDCA for the past twelve months 5. AP ≥ 1.67 × ULN 6. For females of reproductive potential, use of at least one barrier contraceptive and a second effective birth control method during the study and for at least two weeks after the last dose. For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose", "candidate_expression": "((AP above ULN for at least six months) AND (AP ≥ 1.67 × ULN) AND (For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose) AND (Must have given written informed consent (signed and dated) and any authorizations required by local law) AND (PBC) AND (PBC-specific antinuclear antibodies positive) AND (Positive Anti-Mitochondrial Antibodies (AMA) titers) AND (UDCA stable dose recommended dose for the past twelve months) AND (appropriate) AND (barrier contraceptive at least one) AND (birth control method second effective during the study for at least two weeks after the last dose) AND (condoms) AND (contraception appropriate) AND (effective) AND (enzyme linked immunosorbent assay (ELISA) M2 positive) AND (female) AND (females) AND (following criteria at least two) AND (immunofluorescence >1/40) AND (liver biopsy) AND (male) AND (reproductive potential) AND (years old 18 to 75 years old (inclusive)) AND NOT (pregnant during the study for at least two weeks after the last dose) AND ((Male) OR (female)))"}
{"candidate_id": "LLM06960", "doc_id": "NCT02560766_exc", "case_bucket": "or", "source_criterion": "History of a primary sleep disorder other than RLS that may significantly affect the symptoms of RLS. Serum ferritin level < 20 ng/mL at screening. History of allergy, hypersensitivity, or intolerance to HORIZANT or any other gabapentin products (eg, Neurontin®, Gralise®). Suffering from a movement disorder that could mimic or confound the accurate diagnosis of RLS (eg, Tourette's syndrome, tic disorder, periodic limb movement disorder [PLMD], sleep disorders). Currently meet Diagnostic and Statistical Manual of Mental Disorders - Fifth Edition (DSM-5) criteria for substance use disorder, or history thereof, within 12 months before dosing. Current or past history of any significant psychiatric disorder including, but not limited to, depression (treatment with antidepressants), bipolar disorder, or schizophrenia. Diagnosis of attention-deficit hyperactivity disorder (ADHD) is allowed, provided the patient is not receiving medication(s) known to affect the assessment of RLS. History of suicidal behavior or suicidal ideation as indicated by the C-SSRS, administered at screening (the questionnaire is provided in Appendix 4), and as per investigator's judgment. History of seizure disorder or at increased risk for development of a seizure disorder including, but not limited to, complicated febrile seizure and history of significant head injury. Medical condition or disorder that would interfere with the action, absorption, distribution, metabolism, or excretion of gabapentin enacarbil, or, in the investigator's judgment is considered to be clinically significant and may pose a safety concern, or, could interfere with the accurate assessment of safety or efficacy, or could potentially affect a patient's safety or study outcome. Clinically significant abnormal laboratory result or physical examination finding not resolved by the time of baseline assessments.", "candidate_expression": "((ADHD) AND (DSM-5) AND (Diagnostic and Statistical Manual of Mental Disorders - Fifth Edition) AND (PLMD) AND (Serum ferritin < 20 ng/mL) AND (allowed) AND (antidepressants) AND (attention-deficit hyperactivity disorder) AND (movement disorder) AND (primary sleep disorder) AND (psychiatric disorder significant) AND (seizure disorder) AND (substance use disorder within 12 months) AND NOT (RLS) AND ((HORIZANT) OR (gabapentin)) AND ((Gralise) OR (Neurontin)) AND ((Tourette's syndrome) OR (periodic limb movement disorder) OR (sleep disorders) OR (tic disorder)) AND ((bipolar disorder) OR (depression) OR (schizophrenia)) AND ((suicidal behavior) OR (suicidal ideation)) AND ((complicated febrile seizure) OR (head injury)) AND ((allergy) OR (hypersensitivity) OR (intolerance)))"}
{"candidate_id": "LLM06961", "doc_id": "NCT02364648_exc", "case_bucket": "other", "source_criterion": "History of cardiovascular disease; Current pregnancy; Uncontrolled hypertension; Uncontrolled hyperlipidemia; Current hormone replacement therapy; Current use of tobacco products; Elevated liver enzymes; Current autoimmune disease; Daily use of of antioxidants >300mg", "candidate_expression": "((>300mg) AND (Current) AND (Daily use) AND (Elevated liver enzymes) AND (History) AND (Uncontrolled) AND (antioxidants) AND (autoimmune disease) AND (cardiovascular disease) AND (hormone replacement therapy) AND (hyperlipidemia) AND (hypertension) AND (pregnancy) AND (use of tobacco products))"}
{"candidate_id": "LLM06962", "doc_id": "NCT02102243_inc", "case_bucket": "other", "source_criterion": "Normotensive controls Stage I (140-159/90-99 mmHg) untreated subjects with essential hypertension Patients with PA and stage I (140-159/90-99 mmHg) hypertension", "candidate_expression": "((Normotensive) AND (PA) AND (Stage I) AND (controls) AND (essential hypertension) AND (hypertension) AND (stage I) AND (untreated))"}
{"candidate_id": "LLM06963", "doc_id": "NCT01084993_exc", "case_bucket": "or", "source_criterion": "Intolerance or allergy to ASA, clopidogrel or ticlopidine precluding treatment for 12 months Concurrent participation in other investigational study Femoral sheath (artery)", "candidate_expression": "((Concurrent participation in other investigational study) AND (Femoral sheath (artery)) AND (for 12 months) AND (precluding) AND (treatment) AND ((Intolerance) OR (allergy)) AND ((ASA) OR (clopidogrel) OR (ticlopidine)))"}
{"candidate_id": "LLM06964", "doc_id": "NCT01639664_exc", "case_bucket": "or", "source_criterion": "Age less than 14 years Pregnancy Estimated life expectancy (due to comorbidities) less than 90 days Presence of relative or absolute contraindications to CPFA Admission from an other ICU where the patient remained for more than 24 hours Absence of informed consent", "candidate_expression": "((Absence of informed consent) AND (Admission) AND (Age) AND (CPFA) AND (Estimated life expectancy) AND (Pregnancy) AND (absolute contraindications) AND (an other ICU) AND (for more than 24 hours) AND (less than 14 years) AND (less than 90 days) AND (patient remained) AND (relative contraindications))"}
{"candidate_id": "LLM06965", "doc_id": "NCT03056287_inc", "case_bucket": "or", "source_criterion": "1) age 50-70 2) stroke within the past 6 to 60 months, 3) major depressive disorder (PHQ-9 > 10) and diagnosed using the Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV), 4) residual paresis in the lower extremity (Fugl-Meyer LE motor score <34), 5) ability to walk without assistance and without an AFO on the treadmill ≥ 30 seconds at speeds ranging from 0.2-0.8 m/s, 6) no antidepressant medications or clinically able to discontinue medications, 7) HRSD question #9 regarding suicide <2, 8) provision of informed consent. In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.", "candidate_expression": "((50-70) AND (<2) AND (<34) AND (> 10) AND (AFO on the treadmill) AND (Fugl-Meyer LE motor score) AND (HRSD question #9) AND (In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.) AND (PHQ-9) AND (Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV)) AND (ability to walk without assistance) AND (age) AND (clinically able to discontinue medications) AND (from 0.2-0.8 m/s) AND (lower extremity) AND (major depressive disorder) AND (no) AND (residual paresis) AND (speeds) AND (stroke) AND (within the past 6 to 60 months) AND (without) AND (≥ 30 seconds) AND ((antidepressant) OR (clinically able to discontinue medications)))"}
{"candidate_id": "LLM06966", "doc_id": "NCT02934269_inc", "case_bucket": "or", "source_criterion": "Healthy male and/or female subjects between the ages of 18 and 55 years, and a body mass index (BMI) of ≥ 18 and ≤ 33 kg/m2 with body weight ≥ 50 and ≤ 90 kg at screening. Females must have been surgically sterilized (hysterectomy, bilateral oophorectomy, or bilateral salpingo-oophorectomy; proper documentation required) at least 6 months before screening, or be postmenopausal (defined as 24 consecutive months without menses before screening, with a follicle-stimulating hormone [FSH] level of > 40 IU/L at screening).", "candidate_expression": "((24 consecutive months) AND (> 40 IU/L) AND (Females) AND (Healthy) AND (ages) AND (at least 6 months before) AND (at screening) AND (before screening) AND (between 18 and 55 years) AND (body mass index (BMI)) AND (body weight) AND (follicle-stimulating hormone [FSH]) AND (menses) AND (screening) AND (without) AND (≥ 18 and ≤ 33 kg/m2) AND (≥ 50 and ≤ 90 kg) AND ((bilateral oophorectomy) OR (bilateral salpingo-oophorectomy) OR (hysterectomy)) AND ((postmenopausal) OR (surgically sterilized)) AND ((female) OR (male)))"}
{"candidate_id": "LLM06967", "doc_id": "NCT02804126_exc", "case_bucket": "or", "source_criterion": "coagulopathy allergy to to local anesthetics depression, antidepressant drugs treatment epilepsy usage of painkiller before surgery addiction to alcohol or recreational drugs", "candidate_expression": "((addiction to alcohol) AND (addiction to recreational drugs) AND (allergy) AND (antidepressant drugs) AND (coagulopathy) AND (depression) AND (epilepsy) AND (local anesthetics) AND (painkiller before surgery))"}
{"candidate_id": "LLM06968", "doc_id": "NCT03056287_exc", "case_bucket": "or", "source_criterion": "1. Unable to ambulate at least 150 feet prior to stroke, or experienced intermittent claudication while walking; 2. history of congestive heart failure, unstable cardiac arrhythmias, hypertrophic cardiomyopathy, severe aortic stenosis, angina or dyspnea at rest or during ADL's; 3. History of oxygen dependence; 4. Preexisting neurological disorders, dementia or previous stroke; 5. History of major head trauma; 6. Legal blindness or severe visual impairment; 7. history of psychosis or other Axis I disorder that is primary; 8. Life expectancy <1 yr.; 9. Severe arthritis or other problems that limit passive range of motion; 10. History of DVT or pulmonary embolism within 6 months; 11. Uncontrolled diabetes with recent weight loss, diabetic coma, or frequent insulin reactions; 12. Severe hypertension with systolic >200 mmHg and diastolic >110 mmHg at rest; 13. attempt of suicide in the last 2 years or at suicidal risk assessed by SCID interview; 14. Previous or current enrollment in a clinical trial to enhance motor recovery; 15) currently exercising ≥ 2 times per week (≥20 minutes); 16) Presence of non-MR compatible implants, pregnancy or severe claustrophobia.", "candidate_expression": "((Axis I disorder history primary) AND (DVT) AND (Legal blindness) AND (Life expectancy <1 yr) AND (SCID interview) AND (Severe arthritis) AND (Severe hypertension) AND (Unable to ambulate at least 150 feet prior) AND (angina) AND (at suicidal risk) AND (attempt of suicide in the last 2 years) AND (claustrophobia severe) AND (congestive heart failure) AND (dementia Preexisting) AND (diabetes Uncontrolled) AND (diabetic coma) AND (diastolic >110 mmHg) AND (dyspnea at rest) AND (dyspnea during ADL's) AND (history) AND (hypertrophic cardiomyopathy) AND (insulin reactions frequent) AND (intermittent claudication while walking) AND (major head trauma History) AND (neurological disorders Preexisting) AND (non-MR compatible implants) AND (oxygen dependence History) AND (pregnancy) AND (problems that limit passive range of motion) AND (psychosis history) AND (pulmonary embolism within 6 months) AND (severe aortic stenosis) AND (severe visual impairment) AND (stroke) AND (stroke previous) AND (systolic >200 mmHg) AND (unstable cardiac arrhythmias) AND (weight loss))"}
{"candidate_id": "LLM06969", "doc_id": "NCT02566928_inc", "case_bucket": "or", "source_criterion": "between 7 to 70 years of age fluent in English or Spanish plans to receive care in the Community Health Center during the next year presents with signs and symptoms of a SSTI willing/able to provide informed consent", "candidate_expression": "((Community Health Center) AND (SSTI) AND (age) AND (between 7 to 70 years) AND (during the next year) AND (fluent in English) AND (fluent in Spanish) AND (plans to) AND (receive care) AND (signs) AND (symptoms) AND (willing/able to provide informed consent))"}
{"candidate_id": "LLM06970", "doc_id": "NCT02944292_inc", "case_bucket": "other", "source_criterion": "Age 18 years or older Mechanical ventilation IAP between 12 and 20 mmHg in at least two consecutive measurements within 1-12 h Spontaneous breathing activity of at least 6 breaths/minute RASS score between 0 and -4 Physician-led sedation (if sedated; as opposed to nurse-led protocol)", "candidate_expression": "((Age 18 years or older) AND (IAP between 12 and 20 mmHg at least two consecutive measurements) AND (Mechanical ventilation) AND (RASS score between 0 and -4) AND (Spontaneous breathing activity at least 6 breaths/minute) AND (sedation Physician-led))"}
{"candidate_id": "LLM06971", "doc_id": "NCT03126214_inc", "case_bucket": "or", "source_criterion": "Age = 65 years with one additional stroke risk factor (hypertension, diabetes, heart failure history of or left ventricular ejection fraction <0.40), previous stroke or transient ischemic attack). Atrial fibrillation and not on oral anticoagulation (OAC) therapy but eligible Atrial fibrillation on sub-optimal OAC", "candidate_expression": "((<0.40) AND (= 65 years) AND (Age) AND (Atrial fibrillation) AND (OAC) AND (diabetes) AND (heart failure) AND (history) AND (hypertension) AND (left ventricular ejection fraction) AND (not) AND (one additional) AND (oral anticoagulation (OAC) therapy) AND (previous) AND (risk factor) AND (stroke) AND (sub-optimal) AND (transient ischemic attack))"}
{"candidate_id": "LLM06972", "doc_id": "NCT01895946_inc", "case_bucket": "or", "source_criterion": "Aged at least 18 years The presence of a solid, malignant tumour, excluding lymphoma, that is resistance to standard therapies or for which no standard therapies exist The presence of at least one lesion that can be accurately assessed at baseline by Computerised Tomography (CT), Magnetic Resonance Imaging (MRI) or plain X-ray and is suitable for repeated assessment Estimated life expectancy of more than 12 weeks", "candidate_expression": "((Aged at least 18 years) AND (Computerised Tomography (CT)) AND (Estimated life expectancy more than 12 weeks) AND (Magnetic Resonance Imaging (MRI)) AND (lesion at least one accurately assessed at baseline suitable for repeated assessment) AND (plain X-ray) AND (solid, malignant tumour) AND NOT (lymphoma resistance to standard therapies for which no standard therapies exist))"}
{"candidate_id": "LLM06973", "doc_id": "NCT02330757_exc", "case_bucket": "or", "source_criterion": "PCOS or polycystic ovary on ultrasound scan. Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Moderate) AND (PCOS) AND (Previous) AND (Uterine abnormalities) AND (endometriosis) AND (myoma) AND (polycystic ovary) AND (severe) AND (ultrasound scan) AND (uterine surgery))"}
{"candidate_id": "LLM06974", "doc_id": "NCT03181984_inc", "case_bucket": "other", "source_criterion": "Age range: 14 to 65 years-old; Clinically diagnosed of Port-wine Stain; Patients receiving hemoporfin based upon the clinical judgment of the investigator; Written informed consent signed and agreed to receive periodic follow-up", "candidate_expression": "((Age 14 to 65 years-old) AND (Port-wine Stain) AND (Written informed consent signed and agreed to receive periodic follow-up) AND (hemoporfin))"}
{"candidate_id": "LLM06975", "doc_id": "NCT02270970_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
