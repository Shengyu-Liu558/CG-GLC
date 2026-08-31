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
{"candidate_id": "LLM00076", "doc_id": "NCT02862912_inc", "case_bucket": "or", "source_criterion": "ASA I and II women 18-45 yrs old Singleton pregnancy Cervical cerclage 1st or 2nd trimester of pregnancy undergoing with spinal anesthesia Height 150 - 180 cm BMI = 40 kg/m2.", "candidate_expression": "((150 - 180 cm) AND (18-45 yrs) AND (= 40 kg/m2) AND (ASA) AND (BMI) AND (Cervical cerclage) AND (Height) AND (I and II) AND (Singleton pregnancy) AND (old) AND (pregnancy) AND (spinal anesthesia) AND (women) AND ((1st trimester) OR (2nd trimester)))"}
{"candidate_id": "LLM00077", "doc_id": "NCT02901106_exc", "case_bucket": "other", "source_criterion": "pregnant or breastfeeding woman patient with a measure of legal protection subject unaffiliated insurance", "candidate_expression": "((patient with a measure of legal protection) AND (pregnant or breastfeeding woman))"}
{"candidate_id": "LLM00078", "doc_id": "NCT03480607_inc", "case_bucket": "other", "source_criterion": "American society of anesthesiologist (ASA) physical status I or II", "candidate_expression": "((ASA) AND (American society of anesthesiologist physical status I or II))"}
{"candidate_id": "LLM00079", "doc_id": "NCT02315287_inc", "case_bucket": "or", "source_criterion": "HbA1c > 13.0 % No treatment with insulin or oral agents for 6 months 20 = Age < 80 years", "candidate_expression": "((Age 20 = < 80 years) AND (HbA1c > 13.0 %) AND (insulin) AND (oral agents) AND NOT (treatment))"}
{"candidate_id": "LLM00080", "doc_id": "NCT03231982_inc", "case_bucket": "other", "source_criterion": "Adult male and female aged 19 to 75 years Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.", "candidate_expression": "((19 to 75 years) AND (Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.) AND (aged) AND (female) AND (male))"}
{"candidate_id": "LLM00081", "doc_id": "NCT03263481_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00082", "doc_id": "NCT02592980_exc", "case_bucket": "or", "source_criterion": "Patients will not be included if they have reached a stable dose of warfarin, liver dysfunction, alcoholism, use of another anticoagulant, use of chemotherapy, or if they do not meet the inclusion criteria", "candidate_expression": "((if they do not meet the inclusion criteria) AND ((alcoholism) OR (anticoagulant another) OR (chemotherapy) OR (liver dysfunction) OR (warfarin stable dose)))"}
{"candidate_id": "LLM00083", "doc_id": "NCT01346436_exc", "case_bucket": "other", "source_criterion": "Age <18 years old Patient unable to communicate or to understand the study Patient refusing to participate to the study contraindication to laparoscopy", "candidate_expression": "((<18 years old) AND (Age) AND (Patient refusing to participate to the study) AND (Patient unable to communicate or to understand the study) AND (contraindication) AND (laparoscopy))"}
{"candidate_id": "LLM00084", "doc_id": "NCT02431559_exc", "case_bucket": "or", "source_criterion": "1. Prior exposure to doxorubicin, PLD or any other anthracycline, motolimod and other TLR agonists, MEDI4736 or checkpoint inhibitors, such as anti-CTLA4 and anti-PD1/anti-PD-L1 antibodies. 2. Subjects with platinum-refractory disease, defined as disease progression while receiving first line platinum-based therapy. 3. Clinically significant persistent immune-related adverse events following prior therapy. 4. Subjects with history or evidence upon physical examination of CNS disease, including primary brain tumor, seizures not controlled with standard medical therapy, any brain metastases, or, within six months prior to Day 1 of this study, history of cerebrovascular accident (CVA, stroke), transient ischemic attack (TIA) or subarachnoid hemorrhage. 5. Subjects with clinically significant cardiovascular disease. This includes: 1. Resisted hypertension 2. Myocardial infarction or unstable angina within 6 months prior to Day 1 of the study. 3. History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation) or cardiac arrhythmias requiring anti-arrhythmic medications, except for atrial fibrillation that is well controlled with anti-arrhythmic medication. 4. Baseline ejection fraction ≤ 50% as assessed by echocardiogram or MUGA. 5. New York Heart Association (NYHA) Class II or higher congestive heart failure. 6. Grade 2 or higher peripheral ischemia, except for brief (< 24 hrs) episodes of ischemia managed non-surgically and without permanent deficit. 6. History of pneumonitis or interstitial lung disease. 7. Active, suspected or prior documented autoimmune disease (including inflammatory bowel disease, celiac disease, Wegner's granulomatosis, active Hashimoto's thyroiditis, rheumatoid arthritis, lupus, scleroderma and its variants, multiple sclerosis, myasthenia gravis). Vitiligo, type I diabetes mellitus, residual hypothyroidism due to autoimmune condition only requiring hormone replacement, psoriasis not requiring systemic treatment, or conditions not expected to recur in the absence of an external trigger are permitted. 8. Other malignancy within 2 years prior to Day 1 of the study, except for those treated with surgical intervention only. 9. Subjects with clinical symptoms or signs of gastrointestinal obstruction and/or who require drainage gastrostomy tube and/or parenteral hydration or nutrition. 10. Known immunodeficiency or HIV, Hepatitis B or Hepatitis C positivity. 11. History of severe allergic reactions to any unknown allergens or components of the study drugs. 12. Other serious illnesses (e.g., serious infections requiring antibiotics, bleeding disorders). 13. Prior treatment in any other interventional clinical trial within 4 weeks prior to Day 1 of the study. 14. Mental impairment that may compromise compliance with the requirements of the study. 15. Lack of availability for immunological and clinical follow-up assessment. 16. Women who are breastfeeding or pregnant as evidenced by positive serum pregnancy test 17. Subjects unwilling to use acceptable methods of contraception. -Female subjects should refrain from breastfeeding throughout this period. 18. Any condition that, in the clinical judgment of the treating physician, is likely to prevent the subject from complying with any aspect of the protocol or that may put the subject at unacceptable risk. 19. Subjects must not donate blood while on study and for at least 90 days following the last MEDI4736 treatment. 20. History of allogeneic organ transplant", "candidate_expression": "((2 or higher) AND (< 24 hrs) AND (Baseline) AND (CNS disease) AND (Class II or higher) AND (Clinically significant) AND (Day 1 of the study) AND (Day 1 of this study) AND (Female) AND (Grade 2 or higher) AND (History) AND (Lack of) AND (Mental impairment) AND (New York Heart Association (NYHA)) AND (Prior) AND (Resisted hypertension) AND (Women) AND (acceptable) AND (allergic reactions) AND (allogeneic organ transplant) AND (anti-arrhythmic medication) AND (anti-arrhythmic medications) AND (atrial fibrillation) AND (autoimmune disease) AND (availability for) AND (breastfeeding) AND (brief) AND (cardiovascular disease) AND (clinically significant) AND (compromise compliance) AND (congestive heart failure) AND (contraception) AND (controlled) AND (disease progression) AND (donate blood) AND (due to autoimmune condition) AND (ejection fraction) AND (except) AND (except for) AND (first line platinum-based therapy) AND (following prior therapy) AND (for at least 90 days following the last MEDI4736 treatment) AND (hormone replacement) AND (illnesses) AND (immune-related adverse events) AND (ischemia) AND (malignancy) AND (non) AND (not) AND (not expected to recur) AND (on study) AND (peripheral ischemia) AND (permanent deficit) AND (persistent) AND (platinum-refractory disease) AND (positive) AND (prior therapy) AND (refrain from) AND (requiring anti-arrhythmic medications) AND (requiring hormone replacement) AND (requiring systemic treatment) AND (serious) AND (serum pregnancy test) AND (severe) AND (standard medical therapy) AND (surgical intervention) AND (surgically) AND (systemic treatment) AND (the last MEDI4736 treatment) AND (this period) AND (those) AND (throughout this period.) AND (to any unknown allergens or components of the study drugs) AND (treatment) AND (unwilling) AND (well controlled with anti-arrhythmic medication) AND (while on study) AND (while receiving first line platinum-based therapy) AND (within 2 years prior to Day 1 of the study) AND (within 6 months prior to Day 1 of the study) AND (within six months prior to Day 1 of this study) AND (without) AND (≤ 50%) AND ((interstitial lung disease) OR (pneumonitis)) AND ((Hashimoto's thyroiditis) OR (Wegner's granulomatosis) OR (celiac disease) OR (inflammatory bowel disease) OR (lupus) OR (multiple sclerosis) OR (myasthenia gravis) OR (rheumatoid arthritis) OR (scleroderma) OR (scleroderma variants)) AND ((Vitiligo) OR (residual hypothyroidism) OR (type I diabetes mellitus)) AND ((autoimmune condition) OR (conditions) OR (psoriasis)) AND ((clinical symptoms of gastrointestinal obstruction) OR (drainage gastrostomy tube) OR (parenteral hydration) OR (parenteral nutrition) OR (signs of gastrointestinal obstruction)) AND ((HIV) OR (Hepatitis B) OR (Hepatitis C) OR (immunodeficiency)) AND ((bleeding disorders) OR (infections requiring antibiotics)) AND ((breastfeeding) OR (pregnant)) AND ((clinical follow-up assessment) OR (immunological follow-up assessment)) AND ((MEDI4736) OR (PLD) OR (TLR agonists) OR (anthracycline) OR (checkpoint inhibitors) OR (doxorubicin) OR (motolimod)) AND ((anti-CTLA4) OR (anti-PD-L1 antibodies) OR (anti-PD1 antibodies)) AND ((brain metastases) OR (primary brain tumor) OR (seizures)) AND ((cerebrovascular accident) OR (subarachnoid hemorrhage) OR (transient ischemic attack (TIA))) AND ((CVA) OR (stroke)) AND ((Myocardial infarction) OR (unstable angina)) AND ((ventricular fibrillation) OR (ventricular tachycardia)) AND ((cardiac arrhythmias) OR (ventricular arrhythmia)) AND ((MUGA) OR (echocardiogram)))"}
{"candidate_id": "LLM00085", "doc_id": "NCT02406885_inc", "case_bucket": "or", "source_criterion": "Men or women, 18 to 65 years old with a BMI of 35 kg/m2 or greater who will be undergoing bariatric surgery (VSG and RYGB) Signed written informed consent Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug Women must not be breastfeeding", "candidate_expression": "((BMI 35 kg/m2 or greater) AND (Men) AND (RYGB) AND (Signed written informed consent) AND (VSG) AND (Women must not be breastfeeding) AND (Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug) AND (bariatric surgery) AND (old 18 to 65 years) AND (women))"}
{"candidate_id": "LLM00086", "doc_id": "NCT02780427_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitive reaction to dexmedetomidine Organ dysfunction, and significant developmental delays or behavior problems Cardiac arrhythmia Known. acyanotic congenital heart disease or children after cardiac interventional procedures for follow-up examination.", "candidate_expression": "((Cardiac arrhythmia) AND (Organ dysfunction) AND (acyanotic congenital heart disease) AND (allergy) AND (behavior problems) AND (cardiac interventional procedures for follow-up examination) AND (children after cardiac interventional procedures cardiac interventional procedures) AND (developmental delays significant) AND (dexmedetomidine) AND (follow-up examination) AND (hypersensitive))"}
{"candidate_id": "LLM00087", "doc_id": "NCT03017053_inc", "case_bucket": "or", "source_criterion": "Ability to understand and the willingness to sign a written informed consent document Age= 18 and= 75 years Clinical/ Histological/ cytological/ Imaging examination proven Oral/Oropharynx Squamous-cell carcinoma (Tongue, buccal mucosa, mouth floor, hard palate, Molar area), the depth of invasion > 4mm in preoperative assessment In line with clinical stage I / II stage (T1-2 N0 M0; AJCC 2010) and receiving surgical resection KPS= 70 Normal bone marrow reserve function and normal liver, kidney function Expected survival period= 6 months", "candidate_expression": "((0) AND (1-2) AND (= 18 and= 75 years) AND (= 6 month) AND (= 70) AND (> 4mm) AND (Ability to understand and the willingness to sign a written informed consent document) AND (Age) AND (Clinical examination) AND (Expected survival period) AND (Histological examination) AND (Imaging examination) AND (KPS) AND (M) AND (Molar area) AND (N) AND (Normal) AND (Oral) AND (Oropharynx) AND (Squamous-cell carcinoma) AND (T) AND (Tongue) AND (bone marrow reserve function) AND (buccal mucosa) AND (clinical stage I) AND (clinical stage II) AND (cytological examination) AND (depth of invasion) AND (hard palate) AND (kidney function) AND (liver function) AND (mouth floor) AND (normal) AND (preoperative assessment) AND (surgical resection))"}
{"candidate_id": "LLM00088", "doc_id": "NCT02632266_exc", "case_bucket": "or", "source_criterion": "Newborn infants <28 weeks and >34 weeks gestation, those with life threatening illness, congenital and chromosomal anomalies, gastrointestinal anomalies or necrotizing enterocolitis and fed premature formula", "candidate_expression": "((Newborn infants) AND (anomalies congenital) AND (chromosomal anomalies) AND (fed premature formula) AND (gastrointestinal anomalies) AND (gestation <28 weeks and >34 weeks) AND (life threatening illness) AND (necrotizing enterocolitis))"}
{"candidate_id": "LLM00089", "doc_id": "NCT01824537_inc", "case_bucket": "other", "source_criterion": "Couple must have been in a new relationship that started no more than six months prior to study entry Both partners plan on remaining in Montreal for at least 1 year Plan on having continued sexual contact with partner Be willing to comply with study procedures", "candidate_expression": "((Be willing to comply with study procedures) AND (Plan on) AND (for at least 1 year) AND (having continued sexual contact with partner) AND (new relationship) AND (no more than six months prior to study entry) AND (plan on) AND (remaining in Montreal))"}
{"candidate_id": "LLM00090", "doc_id": "NCT01728194_exc", "case_bucket": "or", "source_criterion": "Psychotic depression by DSM-IV, i.e., presence of delusions with a SCID-R score higher than 2; High suicide risk, i.e. intent or plan to attempt suicide in near future; Presence of any Axis I psychiatric disorder (other than unipolar major depression) or substance abuse; History of psychiatric disorders other than unipolar major depression or generalized anxiety disorder (bipolar disorder, hypomania, and dysthymia are exclusion criteria); Dementia: Diagnosis of dementia by DSM-IV; Mild Cognitive Impairment (MCI); Acute or severe medical illness, i.e., delirium, metastatic cancer, decompensated cardiac, liver or kidney failure, major surgery, stroke or myocardial infarction during the three months prior to entry; or use of drugs known to cause depression, e.g., reserpine, alpha-methyl-dopa, steroids, sympathomimetics withdrawal; Neurological brain disease and/or history of electroconvulsive therapy; History of any use of citalopram or escitalopram during the current episode or need for drugs that may interact with these agents, i.e. drug metabolized by the 2D6 P450 isoenzyme system; Current involvement in psychotherapy; Contraindications to MRI scanning including cardiac pacemaker, metallic objects and metallic implants contraindicating MRI, cardiac stent, claustrophobia; Inability to speak English; Corrected visual acuity < 20/70; Color blindness.", "candidate_expression": "((Color blindness) AND (Contraindications) AND (Dementia DSM-IV) AND (Inability to speak English) AND (MCI Acute severe) AND (MRI) AND (Mild Cognitive Impairment) AND (Psychotic depression DSM-IV) AND (SCID-R score higher than 2) AND (agents) AND (alpha-methyl-dopa) AND (attempt suicide in near future) AND (bipolar disorder) AND (brain disease Neurological) AND (cardiac failure) AND (cardiac pacemaker) AND (cardiac stent) AND (citalopram) AND (claustrophobia) AND (delirium) AND (delusions) AND (depression) AND (drugs) AND (drugs entry) AND (dysthymia) AND (electroconvulsive therapy) AND (episode current) AND (escitalopram) AND (generalized anxiety disorder) AND (hypomania) AND (kidney failure) AND (liver failure) AND (major surgery) AND (medical illness three months prior to entry) AND (metallic implants) AND (metallic objects) AND (metastatic cancer) AND (myocardial infarction) AND (psychiatric disorder Axis I) AND (psychiatric disorders) AND (psychotherapy) AND (reserpine) AND (steroids) AND (stroke) AND (substance abuse) AND (suicide risk High intent plan to) AND (sympathomimetics withdrawal) AND (unipolar major depression) AND (visual acuity Corrected < 20/70;) AND NOT (unipolar major depression))"}
{"candidate_id": "LLM00091", "doc_id": "NCT03339284_inc", "case_bucket": "other", "source_criterion": "patients with renal cancer coming to the laparoscopic radical nephrectomy", "candidate_expression": "((radical nephrectomy laparoscopic) AND (renal cancer))"}
{"candidate_id": "LLM00092", "doc_id": "NCT03216967_inc", "case_bucket": "other", "source_criterion": "Adult patients Kidney transplant recipients Patients treated by a calcineurin inhibitor and mycophenolic acid Viremia >= 3 log UI/ml Patients who have given written informed consent Negative pregnancy test (blood ß-HCG dosage)", "candidate_expression": "((Adult) AND (Kidney transplant) AND (Patients who have given written informed consent) AND (Viremia >= 3 log UI/ml) AND (blood ß-HCG dosage) AND (calcineurin inhibitor) AND (mycophenolic acid) AND (pregnancy test Negative))"}
{"candidate_id": "LLM00093", "doc_id": "NCT03036462_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to the active substance, to FCM or any of its excipients Known serious hypersensitivity to other parenteral iron products Anaemia not attributed to iron deficiency, e.g. other microcytic anaemia Evidence of iron overload or disturbances in the utilisation of iron", "candidate_expression": "((Anaemia) AND (FCM) AND (Hypersensitivity) AND (active substance) AND (attributed to) AND (disturbances in the utilisation of iron) AND (excipients) AND (hypersensitivity) AND (iron) AND (iron deficiency) AND (iron overload) AND (microcytic anaemia) AND (not) AND (other) AND (parenteral iron products) AND (serious))"}
{"candidate_id": "LLM00094", "doc_id": "NCT00379366_exc", "case_bucket": "other", "source_criterion": "contra-indications of radiotherapy angioplasty with stenting", "candidate_expression": "((angioplasty with stenting) AND (contra-indications) AND (radiotherapy))"}
{"candidate_id": "LLM00095", "doc_id": "NCT03083197_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to tetracycline, doxycycline or azithromycin Administration of doxycycline, azithromycin, chloramphenicol, rifampicin, or tetracycline during the preceding 7 days Pregnancy or breast-feeding Patients with myasthenia gravis or systemic lupus erythematosus Patients with an established infection (diagnostic test required) e.g. acute malaria, dengue, leptospirosis, typhoid, Japanese encephalitis etc. Current TB or TB treatment in = 6 months (contain active antibiotics against Orientia spp.) Current HAART use for HIV, long term use of immunosuppressants (e.g. steroids, chemotherapy, TNF-inhibitors and related agents) Patients with severe disease whom the clinical team feel their condition necessitates the need for additional scrub typhus treatment beyond the allocated antibiotic treatment assigned at randomization (e.g. IV chloramphenicol and/or PO/NG rifampicin)", "candidate_expression": "((HIV) AND (diagnostic test) AND (hypersensitivity) AND (infection) AND ((Pregnancy) OR (breast-feeding)) AND ((myasthenia gravis) OR (systemic lupus erythematosus)) AND ((Japanese encephalitis) OR (acute malaria) OR (dengue) OR (leptospirosis) OR (typhoid)) AND ((TB) OR (TB treatment in = 6 months)) AND ((HAART) OR (immunosuppressants long term use)) AND ((TNF-inhibitors) OR (chemotherapy) OR (steroids)) AND ((azithromycin) OR (doxycycline) OR (tetracycline)) AND ((azithromycin) OR (chloramphenicol) OR (doxycycline) OR (rifampicin) OR (tetracycline)))"}
{"candidate_id": "LLM00096", "doc_id": "NCT01715584_inc", "case_bucket": "other", "source_criterion": "age over 40 composite head and neck tumor resection treated hypertension hypertension medications taken on morning of surgery (except diuretics)", "candidate_expression": "((age over 40) AND (composite head and neck tumor resection) AND (hypertension medications on morning of surgery) AND (hypertension treated) AND NOT (diuretics))"}
{"candidate_id": "LLM00097", "doc_id": "NCT02301962_inc", "case_bucket": "or", "source_criterion": "Subject or subject's legally acceptable representative has provided informed consent. Male or female >=18 years of age. Histologically or cytologically confirmed diagnosis of adenocarcinoma of the colon or rectum. Wild-type KRAS (without mutation in exon 2 [codons 12 and 13], exon 3 [codons 59 and 61], and exon 4 [codons 117 and 146]) and wild-type NRAS (without mutation in exon 2 [codons 12 and 13], exon 3 [codons 59 and 61], and exon 4 [codons 117 and 146]) tumor status. Eastern Cooperative Oncology Group (ECOG) performance status of 0, 1 or 2. Measurable or non-measurable disease per RECIST Version 1.1. Must have failed after fluoropyrimidine-, oxaliplatin-, and irinotecan-containing chemotherapy regimens for metastatic disease. Failure is defined as either disease progression (clinical or radiological) or intolerance to the regimen. Metastatic relapse within 6 months after completing adjuvant chemotherapy (with either an irinotecan or oxaliplatin containing regimen) will also be considered as treatment failure of a prior regimen for metastatic disease. Laboratory: Adequate baseline organ function defined by (<=7 days prior to first dose of study treatment). Hematologic function, as follows: Absolute neutrophil count (ANC) >=1.5 x 10^9/Liter (L), Platelet count >=75 x 10^9/L, Hemoglobin >=8.0 gram/deciliter (g/dL). Renal function, as follows: Creatinine <=1.5 x upper limit of normal (ULN). Hepatic function, as follows: Aspartate aminotransferase (AST) <=3 x ULN, Alanine aminotransferase (ALT) <=3 x ULN, Total Bilirubin <=1.5 x ULN. Metabolic function, as follows: Serum Magnesium within normal limits. Serum Calcium within normal limits. Serum Potassium within normal limits. All prior treatment related toxicities common terminology criteria for adverse events (CTCAE) version 4.03 <=Grade 1 at the time of enrollment. Women of childbearing potential must have a negative serum pregnancy test within 7 days of first dose of study treatment and agree to use adequate contraception, during the study and for 2 months following the last dose of study treatment. Men with a female partner of childbearing potential must have either had a prior vasectomy or agree to use adequate contraception, from time of signing informed consent until 5 months after the last dose of study treatment.", "candidate_expression": "((Adequate baseline organ function <=7 days prior to first dose of study treatment) AND (Alanine aminotransferase (ALT) <=3 x ULN) AND (Creatinine <=1.5 x upper limit of normal (ULN)) AND (Eastern Cooperative Oncology Group (ECOG) performance status 0, 1 or 2) AND (RECIST Version 1.1) AND (Serum Calcium within normal limits) AND (Serum Magnesium within normal limits) AND (Serum Potassium within normal limits) AND (Subject or subject's legally acceptable representative has provided informed consent.) AND (Total Bilirubin <=1.5 x ULN) AND (Women of childbearing potential must have a negative serum pregnancy test within 7 days of first dose of study treatment and agree to use adequate contraception, during the study and for 2 months following the last dose of study treatment. Men with a female partner of childbearing potential must have either had a prior vasectomy or agree to use adequate contraception, from time of signing informed consent until 5 months after the last dose of study treatment.) AND (adenocarcinoma) AND (age >=18 years) AND (metastatic disease) AND (spartate aminotransferase (AST) <=3 x ULN) AND (the regimen after completing adjuvant chemotherapy) AND ((colon) OR (rectum)) AND ((Measurable disease) OR (non-measurable disease)) AND ((Male) OR (female)) AND ((fluoropyrimidine- containing chemotherapy) OR (irinotecan-containing chemotherapy) OR (oxaliplatin- containing chemotherapy)) AND ((Metastatic relapse within 6 months after completing adjuvant chemotherapy) OR (disease progression) OR (intolerance)) AND ((irinotecan containing regimen) OR (oxaliplatin containing regimen)) AND ((Absolute neutrophil count (ANC) >=1.5 x 10^9/Liter (L)) OR (Hemoglobin >=8.0 gram/deciliter (g/dL)) OR (Platelet count >=75 x 10^9/L)) AND ((Histologically) OR (cytologically)))"}
{"candidate_id": "LLM00098", "doc_id": "NCT03320057_inc", "case_bucket": "or", "source_criterion": "Women seeking medication abortion through 70 days gestation Eligible for Mifeprex(r) at a study clinical site English or Spanish speaking Willing and able to participate in the study, including willing to go to the study pharmacy to obtain mifepristone", "candidate_expression": "((Eligible for) AND (English speaking) AND (Mifeprex(r)) AND (Spanish speaking) AND (Willing and able to participate in the study) AND (Women) AND (medication abortion) AND (mifepristone) AND (study clinical site) AND (through 70 days gestation) AND (to obtain) AND (willing to go to the study pharmacy))"}
{"candidate_id": "LLM00099", "doc_id": "NCT03228654_inc", "case_bucket": "or", "source_criterion": "uterine size <12 weeks. presence of benign cause for the hysterectomy e.g. fibroid uterus, perimenopausal beeding not responding to medical treatment or complex endometrial hyperplasia without atypia. Absence of significant scarring in the pelvis from previous surgeries.", "candidate_expression": "((benign cause) AND (hysterectomy) AND (medical treatment) AND (surgeries previous) AND (uterine size <12 weeks) AND NOT (atypia) AND NOT (significant scarring pelvis from previous surgeries) AND ((complex endometrial hyperplasia) OR (fibroid uterus) OR (perimenopausal beeding responding to medical treatment)))"}
{"candidate_id": "LLM00100", "doc_id": "NCT01567605_inc", "case_bucket": "other", "source_criterion": "traumatic spinal cord injury at least one year ago regular bowel care routine (at least four weeks)", "candidate_expression": "((regular bowel care routine at least four weeks) AND (traumatic spinal cord injury at least one year ago))"}
```
