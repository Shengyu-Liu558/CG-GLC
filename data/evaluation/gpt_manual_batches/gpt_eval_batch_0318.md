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
{"candidate_id": "LLM07926", "doc_id": "NCT03247413_inc", "case_bucket": "or", "source_criterion": "patients with a diagnosis of either cervical, thoracic, or lumbar facet or sacroiliac joint pain who have responded to medial branch blocks and are already scheduled for bilateral radiofrequency ablations age greater than 18 years old English speaking", "candidate_expression": "((English speaking) AND (age greater than 18 years old) AND (bilateral radiofrequency ablations scheduled for) AND (cervical joint pain) AND (lumbar facet joint pain) AND (medial branch blocks) AND (sacroiliac joint pain) AND (thoracic joint pain))"}
{"candidate_id": "LLM07927", "doc_id": "NCT03084588_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure requiring dialysis Poorly controlled pulmonary disease (severe asthma or COPD) -Contraindication to regional anesthesia (recent anticoagulant use) Sleep apnea or morbid obesity with possible sleep apnea Allergy to methadone Significant preoperative pain requiring treatment with high doses of opioids (more than 6-8 Norco tablets or equivalence per day) or recent history of opioid abuse", "candidate_expression": "((Allergy) AND (Contraindication) AND (Norco tablets) AND (Poorly controlled) AND (Preoperative) AND (Significant) AND (anticoagulant) AND (dialysis) AND (equivalence) AND (high doses) AND (history) AND (methadone) AND (more than 6-8 per day) AND (opioids) AND (possible) AND (pulmonary disease) AND (recent) AND (regional anesthesia) AND (renal failure) AND (requiring) AND (severe) AND (sleep apnea) AND ((Sleep apnea) OR (morbid obesity)) AND ((opioid abuse) OR (preoperative pain)) AND ((COPD) OR (asthma)))"}
{"candidate_id": "LLM07928", "doc_id": "NCT00061308_inc", "case_bucket": "or", "source_criterion": "Have had one prior platinum-based chemotherapy regimen for the treatment of primary disease. At least 4 weeks since last surgery or radiation therapy. Must have had a treatment-free interval of greater than 6 months following response to platinum. ECOG performance status of 0,1, or 2.", "candidate_expression": "((ECOG performance status) AND (a treatment-free interval greater than 6 months following response to platinum) AND (platinum) AND (platinum-based chemotherapy regimen prior) AND (primary disease At least 4 weeks since last surgery or radiation therapy) AND ((.) OR (0) OR (0,1)))"}
{"candidate_id": "LLM07929", "doc_id": "NCT02357654_exc", "case_bucket": "other", "source_criterion": "day 3 transfers", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07930", "doc_id": "NCT02647788_inc", "case_bucket": "scope", "source_criterion": "Patients undergoing ambulatory hand surgery for carpal tunnel and trigger finger, under local anesthesia with or without sedation.", "candidate_expression": "((carpal tunnel) AND (hand surgery ambulatory) AND (local anesthesia) AND (trigger finger))"}
{"candidate_id": "LLM07931", "doc_id": "NCT02990403_exc", "case_bucket": "or", "source_criterion": "having experienced severe allergies, trauma history and/or operation history within 3 months. with a history of mental illness and/or family history of mental illness limb disabled. taking medicine within one month. suffering major events or having mood swings. having internal and surgical disease(after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) chromosome aberrations in anyone of the couple. patients who have drugs contraindications", "candidate_expression": "((after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) AND (anyone of the couple) AND (blood routine) AND (chromosome aberrations) AND (contraindications) AND (drugs) AND (electrocardiogram) AND (family history) AND (having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) AND (hepatic function) AND (history) AND (limb disabled) AND (medicine) AND (physical examination) AND (renal function) AND (severe) AND (surgical) AND (urine routine) AND (within 3 months) AND (within one month) AND ((major events) OR (mood swings)) AND ((allergies) OR (operation) OR (trauma)) AND ((internal disease) OR (surgical disease)) AND ((mental illness)))"}
{"candidate_id": "LLM07932", "doc_id": "NCT02563535_exc", "case_bucket": "or", "source_criterion": "need for major amputation known before intervention allergy to Paclitaxel contraindication for combined antiplatelet treatment life expectancy <1 year hypersensitivity or contraindication to one of the study drugs lack of consent", "candidate_expression": "((Paclitaxel) AND (allergy) AND (combined antiplatelet treatment) AND (contraindication) AND (lack of consent) AND (life expectancy <1 year) AND (major amputation) AND (study drugs one of) AND ((contraindication) OR (hypersensitivity)))"}
{"candidate_id": "LLM07933", "doc_id": "NCT02150590_inc", "case_bucket": "other", "source_criterion": "chronic obstructive pulmonary disease (COPD), GOLD grade 2-3 residents at low altitude (<800 m)", "candidate_expression": "((COPD) AND (GOLD grade 2-3) AND (chronic obstructive pulmonary disease))"}
{"candidate_id": "LLM07934", "doc_id": "NCT03352869_exc", "case_bucket": "or", "source_criterion": "Except for serious complications (cardiovascular events and recent significant liver, kidney or lung disease within 3 months) high blood pressure (>160/100mmHg) active infection secondary diabetes pregnancy alcohol abuse allergic to GLP-1 receptor agonist", "candidate_expression": "((>160/100mmHg) AND (GLP-1 receptor agonist) AND (active infection) AND (alcohol abuse) AND (allergic) AND (blood pressure) AND (cardiovascular events) AND (diabetes) AND (high blood pressure) AND (pregnancy) AND (secondary) AND (serious complications) AND (significant) AND (within 3 months) AND ((disease kidney) OR (disease liver) OR (lung disease)))"}
{"candidate_id": "LLM07935", "doc_id": "NCT02102243_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure or coronary artery disease Blood pressure averaging > 159/99 mmHg Serum creatinine > 1.5 mg/dL Diabetes mellitus or other systemic illness Left ventricular hypertrophy by echocardiography or ECG Pregnancy Hypersensitivity to spironolactone, chlorthalidone, amlodipine, human recombinant insulin or Definity Any history of substance abuse (other than tobacco) History of gouty arthritis Patients with right-to-left, bi-directional, or transient right-to-left cardiac shunts Hypersensitivity to perflutren, blood, blood products or albumin", "candidate_expression": "((> 1.5 mg/dL) AND (> 159/99 mmHg) AND (Blood pressure) AND (Congestive heart failure) AND (Diabetes mellitus) AND (ECG) AND (Hypersensitivity) AND (Left ventricular hypertrophy) AND (Pregnancy) AND (Serum creatinine) AND (albumin) AND (amlodipine) AND (bi-directional) AND (blood) AND (blood products) AND (cardiac shunts) AND (chlorthalidone) AND (coronary artery disease) AND (echocardiography) AND (gouty arthritis) AND (human recombinant insulin) AND (other) AND (perflutren) AND (right-to-left) AND (right-to-left,) AND (spironolactone) AND (substance abuse) AND (systemic illness) AND (tobacco) AND (transient))"}
{"candidate_id": "LLM07936", "doc_id": "NCT01000155_exc", "case_bucket": "or", "source_criterion": "Subjects with hemoglobin SC or SB+ thalassemia Subjects on chronic transfusion program Subjects who have received RBC transfusions cannot have >15% adult hemoglobin Known positive status for HIV, active hepatitis B or hepatitis C Pregnant or breast feeding women Individuals with a history of malignancy are ineligible except for the following circumstances. Individuals with a history of malignancy are eligible if they have been disease-free for at least 5 years and are deemed by the investigator to be at low risk for recurrence of that malignancy. Individuals with the following cancer are eligible if diagnosed and adequately treated within the past 5 years: cervical or breast cancer in situ, and basal cell or squamous cell carcinoma of the skin Subjects with a history of thrombosis or other reason (other than sickle cell disease) for enhanced thrombotic risk Subjects with unresolved infections Severe or uncontrolled medical conditions that could compromise study participation Subjects on fetal hemoglobin inducing agents Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy Known allergic reaction to a histone deacetylase inhibitor Subjects who have received valproic acid for treatment of epilepsy within 30 days of enrollment Subjects who have received any HDAC inhibitors other than valproic acid", "candidate_expression": "((>15% adult hemoglobin) AND (HDAC inhibitors) AND (RBC transfusions) AND (Severe or uncontrolled medical conditions that could compromise study participation) AND (Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy) AND (active) AND (adequately) AND (adequately treated) AND (allergic reaction) AND (are eligible) AND (cannot have) AND (chronic) AND (compromise study participation) AND (deemed by the investigator) AND (diagnosed) AND (disease-free) AND (enhanced risk) AND (enrollment) AND (epilepsy) AND (fetal) AND (fetal hemoglobin inducing agents) AND (for at least 5 years) AND (histone deacetylase inhibitor) AND (history) AND (infections) AND (low risk) AND (malignancy) AND (medical conditions) AND (other than) AND (recurrence of that malignancy) AND (sickle cell disease) AND (that malignancy) AND (thrombotic) AND (transfusion program) AND (treated) AND (treatment) AND (unresolved) AND (valproic acid) AND (within 30 days of enrollment) AND (within the past 5 years) AND (women) AND ((Pregnant) OR (breast feeding)) AND ((SB+ thalassemia) OR (hemoglobin SC)) AND ((basal cell carcinoma of the skin) OR (breast cancer in situ) OR (cervical cancer in situ) OR (squamous cell carcinoma of the skin)) AND ((thrombosis) OR (thrombotic risk)) AND ((HIV) OR (hepatitis B) OR (hepatitis C)))"}
{"candidate_id": "LLM07937", "doc_id": "NCT02558504_inc", "case_bucket": "or", "source_criterion": "Age over 18 years, General Condition WHO 0, 1 or 2, ASA Class I and II, eligible for endoscopic or surgical treatment with curative intent, Histological diagnosis of high grade glandular epithelial neoplasia (Vienna 4-1 to 4-46), possibly multifocal or stage 0 (Tis, N0, M0), Endoscopic and histological confirmed diagnosis of intestinal metaplasia, Histological diagnosis confirmed by two endoscopies with biopsies and two pathological readings; biopsies should be carried out according to the protocol of the SFED (four-quadrant biopsies every cm) with at least once acetic acid for staining. Operators describe Barrett's esophagus using he SFED planimetric model. The final exam will be no more than two months before the date of treatment and should have been achieved in investigator establishment, Minimum 1 cm, Maximum 12 cm. the resected lesion must have been well differentiated and confined to the mucosa (m2 maximum) on histological analysis, resection should be more than two months, resection must have been macroscopically complete laterally, resection must have been histologically complete in depth, resection must have been histologically complete laterally with regard to the microinvasive cancer, that is to say with a clear margin of safety (margin may be high-grade dysplasia provided that the latter has not macroscopic translation), At least one endoscopic and histologic follow-up should be conducted with dye in a period of less than two months before the date of treatment, and at the investigator establishment. Patient may take an inhibitor of proton pump equivalent to 2 times 40 mg of esomeprazole, No mediastinal or celiac, or suspected metastatic lymph nodes by EUS, Affiliation to a social security system or similar, Lack of participation in another clinical study, Informed consent signed.", "candidate_expression": "((ASA Class I II) AND (Affiliation to a social security system) AND (Age over 18 years) AND (EUS) AND (Endoscopic histological confirmed) AND (General Condition WHO 0 1 2) AND (Histological) AND (Histological diagnosis) AND (Informed consent signed) AND (M 0 Endoscopic confirmed) AND (N 0) AND (T is) AND (Vienna 4-1 to 4-46) AND (biopsies) AND (diagnosis Histological) AND (endoscopies two) AND (glandular epithelial neoplasia high grade multifocal) AND (histological) AND (histological analysis m2 maximum) AND (histologically) AND (intestinal metaplasia) AND (microinvasive cancer) AND (pathological readings two) AND (resected lesion well differentiated confined to the mucosa) AND (resection complete in depth) AND (resection complete laterally) AND (resection macroscopically complete laterally) AND (resection more than two months) AND (stage 0) AND (surgical treatment) AND (treatment endoscopic) AND NOT (lymph nodes mediastinal celiac metastatic) AND NOT (participation in clinical study another))"}
{"candidate_id": "LLM07938", "doc_id": "NCT02579928_exc", "case_bucket": "or", "source_criterion": "Current inpatient hospitalization or active suicidal ideation requiring referral for inpatient hospitalization for safety. History of psychotic disorder or manic episode diagnosed by MINI-KID History of substance dependence diagnosis by MINI-KID (excluding tobacco) or positive urine toxicology. Pregnancy (urine pregnancy tests on the day of scans for menstruating girls). Inability to provide written informed consent according to the Yale Human Investigation Committee (HIC) guidelines in English.", "candidate_expression": "((MINI-KID) AND (Pregnancy) AND (hospitalization Current) AND (inpatient) AND (inpatient hospitalization) AND (manic episode) AND (menstruating girls) AND (psychotic disorder) AND (referral requiring) AND (substance dependence) AND (suicidal ideation active) AND (urine pregnancy tests on the day of scans) AND (urine toxicology positive) AND NOT (tobacco) AND NOT (written informed consent Yale Human Investigation Committee (HIC) guidelines))"}
{"candidate_id": "LLM07939", "doc_id": "NCT03323047_inc", "case_bucket": "or", "source_criterion": "Healthy patients aged 3-13 years Level I or level II on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) obstructive sleep apnea or recurrent throat infections undergoing elective tonsillectomy with or without adenoidectomy Parents who agree to complete documentation and follow up at 14 days post-operation.", "candidate_expression": "((3-13 years) AND (American Society of Anesthesiologists (ASA) physical status) AND (Healthy) AND (Level I or level II) AND (Parents who agree to complete documentation and follow up at 14 days post-operation.) AND (adenoidectomy) AND (aged) AND (elective) AND (recurrent) AND (tonsillectomy) AND ((obstructive sleep apnea) OR (throat infections)))"}
{"candidate_id": "LLM07940", "doc_id": "NCT02519777_exc", "case_bucket": "or", "source_criterion": "Major depressive disorder with psychotic features Traumatic Brain Injury (TBI) with a clear impact on activities of daily living Developmental delay, intellectual deficit, and/or severe educational disability resulting in some dependence for activities of daily living Ongoing substance use disorder with significant impact on activities of daily living. Difficult or impossible to determine whether cognitive or functional decline is due to substance use or HIV, or both Evidence of intoxication or withdrawal during the screening evaluation Central nervous system (CNS) infections or opportunistic conditions: brain abscess (bacterial, mycobacterial, fungal or Toxoplasma), meningitis with persistent neurologic impairment, primary CNS lymphoma, progressive multifocal leukoencephalopathy (PML), or another structural brain lesion with neurological sequelae Other CNS conditions: non-opportunistic primary or metastatic brain tumors, uncontrolled seizure disorder, progressive multiple sclerosis, stroke with neurological sequelae, or dementia due to causes other than HIV (eg, Alzheimer's disease) Constitutional illness (eg, persistent unexplained fever, diarrhea, significant weight loss, disabling weakness) within 30 days of screening Known untreated B12 deficiency or malnutrition (body mass index [BMI] less than 18) at screening Evidence of current hepatitis C virus infection (HCV) (ie, HCV antibody [Ab] positive within 90 days prior to study entry unless also shown to be plasma HCV RNA negative within the same time period) Unstable and advanced liver disease (as defined by the presence of at least one of the following: ascites, encephalopathy, coagulopathy, hypoalbuminemia, esophageal or gastric varices, or persistent jaundice) Prior or current use of any CCR5 antagonist (such as MVC and cenicriviroc [CVC]) and integrase inhibitor (such as RAL, DTG, and elvitegravir [EVG]) Current use of any medication, including antiretrovirals, prohibited in the study (refer to the A5324 protocol-specific web page [PSWP] for the prohibited medications) Breastfeeding Presence of an AIDS-defining opportunistic infection within 6 months prior to entry. Note: Refer to the A5324 Manual of Operations (MOPS) for the list of AIDS-defining opportunistic infections. Active syphilis or treatment for syphilis within 90 days prior to study entry. NOTE: Active syphilis is defined as four-fold increase in serum rapid plasma reagin (RPR) or venereal disease research laboratory (VDRL) tests in an individual with past syphilis, or newly reactive serum RPR or VDRL with a reactive confirmatory test (enzyme immunoassays [EIA] or chemiluminescent assay [CIA], T. pallidum particle agglutination [TP-PA], or fluorescent treponemal antibody absorbed [FTA-ABS]). Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation", "candidate_expression": "((AIDS-defining opportunistic infection within 6 months prior to entry) AND (Alzheimer's disease) AND (B12 deficiency) AND (Breastfeeding) AND (CCR5 antagonist) AND (CNS conditions Other primary) AND (CNS lymphoma primary) AND (Central nervous system (CNS) infections) AND (Central nervous system (CNS) opportunistic conditions) AND (Constitutional illness within 30 days of screening) AND (DTG) AND (Developmental delay) AND (HCV antibody [Ab] positive within 90 days prior to study entry) AND (MVC) AND (Major depressive disorder) AND (RAL) AND (T. pallidum particle agglutination [TP-PA]) AND (Traumatic Brain Injury (TBI)) AND (VDRL) AND (allergy) AND (antiretrovirals) AND (ascites) AND (body mass index [BMI] less than 18) AND (brain abscess bacterial mycobacterial fungal) AND (brain tumors non-opportunistic metastatic) AND (cenicriviroc [CVC]) AND (chemiluminescent assay [CIA]) AND (coagulopathy) AND (components of study drugs) AND (dementia) AND (dependence for activities of daily living) AND (diarrhea) AND (disabling weakness) AND (elvitegravir [EVG]) AND (encephalopathy) AND (enzyme immunoassays [EIA]) AND (esophageal varices) AND (evere educational disability) AND (fluorescent treponemal antibody absorbed [FTA-ABS]) AND (gastric varices) AND (hepatitis C virus infection (HCV) Evidence current) AND (hypersensitivity) AND (hypoalbuminemia) AND (impact on activities of daily living) AND (integrase inhibitor) AND (intellectual deficit) AND (intoxication) AND (jaundice persistent Prior current) AND (liver disease Unstable advanced) AND (malnutrition) AND (medication Current prohibited in the study) AND (meningitis Toxoplasma) AND (neurologic impairment persistent) AND (neurological sequelae) AND (plasma HCV RNA negative within the same time period) AND (progressive multifocal leukoencephalopathy (PML)) AND (progressive multiple sclerosis) AND (reactive confirmatory test) AND (seizure disorder uncontrolled) AND (sensitivity) AND (serum RPR) AND (serum rapid plasma reagin (RPR)) AND (stroke) AND (structural brain lesion another) AND (substance use disorder Ongoing) AND (syphilis) AND (syphilis Active) AND (syphilis past) AND (treatment within 90 days prior to study entry) AND (unexplained fever persistent) AND (venereal disease research laboratory (VDRL)) AND (weight loss significant) AND (withdrawal) AND NOT (HIV))"}
{"candidate_id": "LLM07941", "doc_id": "NCT01942109_inc", "case_bucket": "other", "source_criterion": "heart failure NYHA II-IV previous treatment with diuretics age>18 years", "candidate_expression": "((>18 years) AND (II-IV) AND (NYHA) AND (age) AND (diuretics) AND (heart failure) AND (previous) AND (treatment))"}
{"candidate_id": "LLM07942", "doc_id": "NCT03190304_inc", "case_bucket": "or", "source_criterion": "Symptomatic patients with heart failure (men and women) aged >18 years, Functional class II, III or IV by the New York Heart Association (NYHA) Left ventricular ejection fraction <35% Ischemic and nonischemic etiology Type B natriuretic peptide (BNP) >150 pg/ml (or pro-BNP [N-terminal-proBNP] = 600 pg / ml) or if the patient was hospitalized for cardiac decompensation within the preceding 12 months, BNP >100 pg/ml (or N-terminal-proBNP = 400 pg / ml)", "candidate_expression": "((<35%) AND (= 400 pg / ml) AND (= 600 pg / ml) AND (>100 pg/ml) AND (>150 pg/ml) AND (>18 years) AND (Functional class II, III or IV) AND (Left ventricular ejection fraction) AND (New York Heart Association (NYHA)) AND (Symptomatic) AND (aged) AND (cardiac decompensation) AND (heart failure) AND (hospitalized) AND (within the preceding 12 months) AND ((Ischemic etiology) OR (nonischemic etiology)) AND ((Type B natriuretic peptide (BNP)) OR (pro-BNP [N-terminal-proBNP])) AND ((men) OR (women)) AND ((BNP) OR (N-terminal-proBNP)))"}
{"candidate_id": "LLM07943", "doc_id": "NCT03019562_inc", "case_bucket": "other", "source_criterion": "19-65 years of age ASA physical status classification I or II Scheduled for total hip replacement surgery", "candidate_expression": "((19-65 years) AND (ASA physical status classification) AND (I or II) AND (Scheduled for) AND (age) AND (total hip replacement surger))"}
{"candidate_id": "LLM07944", "doc_id": "NCT00812344_exc", "case_bucket": "or", "source_criterion": "Significant illness, trauma or surgical procedures. Clinically significant laboratory abnormalities. Clinically significant medical history", "candidate_expression": "((Clinically significant) AND (Significant) AND (illness) AND (laboratory) AND (laboratory abnormalities) AND (medical history) AND (surgical procedures) AND (trauma))"}
{"candidate_id": "LLM07945", "doc_id": "NCT03228238_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07946", "doc_id": "NCT03134378_inc", "case_bucket": "or", "source_criterion": "18 years or older patients who are proven to be infected by Helicobacter pylori based on positive in Urea Breath Test or positive in histopathologic examination of biopsy in antrum and corpus of gaster through esophagoduodenoscopy.", "candidate_expression": "((histopathologic examination of biopsy positive antrum of gaster corpus of gaster) AND (infected by Helicobacter pylori) AND (old 18 years or older) AND ((Urea Breath Test positive) OR (esophagoduodenoscopy)))"}
{"candidate_id": "LLM07947", "doc_id": "NCT02543710_exc", "case_bucket": "or", "source_criterion": "Patients who will not get surgical treatment for their endometrial cancer Patients not suffering from endometrial or epithelial ovarian cancer Patients who do not agree to the proposed treatment or will receive (part of) the treatment in a non-participating centre Patients who cannot or do not want to give informed consent (including language barriers)", "candidate_expression": "((agree to the proposed treatment) AND (endometrial cancer) AND (non-participating centre) AND (not) AND (surgical treatment) AND (treatment) AND ((give informed consent) OR (language barriers)) AND ((cannot) OR (do not want to)) AND ((endometrial ovarian cancer) OR (epithelial ovarian cancer)))"}
{"candidate_id": "LLM07948", "doc_id": "NCT02842424_exc", "case_bucket": "or", "source_criterion": "Rest pain or tissue loss due to PAD (Fontaine stage III and IV), acute lower extremity ischemic event secondary to thromboembolic disease or acute trauma, Walking capacity significantly limited by conditions other than claudication including leg (joint/musculoskeletal, neurologic) and systemic (heart, lung disease) pathology, Current use of either ACE inhibitors or angiotensin II receptor blockers, Chronic kidney disease with estimated Glomerular Filtration Rate < 30 ml/min/1.73 m2, History of bilateral severe renal artery stenosis and 7) History of angioedema related to previous ACE-inhibitor treatment or known hypersensitivity to ramipril or other ACE inhibitors.", "candidate_expression": "((ACE-inhibitor) AND (Chronic kidney disease) AND (Fontaine stage) AND (PAD) AND (Walking capacity significantly limited) AND (acute trauma) AND (conditions other than claudication other than claudication) AND (estimated Glomerular Filtration Rate < 30 ml/min/1.73 m2) AND (ischemic event acute lower extremity) AND (thromboembolic disease) AND NOT (claudication) AND ((Rest pain) OR (tissue loss)) AND ((secondary to acute trauma) OR (secondary to thromboembolic disease)) AND ((leg pathology) OR (systemic pathology)) AND ((joint) OR (musculoskeletal) OR (neurologic)) AND ((heart disease) OR (lung disease)) AND ((ACE inhibitors) OR (angiotensin II receptor blockers)) AND ((angioedema History) OR (renal artery stenosis History bilateral severe)) AND ((ACE-inhibitor treatment previous) OR (hypersensitivity known)) AND ((III) OR (IV)) AND ((ACE inhibitors) OR (ramipril)))"}
{"candidate_id": "LLM07949", "doc_id": "NCT03345589_exc", "case_bucket": "other", "source_criterion": "Autoimmune hepatitis Primary sclerosing cholangitis", "candidate_expression": "((Autoimmune hepatitis) AND (Primary sclerosing cholangitis))"}
{"candidate_id": "LLM07950", "doc_id": "NCT03472846_inc", "case_bucket": "other", "source_criterion": "Postmenopausal women Age 60-80 years T-score according to DXA: <-2.5 indication for osteoporosis therapy according to international guidelines", "candidate_expression": "((Age 60-80 years) AND (DXA) AND (Postmenopausal) AND (T-score according to DXA <-2.5) AND (osteoporosis) AND (osteoporosis therapy indication for) AND (women))"}
```
