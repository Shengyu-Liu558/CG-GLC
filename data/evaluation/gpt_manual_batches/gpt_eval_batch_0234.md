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
{"candidate_id": "LLM05826", "doc_id": "NCT02498483_inc", "case_bucket": "other", "source_criterion": "Apgar score at 5 minutes >7 birthweight greater than 2.4 kg Age of at least 10 hours At least one void.", "candidate_expression": "((Age at least 10 hours) AND (Apgar score at 5 minutes >7) AND (birthweight greater than 2.4 kg) AND (void At least one))"}
{"candidate_id": "LLM05827", "doc_id": "NCT03355326_inc", "case_bucket": "other", "source_criterion": "Diagnosis of uncomplicated gastroschisis Gestational age >33 weeks at time of delivery Weight >1900g at time of delivery Transfer of patient to Riley Hospital for Children prior to any abdominal surgery", "candidate_expression": "((Gestational age >33 weeks at time of delivery) AND (Riley Hospital for Children) AND (Transfer prior to any abdominal surgery) AND (Weight >1900g at time of delivery) AND (abdominal surgery) AND (gastroschisis uncomplicated))"}
{"candidate_id": "LLM05828", "doc_id": "NCT03430284_inc", "case_bucket": "other", "source_criterion": "35-75 years old; diagnosed as type 2 diabetes according to the criteria of the World Health Organization in 1999.", "candidate_expression": "((35-75 years old) AND (criteria of the World Health Organization in 1999) AND (old) AND (type 2 diabetes))"}
{"candidate_id": "LLM05829", "doc_id": "NCT02590315_exc", "case_bucket": "other", "source_criterion": "Personal history of breast cancer A terminal illness Patients who are unable to give informed consent Breast implants", "candidate_expression": "((Breast implants) AND (Personal history) AND (breast cancer) AND (terminal illness) AND (unable to give informed consent))"}
{"candidate_id": "LLM05830", "doc_id": "NCT02645474_inc", "case_bucket": "or", "source_criterion": "adult patients ASA class 1 to 3 patients patients scheduled for elective breast mastectomy or quadrantectomy", "candidate_expression": "((ASA class 1 to 3) AND (adult) AND ((breast quadrantectomy) OR (mastectomy)))"}
{"candidate_id": "LLM05831", "doc_id": "NCT02782702_exc", "case_bucket": "or", "source_criterion": "Hypersensibility to toxin or excipients Myastheny Deglutition's problems Past medical history of dysphagia or aspiration pneumonia Pregnancy (positive B-HCG test performed a maxima 72h before) or breastfeeding Mental , physical incapacity to fill in the questionnaires Guardianship patients Skin infections at the inclusion visit Application in the last 7 days at the site of injection of local treatments (apart emollients or antiseptics) or injections of botulism toxin or dynamic phototherapy or laser in the last 6 months. Systemic treatment with aminosides in the last 15 days Inclusion in another study in the last 2 months.", "candidate_expression": "((Application of local treatments) AND (B-HCG test) AND (Deglutition's problems) AND (Hypersensibility) AND (Inclusion in another study) AND (Myastheny) AND (Past medical history) AND (Skin infections) AND (Systemic treatment) AND (a maxima 72h before) AND (aminosides) AND (apart) AND (at the inclusion visit) AND (botulism toxin) AND (fill in the questionnaires) AND (in the last 15 days) AND (in the last 2 months) AND (in the last 6 months) AND (in the last 7 days) AND (inclusion visit) AND (positive) AND ((aspiration pneumonia) OR (dysphagia)) AND ((Pregnancy) OR (breastfeeding)) AND ((Mental incapacity) OR (physical incapacity)) AND ((antiseptics) OR (emollients)) AND ((excipients) OR (toxin)) AND ((dynamic phototherapy) OR (injections) OR (laser)))"}
{"candidate_id": "LLM05832", "doc_id": "NCT01895946_inc", "case_bucket": "or", "source_criterion": "Aged at least 18 years The presence of a solid, malignant tumour, excluding lymphoma, that is resistance to standard therapies or for which no standard therapies exist The presence of at least one lesion that can be accurately assessed at baseline by Computerised Tomography (CT), Magnetic Resonance Imaging (MRI) or plain X-ray and is suitable for repeated assessment Estimated life expectancy of more than 12 weeks", "candidate_expression": "((Aged) AND (Estimated life expectancy) AND (accurately assessed at baseline) AND (at least 18 years) AND (at least one) AND (excluding) AND (lesion) AND (lymphoma) AND (more than 12 weeks) AND (solid, malignant tumour) AND (suitable for repeated assessment) AND ((Computerised Tomography (CT)) OR (Magnetic Resonance Imaging (MRI)) OR (plain X-ray)) AND ((for which no standard therapies exist) OR (resistance to standard therapies)))"}
{"candidate_id": "LLM05833", "doc_id": "NCT02562456_inc", "case_bucket": "or", "source_criterion": "Children aging between 3 and 6 years presenting good health conditions whose parents or legal guardians accept and sign the consent form with at least one occlusal or occlusal proximal caries lesion in primary molars only occlusal and/or occlusal-proximal surfaces with caries lesions with dentin involvement", "candidate_expression": "((Children) AND (aging between 3 and 6 years) AND (caries lesion at least one primary molars occlusal occlusal proximal occlusal surfaces occlusal-proximal surfaces) AND (caries lesions) AND (dentin involvement) AND (good health conditions) AND (whose parents or legal guardians accept and sign the consent form))"}
{"candidate_id": "LLM05834", "doc_id": "NCT02441179_inc", "case_bucket": "or", "source_criterion": "1. Patients ≥ 18 years-old from \"Instituto Teletón Santiago\" and \"Hospital Clínico Mutual de seguridad\". 2. C5 to T12 spinal cord injury, classified as ISNCSCI grades C and D 3. Traumatic and non-traumatic, non-progressive lesions 4. Onset > 6 months 5. Ability to ambulate with or without assistive devices 6. Ability to follow verbal or visual commands 7. Signed informed consent", "candidate_expression": "((Ability to ambulate with assistive devices) AND (Ability to ambulate without assistive devices) AND (Ability to follow verbal commands) AND (Ability to follow visual commands) AND (Hospital Clínico Mutual de seguridad) AND (ISNCSCI grades C and D) AND (Instituto Teletón Santiago) AND (Signed informed consent) AND (lesions Traumatic non-traumatic non-progressive Onset > 6 months) AND (spinal cord injury C5 to T12) AND (years-old ≥ 18 years))"}
{"candidate_id": "LLM05835", "doc_id": "NCT01116882_inc", "case_bucket": "or", "source_criterion": "1. Subject is at least 18 years old. 2. Subject requires single- or multi-vessel percutaneous coronary intervention (PCI) of de novo or restenotic target lesion (including in-stent restenotic lesions). 3. Subject's lesion(s) is (are) amenable to stent treatment with currently available FDA-approved bare metal or drug eluting stents. 4. Subject is an acceptable candidate for elective, urgent or emergency coronary artery bypass graft (CABG). 5. Subject has clinical evidence of ischemic heart disease in terms of a positive functional study, or documented symptoms. 6. Documented stable angina pectoris [Canadian Cardiovascular Society Classification (CCS) 1, 2, 3, or 4], unstable angina pectoris with documented ischemia (Braunwald Class IB-C, IIB-C, or IIIB-C), non-ST segment elevation myocardial infarction, or documented silent ischemia. 7. Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm. 8. Subject and the treating physician agree that the subject will comply with all follow-up evaluations. 9. Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site. 10. The target lesion(s) is (are) de novo or restenotic (including in-stent restenotic) native coronary artery lesion(s) with greater than 50 and less than 100% stenosis (visual estimate), or the target lesion is an acute (less than 1 month) total occlusion as evidenced by clinical symptoms. 11. Target lesions(s) is (are) located in an infarct (if not treated with primary PCI) or non-infarct-related artery with a 70% or greater stenosis (by visual estimate) more than 72 hours following the ST segment elevation myocardial infarction (STEMI). Lesions treated with PCI more than 72 hours following STEMI would be subject to the same protocol inclusion/exclusion criteria listed above and below with the exception that a target lesion of 70% or greater stenosis may be treated with or without symptoms or abnormal stress test).", "candidate_expression": "((Braunwald Class IB-C, IIB-C, or IIIB-C) AND (Canadian Cardiovascular Society Classification (CCS) 1, 2, 3, or 4) AND (SOS hospital) AND (ST segment elevation myocardial infarction (STEMI)) AND (Subject and the treating physician agree that the subject will comply with all follow-up evaluations.) AND (Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site.) AND (Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm.) AND (Target lesions) AND (amenable to stent treatment) AND (bare metal stents elective urgent) AND (coronary artery bypass graft (CABG) emergency) AND (coronary artery lesion) AND (drug eluting stents) AND (functional study positive) AND (in-stent restenotic lesions in-stent restenotic) AND (infarct in an infarct -related artery) AND (ischemia documented) AND (ischemic heart disease clinical evidence) AND (non-ST segment elevation myocardial infarction) AND (old at least 18 years single- vessel multi-vessel) AND (percutaneous coronary intervention (PCI) de novo restenotic) AND (percutaneous intervention willing able) AND (silent ischemia documented silent) AND (stable angina pectoris stable) AND (stenosis) AND (stenosis 70% or greater) AND (stenosis greater than 50 and less than 100%) AND (stenosis more than 72 hours following the ST segment elevation myocardial infarction (STEMI)) AND (target lesion) AND (target lesion acute less than 1 month) AND (target lesion de novo restenotic in-stent restenotic) AND (total occlusion clinical symptoms) AND (unstable angina pectoris unstable) AND NOT (primary PCI non-infarct-related artery))"}
{"candidate_id": "LLM05836", "doc_id": "NCT03480607_inc", "case_bucket": "other", "source_criterion": "American society of anesthesiologist (ASA) physical status I or II", "candidate_expression": "((ASA) AND (American society of anesthesiologist physical status) AND (I or II))"}
{"candidate_id": "LLM05837", "doc_id": "NCT03084588_inc", "case_bucket": "other", "source_criterion": "All patients presenting for elective shoulder arthroscopic procedures will be eligible for enrollment.", "candidate_expression": "(shoulder arthroscopic procedures elective)"}
{"candidate_id": "LLM05838", "doc_id": "NCT02868437_exc", "case_bucket": "or", "source_criterion": "History of curettage or other intrauterine surgery History of post-abortion complication or infection", "candidate_expression": "((History) AND (curettage) AND (intrauterine surgery) AND ((post-abortion complication) OR (post-abortion infection)))"}
{"candidate_id": "LLM05839", "doc_id": "NCT00050349_inc", "case_bucket": "or", "source_criterion": "Patients with biopsy-proven metastatic carcinoid tumors or other neuroendocrine tumors (Islet cell, Gastrinomas and VIPomas) with at least one measurable lesion (other than bone) that has either not been previously irradiated or if previously irradiated has demonstrated progression since the radiation therapy The patient has no major impairment of renal or hepatic function, as defined by the following laboratory parameters: total bilirubin <1.5 X ULN; AST, ALT<2.5X ULN (<5 X ULN if liver metastases are present) Patients on Sandostatin Lar (long acting somatostatin analogue) must be on a stable dose for 30 days prior to study entry and short acting somatostatin analogues must be judged to be on a clinically stable dose by the investigator prior to study entry Must have a life expectancy of greater than three (3) months Karnofsky Performance Status > 60 Female patients must have a negative serum pregnancy test at screening. (Not applicable to patients with bilateral oophorectomy and/or hysterectomy or to those patients who are postmenopausal.)", "candidate_expression": "((ALT <2.5X ULN <5 X ULN) AND (AST <2.5X ULN) AND (Female) AND (Gastrinomas) AND (Islet cell) AND (Karnofsky Performance Status > 60) AND (Sandostatin Lar stable dose) AND (VIPomas) AND (bilateral oophorectomy) AND (biopsy proven) AND (hysterectomy) AND (irradiated progression) AND (life expectancy greater than three (3) months) AND (liver metastases) AND (long acting somatostatin analogue) AND (major impairment of hepatic function) AND (major impairment of renal function) AND (measurable lesion bone) AND (metastatic carcinoid tumors) AND (other neuroendocrine tumors) AND (postmenopausal) AND (radiation therapy) AND (serum pregnancy test negative at screening) AND (short acting somatostatin analogues clinically stable dose) AND (total bilirubin <1.5 X ULN) AND NOT (irradiated))"}
{"candidate_id": "LLM05840", "doc_id": "NCT02283905_inc", "case_bucket": "scope", "source_criterion": "All adult patients 18 years of age or older admitted to the intensive care units of St. Boniface General Hospital with a diagnosis of acute pulmonary blastomycosis requiring mechanical ventilation.", "candidate_expression": "((18 years or older) AND (St. Boniface General Hospital) AND (acute pulmonary blastomycosis) AND (admitted) AND (adult) AND (age) AND (intensive care units) AND (mechanical ventilation))"}
{"candidate_id": "LLM05841", "doc_id": "NCT02900443_exc", "case_bucket": "or", "source_criterion": "Overlap syndrome with Primary Sclerosing Cholangitis (PSC) or Primary Biliary Cholangitis (PBC) (Paris criteria, strong positive Anti-Mitochondrial Antibodies (AMA), past liver biopsy or cholangiographic findings compatible with PBC or PSC). Presentation with acute liver failure, defined as presence of hepatic encephalopathy and coagulopathy (INR > 1.5) Current treatment with prednisone/prednisolone and/or immunosuppressive medication for an indication other than autoimmune hepatitis Current systemic infection Other clinically significant medical conditions that could interfere with the trial If female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures. History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain", "candidate_expression": "((> 1.5) AND (AMA) AND (Anti-Mitochondrial Antibodies) AND (History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate) AND (INR) AND (Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain) AND (Overlap syndrome) AND (PBC) AND (PSC) AND (Paris criteria,) AND (Primary Biliary Cholangitis) AND (Primary Sclerosing Cholangitis) AND (acute liver failure) AND (autoimmune hepatitis) AND (cholangiographic findings) AND (coagulopathy) AND (f female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures) AND (hepatic encephalopathy) AND (immunosuppressive medication) AND (indication) AND (liver biopsy) AND (other) AND (prednisolone) AND (prednisone) AND (strong positive) AND (systemic infection))"}
{"candidate_id": "LLM05842", "doc_id": "NCT02765217_exc", "case_bucket": "or", "source_criterion": "Receiving antibiotic and/or probiotic, 8 weeks before the study Chronic gastrointestinal system disorders Congenital anomalies Chronic diseases Chemotherapy and radiotherapy Pregnancy", "candidate_expression": "((8 weeks before the study) AND (Chemotherapy) AND (Chronic diseases) AND (Chronic gastrointestinal system disorders) AND (Congenital anomalies) AND (Pregnancy) AND (antibiotic) AND (probiotic) AND (radiotherapy) AND (the study))"}
{"candidate_id": "LLM05843", "doc_id": "NCT00397215_exc", "case_bucket": "or", "source_criterion": "Administration of the licensed MF59-containing vaccines, e.g. Fluad™ or Addigrip™ or virosome-based influenza vaccines such as Inflexal V™, InfectoVac Flu™ or Invivac™ during the 2006-2007 influenza season. Administration of licensed vaccines within 2 weeks (for inactivated vaccines) or 4 weeks (for live vaccines) prior to enrolment in this study. Planned administration of a vaccine not foreseen by the study protocol up to 30 days after the second vaccination with H5N1 vaccine. Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first administration of the study vaccine. Any confirmed or suspected immunosuppressive or immunodeficient condition, based on medical history and physical examination (no laboratory testing required). History of chronic alcohol consumption and/or drug abuse. History of hypersensitivity to vaccines. History of allergic disease or reactions likely to be exacerbated by any component of the vaccine (including egg and thiomersal allergy). Acute clinically significant pulmonary, cardiovascular, hepatic or renal functional abnormality, as determined by physical examination or laboratory screening tests. Acute disease at the time of enrolment. Serious chronic disease including any medically significant chronic pulmonary, cardiovascular, renal, neurological, psychiatric or metabolic disorder, as determined by medical history and physical examination. Administration of immunoglobulins and/or any blood products within the three months preceding the first vaccination or during the study. Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days prior to the first vaccination, or planned use during the study period. Any condition which, in the opinion of the investigator, prevents the subject from participation in the study.", "candidate_expression": "((Acute disease at the time of enrolment) AND (Addigrip) AND (Fluad) AND (H5N1 vaccine more than 14 days) AND (History) AND (InfectoVac Flu) AND (Inflexal V) AND (Invivac) AND (MF59-containing vaccines) AND (allergic disease) AND (allergic reactions) AND (any blood products within the three months preceding the first vaccination) AND (cardiovascular functional abnormality) AND (chronic alcohol consumption) AND (chronic cardiovascular disorder) AND (chronic disease Serious) AND (chronic metabolic disorder) AND (chronic neurological disorder) AND (chronic psychiatric disorder) AND (chronic pulmonary disorder) AND (chronic renal disorder) AND (condition which prevents the subject from participation in the study) AND (drug) AND (drug abuse) AND (egg allergy) AND (hepatic functional abnormality) AND (hypersensitivity to vaccines) AND (immunodeficient condition) AND (immunoglobulins) AND (immunosuppressants) AND (immunosuppressive condition confirmed suspected) AND (inactivated vaccines within 2 weeks prior to enrolment in this study) AND (licensed vaccines) AND (live vaccines within 4 weeks prior to enrolment in this study) AND (not) AND (other immune-modifying drugs) AND (product other than the study vaccine(s) within 30 days prior to the first vaccination non-registered) AND (pulmonary functional abnormality) AND (renal functional abnormality) AND (thiomersal allergy) AND (use planned during the study period) AND (vaccination) AND (vaccination first) AND (vaccination first during the study investigational) AND (vaccine) AND (vaccine foreseen by the study protocol up to 30 days) AND (virosome-based influenza vaccines) AND NOT (study vaccine(s)))"}
{"candidate_id": "LLM05844", "doc_id": "NCT02630628_inc", "case_bucket": "or", "source_criterion": "Biopsy-proven LN Class III/IV±V (ISN/RPS 2003), with biopsy performed within 12 weeks of randomization. Positive anti-dsDNA. Active LN with proteinuria (urine protein/creatinine ratio >1.0 or 24-hr urine protein >1.0 g at baseline), with or without hematuria. Both 'incident' (i.e. new) patients and 'flare' patients can be included.", "candidate_expression": "((LN Active) AND (LN Class III/IV±V) AND (anti-dsDNA Positive) AND (biopsy within 12 weeks) AND (hematuria) AND (proteinuria) AND ((24-hr urine protein >1.0 g) OR (urine protein/creatinine ratio >1.0)))"}
{"candidate_id": "LLM05845", "doc_id": "NCT03033745_exc", "case_bucket": "other", "source_criterion": "Ongoing serious bacterial infections at the time of screening. Other significant medical conditions that could increase the risk to the subject. Females who are pregnant, breast feeding, or planning a pregnancy during the course study. Participation in a study with an Investigational Medicinal Product (IMP) other than IgPro20 within three months prior to enrollment.", "candidate_expression": "((Females who are pregnant, breast feeding, or planning a pregnancy during the course study.) AND (bacterial infections serious at the time of screening))"}
{"candidate_id": "LLM05846", "doc_id": "NCT03208998_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Psychiatric disease) AND (autoimmune hepatitis) AND (consumption of alcohol) AND (drugs consumption of) AND (hepatitis C virus) AND (hepatitis D virus) AND (human immunodeficiency virus) AND (neoplastic diseases liver))"}
{"candidate_id": "LLM05847", "doc_id": "NCT02509949_exc", "case_bucket": "or", "source_criterion": "Patients with a history of drug abuse; preoperative history of schizophrenia, epilepsy, parkinsonism, use of cholinesterase inhibitor, inability to communicate in the preoperative period (coma, profound dementia, or language barrier).", "candidate_expression": "((cholinesterase inhibitor) AND (drug abuse) AND (epilepsy) AND (history) AND (inability to communicate) AND (language barrier) AND (parkinsonism) AND (preoperative) AND (schizophrenia) AND ((coma) OR (profound dementia)))"}
{"candidate_id": "LLM05848", "doc_id": "NCT03472508_exc", "case_bucket": "or", "source_criterion": "(1)Women who are pregnant and/or lactating; or women who intend to conceive within a year; (2)History of allergies to enalapril, folic acid or other components of the compound drug; (3)History of adverse reactions or intolerance to enalapril or other ACE inhibitors, or drugs or supplements containing folic acid; (4)Diagnosis or suspicion of secondary hypertension; (5)Known serious medical conditions, including: Cardiovascular: patients with clinically diagnosed cardiac dysfunction (NYHA class III and above), hypertrophic obstructive cardiomyopathy, clinically significant valvular heart disease, acute coronary syndrome within the last 3 months, or percutaneous coronary intervention (PCI), or coronary artery bypass graft (CABG); or abnormal pre-enrollment ECG test results with clinically significant arrhythmias (atrial flutter, atrial fibrillation, grade II-III atrioventricular block, etc.); Digestive: a previous diagnosis of various types of viral hepatitis that are still in the active phase; abnormal pre-enrollment liver function test results (ALT, AST, GGT, TBIL, or DBIL 3 times higher than normal, ALB = 30g/L); gastrectomy and/or gastrojejunostomy; gastrointestinal dysfunction; Urinary: pre-enrollment serum creatinine greater than 200umol/L; clinical diagnosis of renal artery stenosis, isolated kidney, kidney transplantation and/or other diseases; Endocrine: type 1 diabetes or uncontrolled type 2 diabetes (fasting blood glucose above 11.1 mmol/L at pre-enrollment); previous diagnosis of hyperthyroidism and failure to correct; Respiratory: pulmonary heart disease; chronic obstructive pulmonary disease; Neuropsychiatric: recent transient ischemic attack or stroke (within the last 3 months); peripheral or severe autonomic dysfunction; mental or nervous system dysfunction, inability to express desire; known drug or alcohol dependence; Malignancy, malnutrition, hematopoietic disorders and other serious diseases. (6)Significant signs of abnormalities as seen in laboratory tests or physical characteristics, which, at the discretion of the investigators, indicates that the patient is experiencing a serious illness or, may affect the observation and evaluation of the drug's efficacy or adverse events, or renders the patient unsuitable for participating in this study; (7)Patients currently taking folate, B12, or B6, or any compounds containing them, who express an inability or a refusal to stop usage; (8)Regular usage of folic acid supplements or compounds containing folic acid in the past 3 months; (9)Participation in a clinical trial for a drug that has not yet been officially approved for marketing within one month prior to the first visit.", "candidate_expression": "((ALB = 30g/L) AND (NYHA class III and above) AND (Participation in a clinical trial within one month prior to the first visit) AND (Women) AND (allergies History) AND (arrhythmias clinically significant) AND (drug that has not yet been officially approved for marketing) AND (fasting blood glucose above 11.1 mmol/L at pre-enrollment) AND (intend to conceive within a year) AND (laboratory tests) AND (medical conditions serious) AND (recent) AND (secondary hypertension) AND (signs of abnormalities Significant) AND (type 2 diabetes uncontrolled) AND (women) AND ((Malignancy) OR (alcohol dependence) OR (autonomic dysfunction) OR (chronic obstructive pulmonary disease) OR (drug dependence) OR (gastrectomy) OR (gastrointestinal dysfunction) OR (gastrojejunostomy) OR (hematopoietic disorders) OR (hyperthyroidism previous failure to correct) OR (inability to express desire) OR (isolated kidney) OR (kidney transplantation) OR (liver function test abnormal pre-enrollment) OR (malnutrition) OR (mental system dysfunction) OR (nervous system dysfunction) OR (pulmonary heart disease) OR (renal artery stenosis clinical diagnosis) OR (serum creatinine pre-enrollment greater than 200umol/L) OR (type 1 diabetes) OR (viral hepatitis previous active phase)) AND ((B12) OR (B6) OR (folate)) AND ((inability) OR (refusal to stop usage)) AND ((Regular usage) OR (in the past 3 months)) AND ((compounds containing folic acid) OR (folic acid supplements)) AND ((components of the compound drug) OR (enalapril) OR (folic acid)) AND ((adverse reactions) OR (intolerance)) AND ((ACE inhibitors other) OR (enalapril) OR (folic acid)) AND ((Diagnosis) OR (suspicion)) AND ((lactating) OR (pregnant)) AND ((ECG test abnormal pre-enrollment) OR (acute coronary syndrome within the last 3 months) OR (cardiac dysfunction clinically diagnosed) OR (coronary artery bypass graft (CABG)) OR (hypertrophic obstructive cardiomyopathy) OR (percutaneous coronary intervention (PCI)) OR (valvular heart disease clinically significant)) AND ((atrial fibrillation) OR (atrial flutter) OR (atrioventricular block)) AND ((grade II) OR (grade III)) AND ((ALT) OR (AST) OR (DBIL) OR (GGT) OR (TBIL)) AND ((stroke) OR (transient ischemic attack)) AND ((peripheral) OR (severe)))"}
{"candidate_id": "LLM05849", "doc_id": "NCT02430740_exc", "case_bucket": "other", "source_criterion": "polycystic ovaries untreated thyroid pathology hypogonadotropic hypogonadism untreaed hyperprolactinemia study drug hypersensitivity previous OHSS unilateral ovariectomy genital malformation BMI>40", "candidate_expression": "((>40) AND (BMI) AND (OHSS) AND (genital malformation) AND (hyperprolactinemia) AND (hypersensitivity) AND (hypogonadotropic hypogonadism) AND (ovariectomy) AND (polycystic ovaries) AND (previous) AND (study drug) AND (thyroid pathology) AND (unilateral) AND (untreaed) AND (untreated))"}
{"candidate_id": "LLM05850", "doc_id": "NCT03624517_inc", "case_bucket": "or", "source_criterion": "Adult males and females who are 18 years of age or older. Evidence or suspicion of upper gastrointestinal bleed (GIB) Patient with known or suspected cirrhosis Upper GIB secondary to bleeding esophageal varices as show by esophageal endoscopy, requiring endoscopic band ligation (EBL) at presentation Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so", "candidate_expression": "((18 years of age or older) AND (Adult) AND (Evidence) AND (Upper GIB) AND (Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so) AND (at presentation) AND (bleeding) AND (cirrhosis) AND (endoscopic band ligation (EBL)) AND (esophageal endoscopy) AND (esophageal varices) AND (females) AND (known) AND (males) AND (requiring) AND (secondary) AND (suspected) AND (suspicion) AND (upper gastrointestinal bleed (GIB)))"}
```
