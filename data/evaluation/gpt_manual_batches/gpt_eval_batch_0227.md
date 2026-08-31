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
{"candidate_id": "LLM05651", "doc_id": "NCT00397215_exc", "case_bucket": "or", "source_criterion": "Administration of the licensed MF59-containing vaccines, e.g. Fluad™ or Addigrip™ or virosome-based influenza vaccines such as Inflexal V™, InfectoVac Flu™ or Invivac™ during the 2006-2007 influenza season. Administration of licensed vaccines within 2 weeks (for inactivated vaccines) or 4 weeks (for live vaccines) prior to enrolment in this study. Planned administration of a vaccine not foreseen by the study protocol up to 30 days after the second vaccination with H5N1 vaccine. Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first administration of the study vaccine. Any confirmed or suspected immunosuppressive or immunodeficient condition, based on medical history and physical examination (no laboratory testing required). History of chronic alcohol consumption and/or drug abuse. History of hypersensitivity to vaccines. History of allergic disease or reactions likely to be exacerbated by any component of the vaccine (including egg and thiomersal allergy). Acute clinically significant pulmonary, cardiovascular, hepatic or renal functional abnormality, as determined by physical examination or laboratory screening tests. Acute disease at the time of enrolment. Serious chronic disease including any medically significant chronic pulmonary, cardiovascular, renal, neurological, psychiatric or metabolic disorder, as determined by medical history and physical examination. Administration of immunoglobulins and/or any blood products within the three months preceding the first vaccination or during the study. Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days prior to the first vaccination, or planned use during the study period. Any condition which, in the opinion of the investigator, prevents the subject from participation in the study.", "candidate_expression": "((Acute disease at the time of enrolment) AND (H5N1 vaccine more than 14 days) AND (History) AND (chronic disease Serious) AND (condition which prevents the subject from participation in the study) AND (egg allergy) AND (hypersensitivity to vaccines) AND (immunosuppressants) AND (licensed vaccines) AND (not) AND (other immune-modifying drugs) AND (product other than the study vaccine(s) within 30 days prior to the first vaccination) AND (thiomersal allergy) AND (use planned during the study period) AND (vaccination) AND (vaccination first) AND (vaccine foreseen by the study protocol up to 30 days) AND NOT (study vaccine(s)) AND ((MF59-containing vaccines) OR (virosome-based influenza vaccines)) AND ((inactivated vaccines within 2 weeks prior to enrolment in this study) OR (live vaccines within 4 weeks prior to enrolment in this study)) AND ((Addigrip) OR (Fluad)) AND ((immunodeficient condition) OR (immunosuppressive condition)) AND ((confirmed) OR (suspected)) AND ((chronic alcohol consumption) OR (drug abuse)) AND ((allergic disease) OR (allergic reactions)) AND ((cardiovascular functional abnormality) OR (hepatic functional abnormality) OR (pulmonary functional abnormality) OR (renal functional abnormality)) AND ((chronic cardiovascular disorder) OR (chronic metabolic disorder) OR (chronic neurological disorder) OR (chronic psychiatric disorder) OR (chronic pulmonary disorder) OR (chronic renal disorder)) AND ((InfectoVac Flu) OR (Inflexal V) OR (Invivac)) AND ((any blood products) OR (immunoglobulins)) AND ((investigational) OR (non-registered)) AND ((drug) OR (vaccine)) AND ((during the study the study) OR (within the three months preceding the first vaccination the first vaccination)))"}
{"candidate_id": "LLM05652", "doc_id": "NCT03015818_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Pregnancy Concurrent antibiotherapy Certain infectious endocarditis Concurrent anti-inflammatory therapy, including corticosteroid therapy", "candidate_expression": "((Inability to give informed consent) AND (Pregnancy) AND (anti-inflammatory) AND (anti-inflammatory therapy Concurrent) AND (antibiotherapy Concurrent) AND (corticosteroid) AND (corticosteroid therapy) AND (infectious endocarditis Certain))"}
{"candidate_id": "LLM05653", "doc_id": "NCT02022709_inc", "case_bucket": "or", "source_criterion": "Having been diagnosed with primary OCD as defined by the Diagnostic and Statistical Manual of Mental Disorders (DSM-IV-) criteria;Cleaning or checking as primary OCD symptoms Yale-Brown Obsessive-Compulsive Scale (Y-BOCS) score of = 16 Never receiving adequate treatment or stop receiving treatment for at least 8 weeks Having an education degree of high school or above Accepting to participate in the study", "candidate_expression": "((DSM-IV) AND (Diagnostic and Statistical Manual of Mental Disorders) AND (Y-BOCS score of = 16) AND (Yale-Brown Obsessive-Compulsive Scale) AND (ccepting to participate in the study) AND (degree of high school) AND (primary OCD) AND (NOT (treatment for at least 8 weeks) OR NOT (treatment adequate)))"}
{"candidate_id": "LLM05654", "doc_id": "NCT02035904_inc", "case_bucket": "or", "source_criterion": "F; age 18 to 70 American Society of Anesthesiologists (ASA) I e II; breast cancer ( DIN 2 e 3, o LIN 2 e 3 sec. Tavassoli) scheduled for nipple-sparing mastectomy, simple mastectomy, skin-sparing mastectomy, skin-reducing mastectomy c, lymphnode biopsy and axillary dissection; immediate sub-pectoral prosthetic reconstruction; signed informed consent.", "candidate_expression": "((American Society of Anesthesiologists (ASA) I e II) AND (DIN 2 e 3) AND (F) AND (LIN 2 e 3 sec) AND (age 18 to 70) AND (axillary dissection) AND (breast cancer) AND (lymphnode biopsy) AND (nipple-sparing mastectomy scheduled for) AND (simple mastectomy) AND (skin-reducing mastectomy) AND (skin-sparing mastectomy) AND (sub-pectoral prosthetic reconstruction immediate))"}
{"candidate_id": "LLM05655", "doc_id": "NCT02042287_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05656", "doc_id": "NCT00404495_inc", "case_bucket": "other", "source_criterion": "Cohort 1: Recurrent or refractory medulloblastoma in which current standard treatment approaches have failed; biopsy is not required for recurrent disease. Cohort 2: Newly-diagnosed high-grade glioma (World Health Organization [WHO] grade 3 or 4) Life expectancy ≥ 3 months", "candidate_expression": "((Life expectancy ≥ 3 months) AND (Recurrent medulloblastoma) AND (World Health Organization [WHO] grade 3 or 4) AND (high-grade glioma) AND (refractory medulloblastoma) AND (standard treatment failed not required))"}
{"candidate_id": "LLM05657", "doc_id": "NCT02888704_exc", "case_bucket": "or", "source_criterion": "Subjects who have systemic infection Subjects who have human Immunodeficiency virus (HIV), hepatitis B virus (HBV), and hepatitis C virus (HCV) Subjects who need to take the medicine which is prohibited during this study Subjects who have asthma Subjects who can not stop treatment with topical steroids (group 1~5), oral antibiotics, whole body photochemotherapy, immunosuppressive drug within 4 weeks before the treatment visit Pregnant, breast-feeding women or women who plan to become pregnant during this study (Females of childbearing potential must have a negative urine pregnancy test) Subjects who currently participate in other clinical trial or participated in other clinical trial within 30 days Subjects who had a serious adverse events during stem cell therapy Subjects who had a hypersensitivity to antibiotics or antimycotics Subjects who creatinine value is more than two times of the upper limit of the normal range at screening test Subjects who aspartate transaminase/alkaline transaminase (AST/ALT) value is more than three times of the upper limit of the normal range at screening test Subjects who have any other condition which the investigator judges would make patients unsuitable for study participation", "candidate_expression": "((Pregnant) AND (any other condition) AND (aspartate transaminase/alkaline transaminase (AST/ALT)) AND (asthma) AND (at screening test) AND (breast-feeding) AND (childbearing potential) AND (creatinine) AND (during) AND (during this study) AND (hypersensitivity) AND (more than three times of the upper limit of the normal range) AND (more than two times of the upper limit of the normal range) AND (negative) AND (pregnant) AND (screening test) AND (serious adverse events) AND (stem cell therapy) AND (systemic infection) AND (the investigator judges would make patients unsuitable for study participation) AND (treatment visit) AND (urine pregnancy test) AND (within 4 weeks before) AND ((immunosuppressive drug) OR (oral antibiotics) OR (topical steroids) OR (whole body photochemotherapy)) AND ((Females) OR (women)) AND ((hepatitis B virus (HBV)) OR (hepatitis C virus (HCV)) OR (human Immunodeficiency virus (HIV))) AND ((antibiotics) OR (antimycotics)))"}
{"candidate_id": "LLM05658", "doc_id": "NCT03404479_inc", "case_bucket": "other", "source_criterion": "Subjects who voluntarily consented, after listening enough explanation for this study and investigational product. Adult over 50 years of age. At least one of the knee pain VAS score is 40mm or more. Patients who require medication for more than 12 weeks due to osteoarthritis symptoms. Those who are able to follow the requirements of this clinical trial, such as being able to trace during the clinical trial period and to read and write the VAS questionnaire. Those who weigh more than 40kg", "candidate_expression": "((Adult) AND (Subjects who voluntarily consented, after listening enough explanation for this study and investigational product.) AND (VAS score 40mm or more) AND (age over 50 years) AND (knee pain At least one) AND (medication more than 12 weeks) AND (osteoarthritis symptoms) AND (weigh more than 40kg))"}
{"candidate_id": "LLM05659", "doc_id": "NCT02314559_inc", "case_bucket": "other", "source_criterion": "All patients subjected to deep sedation in ambulant care, having a colonoscopy ASA 1-3", "candidate_expression": "((1-3) AND (ASA) AND (ambulant) AND (colonoscopy) AND (deep sedation))"}
{"candidate_id": "LLM05660", "doc_id": "NCT03154931_inc", "case_bucket": "other", "source_criterion": "Clinical Administered PTSD Scale 5 Monthly version Criteria A and >30 points", "candidate_expression": "((>30 points) AND (Clinical Administered PTSD Scale) AND (Criteria A))"}
{"candidate_id": "LLM05661", "doc_id": "NCT00379366_inc", "case_bucket": "other", "source_criterion": "over 18 years successful angioplasty (residual stenosis < 30%) on a significant stenosis (maximal systolic speed 3 times > from basal maximal systolic speed, stenosis > 70% on angiography) on the venous-prosthesis anastomosis or on the venous segment 5 cm after the anastomosis of a prosthetic haemodialysis vascular access (at least 1 month old) social security affiliation signed informed consent", "candidate_expression": "((3 times > from basal) AND (< 30%) AND (> 70%) AND (angiography) AND (maximal systolic speed) AND (on the venous segment 5 cm after the anastomosis angioplasty) AND (on the venous-prosthesis anastomosis angioplasty) AND (over 18 years) AND (residual stenosis) AND (signed informed consent) AND (significant) AND (social security affiliation) AND (stenosis) AND (successful))"}
{"candidate_id": "LLM05662", "doc_id": "NCT02609048_exc", "case_bucket": "or", "source_criterion": "1. A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment) 2. AST or ALT > 3 × ULN 3. Total bilirubin > 2 × ULN 4. Auto-immune hepatitis 5. Primary sclerosing cholangitis 6. Known history of alpha-1-Antitrypsin deficiency 7. Known history of chronic viral hepatitis 8. Creatine kinase above ULN 9. Serum creatinine above ULN 10. For females, pregnancy or breast-feeding 11. Use of colchicine, methotrexate, azathioprine, or systemic steroids in the two months preceding screening 12. Current use of fibrates, including fenofibrates, or simvastatin 13. Use of an experimental treatment for PBC 14. Use of experimental or unapproved immunosuppressant 15. Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator", "candidate_expression": "((A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment)) AND (ALT > 3 × ULN) AND (AST > 3 × ULN) AND (Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator) AND (Auto-immune hepatitis) AND (Creatine kinase above ULN) AND (PBC) AND (Primary sclerosing cholangitis) AND (Serum creatinine above ULN) AND (Total bilirubin > 2 × ULN) AND (alpha-1-Antitrypsin deficiency history) AND (azathioprine) AND (breast-feeding) AND (colchicine) AND (experimental treatment for PBC experimental) AND (females) AND (fenofibrates) AND (fibrates) AND (immunosuppressant unapproved) AND (in the investigator's opinion) AND (medical condition) AND (methotrexate) AND (other than) AND (pregnancy) AND (simvastatin) AND (systemic steroids) AND (viral hepatitis history chronic))"}
{"candidate_id": "LLM05663", "doc_id": "NCT01000155_exc", "case_bucket": "or", "source_criterion": "Subjects with hemoglobin SC or SB+ thalassemia Subjects on chronic transfusion program Subjects who have received RBC transfusions cannot have >15% adult hemoglobin Known positive status for HIV, active hepatitis B or hepatitis C Pregnant or breast feeding women Individuals with a history of malignancy are ineligible except for the following circumstances. Individuals with a history of malignancy are eligible if they have been disease-free for at least 5 years and are deemed by the investigator to be at low risk for recurrence of that malignancy. Individuals with the following cancer are eligible if diagnosed and adequately treated within the past 5 years: cervical or breast cancer in situ, and basal cell or squamous cell carcinoma of the skin Subjects with a history of thrombosis or other reason (other than sickle cell disease) for enhanced thrombotic risk Subjects with unresolved infections Severe or uncontrolled medical conditions that could compromise study participation Subjects on fetal hemoglobin inducing agents Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy Known allergic reaction to a histone deacetylase inhibitor Subjects who have received valproic acid for treatment of epilepsy within 30 days of enrollment Subjects who have received any HDAC inhibitors other than valproic acid", "candidate_expression": "((>15% adult hemoglobin) AND (HDAC inhibitors) AND (HIV) AND (Pregnant) AND (RBC transfusions) AND (SB+ thalassemia) AND (Severe or uncontrolled medical conditions that could compromise study participation) AND (Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy) AND (active) AND (adequately) AND (adequately treated) AND (allergic reaction) AND (are eligible) AND (basal cell carcinoma of the skin) AND (breast cancer in situ) AND (breast feeding) AND (cannot have) AND (cervical cancer in situ) AND (chronic) AND (compromise study participation) AND (deemed by the investigator) AND (diagnosed) AND (disease-free) AND (enhanced risk) AND (enrollment) AND (epilepsy) AND (fetal) AND (fetal hemoglobin inducing agents) AND (for at least 5 years) AND (hemoglobin SC) AND (hepatitis B) AND (hepatitis C) AND (histone deacetylase inhibitor) AND (history) AND (infections) AND (low risk) AND (malignancy) AND (medical conditions) AND (other than) AND (recurrence of that malignancy) AND (sickle cell disease) AND (squamous cell carcinoma of the skin) AND (that malignancy) AND (thrombosis) AND (thrombotic) AND (thrombotic risk) AND (transfusion program) AND (treated) AND (treatment) AND (unresolved) AND (valproic acid) AND (within 30 days of enrollment) AND (within the past 5 years) AND (women))"}
{"candidate_id": "LLM05664", "doc_id": "NCT03491059_exc", "case_bucket": "or", "source_criterion": "not a regular user of e-cigarettes pregnant or lactating (only excluded from imaging study) prisoner incapable of giving informed consent unable to lie flat on the scanner for extended periods of time unstable medical condition like heart disease, uncontrolled hypertension, thyroid disease, diabetes, renal or liver impairment, or glaucoma prostatic hypertrophy, stroke, or ulcer in past year psychiatric conditions such as schizophrenia, adult ADHD, or bipolar disorder current or regular use of psychiatric medications such as tranquilizers, antipsychotics, and/or antidepressants use of medications that are inducers of CYP2A6 (a nicotine metabolizing enzyme) such as rifampicin, dexamethasone, phenobarbital, and other anti-convulsant drugs unable to communicate in English current use of smokeless tobacco, tobacco cigarettes (5 and fewer a day) occasional use of pipes is permitted if subject abstains for the week prior to the study older than 80 years", "candidate_expression": "((e-cigarettes) AND (incapable of giving informed consent) AND (medical condition unstable) AND (medications inducers of CYP2A6) AND (nicotine metabolizing enzyme) AND (pregnant or lactating (only excluded from imaging study)) AND (prisoner) AND (psychiatric conditions) AND (psychiatric medications) AND (unable to lie flat on the scanner for extended periods of time) AND (years older than 80) AND NOT (regular user) AND ((diabetes) OR (glaucoma) OR (heart disease) OR (hypertension uncontrolled) OR (liver impairment) OR (renal impairment) OR (thyroid disease)) AND ((prostatic hypertrophy) OR (stroke) OR (ulcer)) AND ((adult ADHD) OR (bipolar disorder) OR (schizophrenia)) AND ((antidepressants) OR (antipsychotics) OR (tranquilizers)) AND ((anti-convulsant drugs) OR (dexamethasone) OR (phenobarbital) OR (rifampicin)) AND ((smokeless tobacco) OR (tobacco cigarettes)))"}
{"candidate_id": "LLM05665", "doc_id": "NCT02837783_exc", "case_bucket": "or", "source_criterion": "Patient has history of loose or watery stools Patient has both clinically significant findings and unexplained clinically significant alarm symptoms Patient has symptoms of or been diagnosed with a medical condition that may contribute to abdominal pain Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments", "candidate_expression": "((Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments) AND (abdominal pain) AND (clinically significant alarm symptoms) AND (clinically significant findings) AND (could confound the study assessments) AND (history of) AND (may contribute to abdominal pain) AND (medical condition) AND (unexplained) AND ((clinically significant) OR (protocol-excluded)) AND ((medical history) OR (surgical history)) AND ((loose stools) OR (watery stools)))"}
{"candidate_id": "LLM05666", "doc_id": "NCT03282006_exc", "case_bucket": "or", "source_criterion": "Bacterial infection origin from another organ (e.g. pneumonia) Severe sepsis with multiorgan failure Perinephritic abscess Pyonephrosis requiring drainage Allergy to pivmecillinam E.coli isolate resistant to pivmecillinam Pregnancy/breastfeeding Severe neutropenia Prostatitis Severe kidney failure (eGFR<15 ml/min) Using valproate", "candidate_expression": "((Allergy) AND (Bacterial infection another organ) AND (E.coli isolate resistant to pivmecillinam) AND (Perinephritic abscess) AND (Pregnancy) AND (Prostatitis) AND (Pyonephrosis) AND (Severe sepsis) AND (breastfeeding) AND (drainage requiring) AND (eGFR <15 ml/min) AND (kidney failure Severe) AND (multiorgan failure) AND (neutropenia Severe) AND (pivmecillinam) AND (pneumonia) AND (valproate))"}
{"candidate_id": "LLM05667", "doc_id": "NCT02721017_exc", "case_bucket": "or", "source_criterion": "age less than 13 years at time of procedure use of pain medication prior to procedure pectus carinatum, Poland's syndrome, or any chest wall anomaly other than pectus excavatum previous repair of pectus excavatum by any technique previous thoracic surgery congenital heart disease bleeding dyscrasia major anesthetic risk factors or history of previous problem with anesthesia pregnancy inability to communicate in English", "candidate_expression": "((age less than 13 years at time of procedure) AND (bleeding dyscrasia) AND (congenital heart disease) AND (inability to communicate in English) AND (pain medication prior to procedure) AND (pregnancy) AND (repair of pectus excavatum previous) AND (thoracic surgery previous) AND NOT (pectus excavatum) AND ((anesthetic risk factors major) OR (problem with anesthesia previous)) AND ((Poland's syndrome) OR (chest wall anomaly) OR (pectus carinatum)))"}
{"candidate_id": "LLM05668", "doc_id": "NCT02958072_inc", "case_bucket": "or", "source_criterion": "Diabetes mellitus Foot ulcer at the malleoli area between 0,25 cm² and 5,0 cm² Foot ulcer duration more than 6 weeks Ankle-brachial index above 0,40 or presence of palpable pulses in arteria dorsalis pedes and/or arteria tibialis posterior informed consent", "candidate_expression": "((Ankle-brachial index) AND (Diabetes mellitus) AND (Foot ulcer) AND (above 0,40) AND (arteria dorsalis pedes) AND (arteria tibialis posterior) AND (between 0,25 cm² and 5,0 cm²) AND (informed consent) AND (malleoli area) AND (more than 6 weeks) AND (palpable pulses))"}
{"candidate_id": "LLM05669", "doc_id": "NCT03213834_exc", "case_bucket": "or", "source_criterion": "age <18 years; Pregnancy inability to give informed written consent; previous thoracic surgery or thrombolytic therapy for pleural infection; medical thoracoscopy cannot be performed within 48 hours; inability to tolerate procedure due to hemodynamic instability or severe hypoxemia; inability to correct coagulopathy; presence of a homogeneously echogenic effusion on pleural US27 -", "candidate_expression": "((Pregnancy) AND (age <18 years) AND (cannot) AND (coagulopathy) AND (correct inability to) AND (hemodynamic instability) AND (homogeneously echogenic effusion) AND (hypoxemia severe) AND (inability to give informed written consent;) AND (inability to tolerate) AND (medical thoracoscopy cannot be performed within 48 hours) AND (pleural US) AND (pleural infection) AND (procedure) AND (thoracic surgery) AND (thrombolytic therapy))"}
{"candidate_id": "LLM05670", "doc_id": "NCT00344318_inc", "case_bucket": "or", "source_criterion": "Male or female between, and including, 6-12 weeks (42 to 90 days) of age at the time of the first vaccination. Subjects for whom the investigator believes that their parents/guardians can and will comply with the requirements of the protocol Written informed consent obtained from the parent or guardian of the subject. Free of obvious health problems as established by medical history and clinical examination before entering into the study. Born after a gestation period between 36 and 42 weeks.", "candidate_expression": "((Born) AND (Written informed consent) AND (gestation period between 36 and 42 weeks) AND (of age between 6-12 weeks at the time of the first vaccination between 42 to 90 days) AND NOT (health problems obvious) AND ((guardian) OR (parent)))"}
{"candidate_id": "LLM05671", "doc_id": "NCT02787863_exc", "case_bucket": "or", "source_criterion": "Vaccination against pneumococcal infection in anamnesis; Application of preparations of immune globulin or blood transfusion within last three months prior to clinical studies; Prolonged use (more than 14 days) immunosuppressants or other immunosuppressive drugs within 6 months prior to the start of the study; Any confirmed or suspected immunosuppressive or immunodeficient condition, including HIV infection; A history or currently hematologic and other cancers; A positive reaction for HIV infection, viral hepatitis B and hepatitis C; The presence of respiratory, cardio-vascular insufficiency, impaired liver and kidney function, established during a physical examination at visit number 1; Pronounced congenital defects or serious chronic diseases in the acute stage, including any clinically important exacerbation of chronic diseases of the liver, kidney, cardiovascular, nervous system, mental diseases or metabolic disorders, confirmed by the history or objective examination (pulmonary: cystic fibrosis, lung abscess, empyema, active tuberculosis; extra-pulmonary: congestive heart failure, malabsorption, chronic renal and hepatic failure, cirrhosis, malignancy, immunodeficiency, cirrhosis of the liver); Severe allergic reactions in anamnesis of autoimmune disease; The presence of acute infectious and/or communicable illnesses within 1 month prior to study; History of chronic alcohol abuse and/or drug use; Exacerbation of chronic diseases; Breastfeeding; Pregnancy; Participation in any other clinical study within the last 3 months.", "candidate_expression": "((Breastfeeding) AND (Exacerbation) AND (HIV infection) AND (Participation in clinical study any other within the last 3 months) AND (Pregnancy) AND (Vaccination) AND (alcohol abuse) AND (allergic reactions Severe) AND (blood transfusion) AND (cardio-vascular insufficiency) AND (chronic diseases) AND (chronic diseases serious acute stage) AND (cirrhosis) AND (cirrhosis of the liver) AND (communicable illnesses) AND (congenital defects) AND (congestive heart failure) AND (cystic fibrosis) AND (diseases of the cardiovascular system) AND (diseases of the kidney) AND (diseases of the liver) AND (diseases of the nervous system) AND (drug use) AND (empyema) AND (exacerbation) AND (hepatic failure) AND (immunodeficiency) AND (immunodeficient condition) AND (immunosuppressants more than 14 days) AND (immunosuppressive condition) AND (immunosuppressive drugs other) AND (impaired kidney function) AND (impaired liver) AND (infectious illnesses) AND (lung abscess) AND (malabsorption) AND (malignancy) AND (mental diseases) AND (metabolic disorders) AND (pneumococcal infection) AND (preparations of immune globulin) AND (reaction for HIV infection) AND (reaction for hepatitis C) AND (reaction for viral hepatitis B) AND (renal failure) AND (respiratory insufficiency) AND (tuberculosis active))"}
{"candidate_id": "LLM05672", "doc_id": "NCT03026465_inc", "case_bucket": "or", "source_criterion": "Patients older than 18 years Ischemic symptoms or evidence of myocardial ischemia (inducible or spontaneous) in the presence of >50% de novo stenosis located in native coronary vessels", "candidate_expression": "((>50%) AND (Ischemic symptoms) AND (de novo) AND (evidence) AND (inducible) AND (myocardial ischemia) AND (native coronary vessels) AND (older than 18) AND (spontaneous) AND (stenosis) AND (years))"}
{"candidate_id": "LLM05673", "doc_id": "NCT03639519_exc", "case_bucket": "or", "source_criterion": "Allergy to ascorbic acid Asthma COPD Allergy to opioids Previous history of chemical dependence Prior cardiac surgery Known hyperoxaluria History of renal calculi History of allergic or hypersensitivity reaction to ascorbic acid products Currently taking 1 g or more of ascorbic acid supplementation daily", "candidate_expression": "((Allergy) AND (Asthma) AND (COPD) AND (allergic) AND (ascorbic acid) AND (ascorbic acid 1 g or more) AND (cardiac surgery Prior) AND (chemical dependence Previous history) AND (hyperoxaluria) AND (hypersensitivity) AND (opioids) AND (renal calculi History))"}
{"candidate_id": "LLM05674", "doc_id": "NCT03259243_inc", "case_bucket": "other", "source_criterion": "Patient who undergoing gynecologic laparoscopic surgery Patient who agrees to participate in this study Patient able to speak and understand Thai Patient able to complete the questionnaire", "candidate_expression": "((Patient able to speak and understand Thai) AND (Patient who agrees to participate in this study) AND (able to complete the questionnaire) AND (able to speak and understand Thai) AND (agrees to participate in this study) AND (gynecologic laparoscopic surgery))"}
{"candidate_id": "LLM05675", "doc_id": "NCT00965900_exc", "case_bucket": "or", "source_criterion": "Patients with systolic blood pressure <100 mmHg or basal heart rate <60/min Portal vein thrombosis Uncontrolled ascites or hepatic encephalopathy Severe coagulation disorder: prothrombin time <40% (or INR >1.7) or platelet count <30,000/mm3 Medium or large sized gastric or duodenal varices Coexisting malignancy Severe cardiovascular disorder, renal failure, peritonitis, sepsis Severe erosive esophagitis, severe esophageal stricture, active gastric or duodenal ulcer Contraindication to beta-blocker Pregnancy Refusal to give consent to participate in the trial", "candidate_expression": "((Contraindication) AND (INR >1.7) AND (Portal vein thrombosis) AND (Pregnancy) AND (Refusal to give consent to participate in the trial) AND (ascites Uncontrolled) AND (beta-blocker) AND (cardiovascular disorder Severe) AND (coagulation disorder Severe) AND (duodenal ulcer) AND (duodenal varices) AND (erosive esophagitis Severe) AND (esophageal stricture severe) AND (gastric c) AND (gastric ulcer) AND (heart rate basal <60/min) AND (hepatic encephalopathy) AND (malignancy Coexisting) AND (peritonitis) AND (platelet count <30,000/mm3 Medium large) AND (prothrombin time <40%) AND (renal failure) AND (sepsis) AND (systolic blood pressure <100 mmHg))"}
```
