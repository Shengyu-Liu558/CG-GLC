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
{"candidate_id": "LLM03426", "doc_id": "NCT02339844_inc", "case_bucket": "or", "source_criterion": "Inclusion Criteria Patients: Fulfilling the diagnostic criteria of schizophrenia or schizoaffective disorder according to ICD-10 (International Classification of Diseases version 10) or DSM-IV/V (Diagnostic and Statistical Manual version 4 /5), Age 18-45 years, Never treated with antipsychotic compounds or central nervous system (CNS) stimulants, Legally competent Inclusion criteria controls: Matching patients on age (+/- 2 years), sex and parental socioeconomic status, Age 18-45 years, No psychiatric or physical disease.", "candidate_expression": "((18-45 years) AND (Age) AND (DSM-IV/V (Diagnostic and Statistical Manual version 4 /5)) AND (ICD-10 (International Classification of Diseases version 10)) AND (Legally competent) AND (Never) AND (No) AND (Patients) AND (antipsychotic compounds) AND (central nervous system (CNS) stimulants) AND (controls) AND (physical disease) AND (psychiatric disease) AND (schizoaffective disorder) AND (schizophrenia))"}
{"candidate_id": "LLM03427", "doc_id": "NCT02531724_inc", "case_bucket": "other", "source_criterion": "Patients in the cardiothoracic intensive care after cardiac surgery with cardiopulmonary bypass Acute kidney injury, defined as increase in S-creatinine 50% or 27 mol/L Normal S-creatinine before surgery", "candidate_expression": "((50% or 27 mol/L) AND (Acute kidney injury) AND (Normal) AND (S-creatinine) AND (after cardiac surgery with cardiopulmonary bypass) AND (before surgery) AND (cardiac surgery) AND (cardiac surgery with cardiopulmonary bypass) AND (cardiopulmonary bypass) AND (cardiothoracic intensive care) AND (increase in S-creatinine) AND (surgery))"}
{"candidate_id": "LLM03428", "doc_id": "NCT03193684_inc", "case_bucket": "other", "source_criterion": "eGFR>60 ml/min healthy volunteers type 2 diabetes patients who otherwise healthy", "candidate_expression": "((eGFR >60 ml/min) AND (healthy) AND (type 2 diabetes))"}
{"candidate_id": "LLM03429", "doc_id": "NCT02298504_exc", "case_bucket": "or", "source_criterion": "Teeth with clinical symptoms of irriversible pulpitis or pulp necrosis or acute dental infection Children with systemic illness that contraindicated vital pulp treatment such a sickle cell disease Teeth that are not restorable", "candidate_expression": "((Teeth that are not restorable) AND (contraindicated) AND (sickle cell disease) AND (systemic illness) AND (vital pulp treatment) AND ((acute dental infection) OR (irriversible pulpitis Teeth) OR (pulp necrosis Teeth)))"}
{"candidate_id": "LLM03430", "doc_id": "NCT03208244_inc", "case_bucket": "scope", "source_criterion": "Recipient is Age = 18 years Serum ALT within normal limits with no history of liver disease Lack of sensitization (i.e. PRA < 20%) that would be expected to result in a high likelihood of needing aggressive immunosuppression to treat rejection", "candidate_expression": "((< 20%) AND (= 18 years) AND (Age) AND (Lack of) AND (PRA) AND (Serum ALT) AND (history) AND (liver disease) AND (no) AND (sensitization) AND (within normal limits))"}
{"candidate_id": "LLM03431", "doc_id": "NCT02969876_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03432", "doc_id": "NCT02653131_exc", "case_bucket": "other", "source_criterion": "HPN < 12 months metabolically unstable cancer as the reason for intestinal failure", "candidate_expression": "((< 12 months) AND (HPN) AND (cancer) AND (intestinal failure) AND (metabolically unstable))"}
{"candidate_id": "LLM03433", "doc_id": "NCT01490034_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03434", "doc_id": "NCT03234816_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities Hypertensive disorders of pregnancy, Peripartum bleeding Baseline systolic blood pressure (SBP) < 100 mmHg Body mass index > 35", "candidate_expression": "((< 100 mmHg) AND (> 35) AND (Baseline) AND (Body mass index) AND (Cardiac morbidities) AND (Hypertensive disorders of pregnancy) AND (Peripartum bleeding) AND (SBP) AND (systolic blood pressure))"}
{"candidate_id": "LLM03435", "doc_id": "NCT00867958_inc", "case_bucket": "other", "source_criterion": "1. Patient is over 18 years old. 2. Patient is scheduled for a non-emergency procedure. 3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.", "candidate_expression": "((3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.) AND (non-emergency) AND (non-emergency procedure) AND (over 18 years old) AND (scheduled) AND (years old))"}
{"candidate_id": "LLM03436", "doc_id": "NCT02368743_exc", "case_bucket": "or", "source_criterion": "Patient included in an interventional study assessing treatment for active proctitis or distal proctosigmoiditis. Patient with left sided, colitis or pancolitis. Patient with severe proctitis (MAYO score ≥ 11 at inclusion). Patient previously treated with biologics. Patient treated with immunosuppressive within 1 month before study inclusion. Patient treated with corticosteroids within 2 weeks before study inclusion.", "candidate_expression": "((MAYO score) AND (active proctitis) AND (at inclusion) AND (biologics) AND (colitis) AND (corticosteroids) AND (distal proctosigmoiditis) AND (immunosuppressive) AND (left sided) AND (pancolitis) AND (previously) AND (proctitis) AND (severe) AND (study inclusion) AND (treated) AND (treatment) AND (within 1 month before study inclusion) AND (within 2 weeks before study inclusion) AND (≥ 11))"}
{"candidate_id": "LLM03437", "doc_id": "NCT03058835_inc", "case_bucket": "or", "source_criterion": "18 - 64 years old Able to give consent unprotected sex (in past 6 months) with 1 or more men of unknown HIV status evaluated for an STI within 6 months prior to screening sex in last 6 months with an HIV-infected partner IDU with report of using previously used or shared needles in past 6 months or has been in a methadone, buprenorphine, or suboxone treatment program in past 6 months or engaging in high-risk sexual behaviors individuals engaging in transactional sex (i.e sex for money, drugs, or housing) Infrequently uses condoms during sex with 1 or more partners of unknown HIV status who are known to be at substantial risk of HIV infection (IDU or bisexual male partner) CrCl = 60 ml/min HIV- uninfected women desiring PrEP", "candidate_expression": "((CrCl = 60 ml/min) AND (HIV- uninfected) AND (HIV-infected partner) AND (IDU) AND (Infrequently uses condoms during sex) AND (PrEP desiring) AND (evaluated for an STI within 6 months prior to screening) AND (men of unknown HIV status 1 or more) AND (old 18 - 64 years) AND (partners of unknown HIV status 1 or more at substantial risk of HIV infection) AND (sex in last 6 months) AND (transactional sex) AND (unprotected sex in past 6 months) AND (women) AND ((buprenorphine) OR (methadone) OR (suboxone)) AND ((engaging in high-risk sexual behaviors) OR (treatment program in past 6 months) OR (using previously used or shared needles in past 6 months)) AND ((sex for drugs) OR (sex for housing) OR (sex for money)) AND ((IDU) OR (bisexual male partner)))"}
{"candidate_id": "LLM03438", "doc_id": "NCT02951832_exc", "case_bucket": "or", "source_criterion": "Having experienced severe allergies, trauma history and/or operation history within 3 months; With a history of mental illness and/or family history of mental illness; Limb disabled; Taking medicine within one month; Suffering major events or having mood swings.", "candidate_expression": "((Limb disabled) AND (family history) AND (history) AND (major events) AND (medicine) AND (mental illness) AND (mood swings) AND (operation) AND (severe allergies) AND (trauma) AND (within 3 months) AND (within one month))"}
{"candidate_id": "LLM03439", "doc_id": "NCT03493919_inc", "case_bucket": "or", "source_criterion": "Subjects who, in the opinion of the investigator, can and will comply with the requirements of the protocol. Written informed consent obtained from the subject prior to performing any study specific procedure. A male or female between, and including, 18 and 50 years of age at the time of the first study visit. Healthy subjects as established by medical history and clinical examination before entering into the study. Healthy subjects with no medical conditions that, in the opinion of the investigator, prevents the subject from participating in the study. Subjects must weigh at least 110 pounds (50 kg), but not to present obesity (BMI < 32kg/m2). Female subjects of non-childbearing potential may be enrolled in the study. Non-childbearing potential is defined as pre-menarche, current bilateral tubal ligation or occlusion, hysterectomy, bilateral ovariectomy or post-menopause. has practiced adequate contraception for 30 days prior to vaccination, and has a negative pregnancy test on the day of vaccination and has agreed to continue adequate contraception during the entire treatment period and for 1 month, after completion of the vaccination series.", "candidate_expression": "((18 and 50 years) AND (30 days prior to vaccination) AND (< 32kg/m2) AND (BMI) AND (Female) AND (Healthy) AND (Written informed consent) AND (adequate) AND (adequate contraception) AND (age) AND (at least 110 pounds) AND (at least 50 kg) AND (at the time of the first study visit) AND (before entering into the study) AND (bilateral ovariectomy) AND (bilateral tubal ligation) AND (bilateral tubal occlusion) AND (childbearing potential) AND (clinical examination) AND (completion of the vaccination series) AND (comply with the requirements of the protocol) AND (continue) AND (contraception) AND (current) AND (entering into the study) AND (medical history) AND (negative) AND (non-) AND (not to present) AND (obesity) AND (on the day of vaccination) AND (performing any study specific procedure) AND (pregnancy test) AND (prior to performing any study specific procedure) AND (study specific procedure) AND (the first study visit) AND (vaccination) AND (weigh) AND ((bilateral tubal ligation) OR (bilateral tubal occlusion)) AND ((bilateral ovariectomy) OR (hysterectomy) OR (post-menopause) OR (pre-menarche)) AND ((during the entire treatment period) OR (for 1 month, after completion of the vaccination series)) AND ((female) OR (male)))"}
{"candidate_id": "LLM03440", "doc_id": "NCT02862912_exc", "case_bucket": "or", "source_criterion": "Any contraindication to neuraxial anesthesia (history of neurologic disease (e.g., multiple sclerosis, spinal stenosis, central or peripheral neuropathy) Pre-existing/chronic back pain Ester local anesthetic allergy, PABA allergy History of atypical cholinesterase (CP is metabolized by cholinesterase)", "candidate_expression": "((Ester local anesthetic) AND (PABA) AND (atypical cholinesterase History) AND (back pain) AND (contraindication) AND (neuraxial anesthesia) AND (neurologic disease history) AND ((Pre-existing) OR (chronic)) AND ((allergy)) AND ((central neuropathy) OR (multiple sclerosis) OR (peripheral neuropathy) OR (spinal stenosis)))"}
{"candidate_id": "LLM03441", "doc_id": "NCT00404495_exc", "case_bucket": "other", "source_criterion": "Diagnosis of brainstem glioma Concurrent administration of any other anti-tumor therapy Pre-existing uncontrolled diarrhea", "candidate_expression": "((Concurrent) AND (anti-tumor therapy) AND (any other) AND (brainstem glioma) AND (uncontrolled diarrhea))"}
{"candidate_id": "LLM03442", "doc_id": "NCT03045562_inc", "case_bucket": "other", "source_criterion": "Informed consent must be obtained prior to any study procedure. Age>18 years. Subjects of STEMI who underwent primary PCI within the first 12 hours.", "candidate_expression": "((Age >18 years.) AND (Informed consent must be obtained prior to any study procedure) AND (STEMI) AND (primary PCI within the first 12 hours.))"}
{"candidate_id": "LLM03443", "doc_id": "NCT01895946_inc", "case_bucket": "or", "source_criterion": "Aged at least 18 years The presence of a solid, malignant tumour, excluding lymphoma, that is resistance to standard therapies or for which no standard therapies exist The presence of at least one lesion that can be accurately assessed at baseline by Computerised Tomography (CT), Magnetic Resonance Imaging (MRI) or plain X-ray and is suitable for repeated assessment Estimated life expectancy of more than 12 weeks", "candidate_expression": "((Aged) AND (Computerised Tomography (CT)) AND (Estimated life expectancy) AND (Magnetic Resonance Imaging (MRI)) AND (accurately assessed at baseline) AND (at least 18 years) AND (at least one) AND (excluding) AND (for which no standard therapies exist) AND (lesion) AND (lymphoma) AND (more than 12 weeks) AND (plain X-ray) AND (resistance to standard therapies) AND (solid, malignant tumour) AND (suitable for repeated assessment))"}
{"candidate_id": "LLM03444", "doc_id": "NCT02380118_exc", "case_bucket": "or", "source_criterion": "known hypersensitivity or contraindication to the study drugs reversible aetiology for agitation (e.g. hypotension, hypoxia, hypoglycaemia) known pregnancy acute alcohol withdrawal patients aged>75 years.", "candidate_expression": "((acute alcohol withdrawal) AND (aged >75 years) AND (agitation) AND (pregnancy) AND (reversible aetiology) AND (study drugs) AND ((contraindication) OR (hypersensitivity)) AND ((hypoglycaemia) OR (hypotension) OR (hypoxia)))"}
{"candidate_id": "LLM03445", "doc_id": "NCT02992938_inc", "case_bucket": "other", "source_criterion": "Patients scheduled for thyroidectomy with general anesthesia in the University of Chile Clinical Hospital", "candidate_expression": "((University of Chile Clinical Hospita) AND (general anesthesia) AND (thyroidectomy scheduled for))"}
{"candidate_id": "LLM03446", "doc_id": "NCT02827487_exc", "case_bucket": "other", "source_criterion": "Previous vaginal delivery. Submucous myoma. Uterine anomalies. Undiagnosed vaginal bleeding. Pelvic inflammatory disease.", "candidate_expression": "((Pelvic inflammatory disease) AND (Submucous myoma) AND (Uterine anomalies) AND (vaginal bleeding Undiagnosed) AND (vaginal delivery Previous))"}
{"candidate_id": "LLM03447", "doc_id": "NCT02499185_exc", "case_bucket": "other", "source_criterion": "Ongoing acute kidney injury Stage 2/3 History of kidney transplant", "candidate_expression": "((Stage 2/3) AND (acute kidney injury) AND (kidney transplant History))"}
{"candidate_id": "LLM03448", "doc_id": "NCT02573909_exc", "case_bucket": "or", "source_criterion": "Planned surgery under regional anesthesia contraindication to the study drug contraindication to the lumbar puncture Contraindication to oxycodone Pregnancy or lactation no informed consent", "candidate_expression": "((Contraindication) AND (contraindication) AND (lumbar puncture) AND (oxycodone) AND (regional anesthesia) AND (study drug) AND (surgery Planned) AND ((Pregnancy) OR (lactation)))"}
{"candidate_id": "LLM03449", "doc_id": "NCT03476850_exc", "case_bucket": "or", "source_criterion": "Chronic pain or narcotic usage during the preceding 30 days Infection at or near the intended needle insertion site Complex or altered abdominal wall anatomy Weight <45kg", "candidate_expression": "((<45kg) AND (Infection) AND (Weight) AND (during the preceding 30 days) AND (intended needle insertion site) AND ((Chronic pain) OR (narcotic)) AND ((Complex abdominal wall anatomy) OR (altered abdominal wall anatomy)))"}
{"candidate_id": "LLM03450", "doc_id": "NCT00676273_exc", "case_bucket": "or", "source_criterion": "Patients: Who are pregnant or planning to become pregnant during the study or in the future With a elevated post-void residual (defined as PVR > 100cc) With a bleeding condition or on anti-coagulant therapy With immunosuppression (i.e. HIV, lymphoma) With multiple sclerosis or other progressive neurological disease With evidence of a local or systemic infection, including urinary tract infection With evidence of intrinsic sphincter deficiency as defined by a maximal urethral closure pressure of <20 cm H2O Previous sub-urethral sling Predominant overactive bladder symptoms", "candidate_expression": "((<20 cm H2O) AND (> 100cc) AND (HIV) AND (PVR) AND (Predominant) AND (Previous) AND (anti-coagulant therapy) AND (bleeding condition) AND (during the study) AND (elevated) AND (immunosuppression) AND (in the future) AND (intrinsic sphincter deficiency) AND (local infection) AND (lymphoma) AND (maximal urethral closure pressure) AND (multiple sclerosis) AND (overactive bladder) AND (overactive bladder symptoms) AND (planning to become) AND (post-void residual) AND (pregnant) AND (progressive neurological disease) AND (sub-urethral sling) AND (systemic infection) AND (urinary tract infection))"}
```
