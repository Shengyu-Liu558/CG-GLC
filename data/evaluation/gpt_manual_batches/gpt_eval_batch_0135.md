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
{"candidate_id": "LLM03351", "doc_id": "NCT02339844_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria patients: Substance abuse on a daily basis during the last 3 month or patients fulfilling the criteria of ongoing substance abuse due to ICD-10/DSM-IV/V, Treatment with antidepressant during the last 30 days, Head injury with more than 5 minutes of unconsciousness, Patients involuntarily admitted or treated, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness Exclusion criteria controls: First degree relatives with psychiatric disease, Substance abuse during the last 3 month or positive screening of drugs in urine-sample, Head injury with more than 5 minutes of unconsciousness, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness", "candidate_expression": "((First degree relatives) AND (ICD-10/DSM-IV/V) AND (controls) AND (daily basis) AND (during the last 3 month) AND (during the last 30 days) AND (more than 5 minutes) AND (ongoing) AND (patients) AND (positive) AND (unconsciousness) AND (urine-sample) AND ((Components of metal) OR (Head injury) OR (Pacemaker) OR (Pregnancy) OR (Severe physical illness) OR (Substance abuse) OR (antidepressant) OR (involuntarily admitted) OR (involuntarily treated) OR (substance abuse)) AND ((Components of metal) OR (Head injury) OR (Pacemaker) OR (Pregnancy) OR (Severe physical illness) OR (Substance abuse) OR (psychiatric disease) OR (screening of drugs)))"}
{"candidate_id": "LLM03352", "doc_id": "NCT03402945_inc", "case_bucket": "other", "source_criterion": "≥18 years of age undergoing open-heart surgery (sternotomy, including minimally-invasive sternotomies)", "candidate_expression": "((age ≥18 years) AND (minimally-invasive sternotomies) AND (open-heart surgery undergoing) AND (sternotomy))"}
{"candidate_id": "LLM03353", "doc_id": "NCT02884401_exc", "case_bucket": "or", "source_criterion": "On chronic treatment (i.e., two weeks or more) with any medication severely affecting oral status (e.g. participants with gingival hypertrophy caused by anti-epileptics, calcium antagonists, cyclosporine and other immunosuppressive) or bone metabolism (e.g. anticoagulant medications, long-standing steroid medications -i.e. equal or more 2.5mg of prednisolone a day taken for >3 months -, anticonvulsants, immunosuppressants). Affected by systemic diseases recognized to severely affect bone metabolism (e.g. Cushing's syndrome, Addison's disease, diabetes mellitus type 1, leukaemia, pernicious anaemia, malabsorption syndromes, chronic liver disease, rheumatoid arthritis). Knowingly affected by HIV or Hepatitis. History of local radiation therapy in the last five years. Affected by limited mental capacity or language skills such that study information cannot be understood, informed consent cannot be obtained, or simple instructions cannot be followed. Presenting an acute endodontic/periodontal lesion in the neighboring areas to the implant site. Completely edentulous With evident severe atrophy of the alveolar ridge that could preclude an implant placement (e.g. sharp knife edge ridge) Severe bruxism or clenching habits Smokers of > 5 cigarettes a day. A daily alcohol intake >2 units/day. Other severe acute or chronic medical or psychiatric condition or laboratory abnormality which may increase the risk associated with trial participation or investigational product administration or may interfere with the interpretation of study results and, in the judgment of the investigator, would make the participant inappropriate for entry into this trial. Patients unable or not willing to return for follow-ups.", "candidate_expression": "((> 5 a day) AND (>2 units/day) AND (>3 months) AND (Addison's disease) AND (Completely) AND (Cushing's syndrome) AND (HIV) AND (Hepatitis) AND (Patients unable or not willing to return for follow-ups) AND (Smokers) AND (alcohol) AND (anti-epileptics) AND (anticoagulant) AND (anticonvulsants) AND (bone metabolism) AND (bruxism) AND (calcium antagonists) AND (chronic liver disease) AND (cigarettes) AND (clenching habits) AND (cyclosporine) AND (diabetes mellitus type 1) AND (edentulous) AND (equal or more 2.5mg a day) AND (ffected by limited mental capacity or language skills such that study information cannot be understood, informed consent cannot be obtained, or simple instructions cannot be followed) AND (gingival hypertrophy) AND (immunosuppressants) AND (immunosuppressive) AND (last five years) AND (lesion endodontic) AND (leukaemia) AND (local radiation therapy) AND (malabsorption syndromes) AND (periodontal lesion) AND (pernicious anaemia) AND (prednisolone) AND (rheumatoid arthritis) AND (steroid) AND (treatment) AND (two weeks or more))"}
{"candidate_id": "LLM03354", "doc_id": "NCT02256956_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03355", "doc_id": "NCT02443623_exc", "case_bucket": "or", "source_criterion": "History of severe related adverse event(s) from previous participation in VA-001 or VA-006 trials or to any smallpox vaccination. Eczema, history of eczema, exfoliative skin conditions, wounds, burns, or other skin conditions at the investigator's discretion. A history of immunodeficiency. Currently or has recently received radiotherapy or chemotherapy, adrenocorticotropic hormone (ACTH), corticosteroids, or immunosuppressive drugs. Eye disease treated with topical steroids. Known or suspected disorders of immunoglobulin synthesis. Leukemia, lymphomas of any type, melanoma, or other malignant neoplasms affecting the bone marrow or lymphatic systems. Has been diagnosed with cancer and who will be undergoing chemotherapy or radiation therapy during the vaccination healing time. Is a transplant recipient (except for corneal transplant). Is pregnant, planning pregnancy or breast feeding (female subjects of childbearing potential must have negative pregnancy test prior to vaccination). Household or other close/intimate contact(s) under the age of 12 months. History of allergies to phenol, any of the antibiotics listed in the vaccine content, or any other component of ACAM2000 or its diluents. Subjects with kidney disease (except kidney stones). Subjects with abnormal EKG at screening (if applicable). To mitigate the risk of enrolling at risk subjects and potentially jeopardizing subject safety an EKG will be performed prior to vaccination with ACAM2000 smallpox vaccine in all potential subjects =50 years old and for all potential subjects <50 with two cardiac risk factors as listed immediately below including; severely or morbidly obese or higher obesity classification (BMI =36); high blood pressure; high blood cholesterol; diabetes or high blood sugar; a first degree relative who had a heart condition before the age of 50; and current tobacco smokers. Severely or morbidly obese or higher obesity classification (BMI =36) High blood pressure diagnosed by a doctor High blood cholesterol diagnosed by a doctor Diabetes or high blood sugar diagnosed by a doctor A first degree relative (for example, mother, father, brother, sister) who had a heart condition before the age of 50 Currently smokes tobacco (cigarettes) Arrhythmia Syncope related to cardiac disease Previous myocardial infarction Angina Coronary artery disease Congestive heart failure Cardiomyopathy Stroke or transient ischemic attack Myocarditis Pericarditis Chest pain or shortness of breath with activity (such as climbing stairs), peripheral edema, heart palpitations, dry cough, irregular heartbeat, excessive fatigue, unexplained syncope Other heart conditions being treated by a physician", "candidate_expression": "((A first degree relative) AND (ACTH) AND (Angina) AND (Arrhythmia) AND (Cardiomyopathy) AND (Congestive heart failure) AND (Coronary artery disease) AND (EKG abnormal at screening) AND (Eye disease) AND (High blood cholesterol) AND (High blood pressure) AND (Myocarditis) AND (Other heart conditions) AND (Pericarditis) AND (Previous myocardial infarction) AND (Syncope) AND (adverse event) AND (age 50) AND (age under 12 months) AND (allergies) AND (at the investigator's discretion) AND (bone marrow) AND (cardiac disease) AND (childbearing potential) AND (diagnosed with cancer) AND (disorders of immunoglobulin synthesis) AND (female) AND (heart condition before the age of 50) AND (history of immunodeficiency) AND (kidney disease) AND (lymphatic systems) AND (pregnancy test negative prior to vaccination vaccination) AND (smallpox vaccination) AND (smokes cigarettes) AND (smokes tobacco) AND (topical steroids) AND (transplant recipient) AND (vaccination) AND (vaccine) AND NOT (corneal transplant) AND NOT (kidney stones) AND ((Stroke) OR (transient ischemic attack)) AND ((Chest pain) OR (dry cough) OR (excessive fatigue) OR (heart palpitations) OR (irregular heartbeat) OR (peripheral edema) OR (shortness of breath with activity) OR (syncope)) AND ((adrenocorticotropic hormone) OR (chemotherapy) OR (corticosteroids) OR (immunosuppressive drugs) OR (radiotherapy)) AND ((Known) OR (suspected)) AND ((Leukemia) OR (lymphomas) OR (malignant neoplasms) OR (melanoma)) AND ((affecting lymphatic systems) OR (affecting the bone marrow)) AND ((chemotherapy) OR (radiation therapy)) AND ((Eczema) OR (burns) OR (exfoliative skin conditions) OR (history of eczema) OR (other skin conditions) OR (wounds)) AND ((breast feeding) OR (planning pregnancy) OR (pregnant)) AND ((Household) OR (close/intimate contact(s))) AND ((ACAM2000) OR (ACAM2000 diluents) OR (antibiotics listed in the vaccine content) OR (phenol)) AND ((BMI =36) OR (higher obesity classification) OR (obese Severely morbidly)) AND ((Diabetes) OR (high blood sugar)) AND ((brother) OR (father) OR (mother) OR (sister)))"}
{"candidate_id": "LLM03356", "doc_id": "NCT03088280_exc", "case_bucket": "other", "source_criterion": "PRA > 50% DSA > 1500 MFI Retransplantation Patients who are planning to receive mycophenolate instead of everolimus Patients who have planning for follow-up in another center", "candidate_expression": "((DSA > 1500 MFI) AND (PRA > 50%) AND (Retransplantation) AND (another center) AND (follow-up planning for) AND (mycophenolate planning to) AND NOT (everolimus))"}
{"candidate_id": "LLM03357", "doc_id": "NCT02277041_exc", "case_bucket": "or", "source_criterion": "women undergoing caesarean section at less than 37 weeks of gestation. Hypertension with pregnancy. Cardiac and coronary diseases with pregnancy", "candidate_expression": "((Cardiac diseases) AND (Hypertension) AND (caesarean section) AND (coronary diseases) AND (gestation) AND (less than 37 weeks) AND (pregnancy) AND (undergoing) AND (women))"}
{"candidate_id": "LLM03358", "doc_id": "NCT02019160_inc", "case_bucket": "other", "source_criterion": "Kindergarteners who have joined our outreach dental service will be invited to join this study. Preschool children aged 3-4 years who have tooth decay and are attending the first year of kindergarten will be invited to join this study.", "candidate_expression": "((3-4 years) AND (Kindergarteners) AND (Preschool children) AND (aged) AND (tooth decay))"}
{"candidate_id": "LLM03359", "doc_id": "NCT02350439_exc", "case_bucket": "or", "source_criterion": "1. Left main disease (angiographically> 50%) 2. Cardiogenic shock / hemodynamic instability 3. Previous CABG 4. Increased risk of bradycardia on investigator clinical judgment 5. Severe chronic obstructive pulmonary disease 6. Coronary vessels with tortuosity or extremely calcified 7. Severe left ventricular hypertrophy or severe valvular disease 8. STEMI or non-STEMI within the past five days 9. Previous myocardial infarction in the distribution of the target vessel for the FFR 10. Acute decompensated heart failure.", "candidate_expression": "((Acute decompensated heart failure) AND (CABG Previous) AND (Cardiogenic shock) AND (Increased risk) AND (Left main disease > 50%) AND (bradycardia Increased risk) AND (chronic obstructive pulmonary disease Severe) AND (hemodynamic instability) AND (investigator clinical judgment) AND (myocardial infarction Previous in the distribution of the target vessel) AND ((Coronary vessel extremely calcified) OR (Coronary vessel tortuosity)) AND ((left ventricular hypertrophy Severe) OR (severe) OR (valvular disease)) AND ((STEMI within the past five days) OR (non-STEMI within the past five days)))"}
{"candidate_id": "LLM03360", "doc_id": "NCT03068897_inc", "case_bucket": "or", "source_criterion": "Present to ED primary for management of LBP, defined as pain originating between the lower border of the scapulae and the upper gluteal folds. Flank pain, that is pain originating from tissues lateral to the paraspinal muscles, will not be included. Musculoskeletal etiology of low back. Patients with non-musculoskeletal etiologies such as urinary tract infection, ovarian cysts, or influenza like illness will be excluded. The primary clinical diagnosis, at the conclusion of the ED visit, must be a diagnosis consistent with non-traumatic, non-radicular, musculoskeletal LBP. Patient is to be discharged home. Patients admitted to the hospital are more likely to be treated with parenteral medication and therefore are not appropriate for this study. Age 18-64 Enrollment will be limited to adults younger than 65 years because of the increased risk of adverse medication effects in the elderly. Non-radicular pain. Patients will be excluded if the pain radiates below the gluteal folds in a radicular pattern. Pain duration <2 weeks (336 hours). Patients with more than two weeks of pain are at increased risk of poor pain and functional outcomes.(9) Prior to the acute attack of LBP, back pain cannot occur more frequently than once per month. Patients with more frequent back pain are at increased risk of poor pain and functional outcomes.(9) Non-traumatic LBP: no substantial and direct trauma to the back within the previous month Functionally impairing back pain: A baseline score of > 5 on the Roland-Morris Disability Questionnaire", "candidate_expression": "((18-64) AND (Age) AND (ED) AND (Flank pain) AND (Functionally impairing) AND (LBP) AND (Musculoskeletal) AND (Non) AND (Non-traumatic) AND (Pain) AND (Present) AND (Prior to the acute attack of LBP) AND (Roland-Morris Disability Questionnaire) AND (acute) AND (acute attack of LBP) AND (adults) AND (adverse effects) AND (attack of LBP) AND (back) AND (back pain) AND (baseline) AND (below the gluteal folds in a radicular pattern) AND (between the lower border of the scapulae and the upper gluteal folds) AND (cannot) AND (elderly) AND (etiologies) AND (etiology) AND (excluded) AND (increased risk) AND (low back) AND (medication) AND (more frequently than once per month) AND (musculoskeletal) AND (no) AND (non) AND (non-radicular) AND (non-traumatic) AND (not) AND (pain) AND (radicular) AND (score of > 5) AND (tissues lateral to the paraspinal muscles) AND (trauma) AND (within the previous month) AND (younger than 65 years) AND ((influenza like illness) OR (ovarian cysts) OR (urinary tract infection)) AND ((duration 336 hours) OR (duration <2 weeks)) AND ((direct) OR (substantial)))"}
{"candidate_id": "LLM03361", "doc_id": "NCT03444142_inc", "case_bucket": "other", "source_criterion": "Patients both sexes Age between 31 and 60 years Diagnosis of diabetes according ADA criteria:", "candidate_expression": "((ADA criteria) AND (Age) AND (between 31 and 60 years) AND (both sexes) AND (diabetes))"}
{"candidate_id": "LLM03362", "doc_id": "NCT02858180_exc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection with Genotype 2 or 3 Amiodarone. Subjects previously treated with amiodarone must have stopped the amiodarone at least 60 days prior to day 1 of SOF/LDV FDC Carbamazepine, phenytoin, phenobarbital, oxcarbazepine Rifabutin, rifampin or rifapentine HIV regimens containing tenofovir or tipranavir/ritonavir St. John's wort Rosuvastatin Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance History of hepatic encephalopathy or variceal hemorrhage Hepatitis B surface antigen positive Hemoglobin (Hb) < 8 g/dL Platelets = 50,000/mm3 alanine aminotransferase (ALT), aspartase aminotransferase (AST), or alkaline phosphatase = 10 times upper limit of normal(ULN) Total bilirubin > 3 mg/dl Severe renal impairment creatinine clearance (CrCl), i.e. < 30 mL/min. History of major organ transplantation with an existing functional graft. History of clinically-significant drug allergy to nucleoside/nucleotide analogs. Pregnant women or women planning to become pregnant Women who are breastfeeding Active or recent history (= 1 year) of drug or alcohol abuse", "candidate_expression": "((< 30 mL/min) AND (< 8 g/dL) AND (= 1 year) AND (= 10 times upper limit of normal) AND (= 50,000/mm3) AND (> 3 mg/dl) AND (ALT) AND (AST) AND (Amiodarone) AND (Carbamazepine) AND (Chronic HCV Infection) AND (CrCl) AND (Genotype 2) AND (Genotype 3) AND (Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance) AND (Hb) AND (Hemoglobin) AND (Hepatitis B surface antigen) AND (Platelets) AND (Pregnant women or women planning to become pregnant) AND (Rifabutin) AND (Rosuvastatin) AND (Severe) AND (St. John's wort) AND (Total bilirubin) AND (Women who are breastfeeding) AND (alanine aminotransferase) AND (alcohol abuse) AND (alkaline phosphatase) AND (aspartase aminotransferase) AND (at least 60 days prior to day 1 of SOF/LDV FDC) AND (clinically-significant) AND (creatinine clearance) AND (day 1 of SOF/LDV FDC) AND (drug abuse) AND (drug allergy) AND (existing functional graft) AND (hepatic encephalopathy) AND (major organ transplantation) AND (nucleoside) AND (nucleotide analogs) AND (oxcarbazepine) AND (phenobarbital) AND (phenytoin) AND (positive) AND (renal impairment) AND (rifampin) AND (rifapentine) AND (tenofovir) AND (tipranavir/ritonavir) AND (variceal hemorrhage))"}
{"candidate_id": "LLM03363", "doc_id": "NCT03209687_inc", "case_bucket": "other", "source_criterion": "Females undergoing Intra-Cytoplasmic Sperm Injection (ICSI) cycles Age between 20 and 40 years", "candidate_expression": "((Age between 20 and 40 years) AND (Females) AND (Intra-Cytoplasmic Sperm Injection (ICSI) cycles undergoing))"}
{"candidate_id": "LLM03364", "doc_id": "NCT02849483_exc", "case_bucket": "or", "source_criterion": "Allergic to study drugs Antiemetics or steroids use within 24 hrs prior to surgery Dependence upon opioids Insulin dependent Diabetes Mellitus Cardiovascular or pulmonary disease Renal or hepatic insufficiency BMI>=35kg/m2 History of motion sickness or PONV Cigarette smoker Conversion to open laparotomy from laparoscopic surgery Pregnants", "candidate_expression": "((>=35kg/m2) AND (Allergic) AND (Antiemetics) AND (BMI) AND (Cardiovascular disease) AND (Cigarette smoker) AND (Conversion) AND (Dependence upon opioids) AND (Diabetes Mellitus) AND (History) AND (Insulin) AND (Insulin dependent) AND (PONV) AND (Pregnants) AND (Renal insufficiency) AND (hepatic insufficiency) AND (laparoscopic surgery) AND (motion sickness) AND (open laparotomy) AND (pulmonary disease) AND (steroids use) AND (study drugs) AND (surgery) AND (within 24 hrs prior to surgery))"}
{"candidate_id": "LLM03365", "doc_id": "NCT02638935_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Women with breast implants on the same side as the lesion Women that underwent local radiation or chemotherapy within the last 12 months Women with history of breast cancer or breast surgery in the same quadrant Lesions in or close to scar tissue (< 1cm) Skin lesions or lesions that have been biopsied previously Lesion larger than 4 cm in the longest dimension No lesion should be included when more than 50% of the lesion is further down than 4 cm beneath the skin level.", "candidate_expression": "((< 1cm) AND (Lesion) AND (Lesions) AND (Women) AND (beneath the skin level) AND (biopsied) AND (breast implants) AND (further down than 4 cm) AND (in or close to scar tissue) AND (larger than 4 cm) AND (lesion) AND (longest dimension) AND (more than 50% of the lesion) AND (previously) AND (same quadrant) AND (same side as the lesion) AND (the lesion) AND (within the last 12 months) AND (women) AND ((Pregnant) OR (lactating)) AND ((breast cancer) OR (breast surgery)) AND ((Skin lesions) OR (lesions)) AND ((chemotherapy) OR (local radiation)))"}
{"candidate_id": "LLM03366", "doc_id": "NCT02964715_inc", "case_bucket": "or", "source_criterion": "biopsy proven NASH Type 2 DM HbA1c :>6.5% BMI < 45kg/m2 Any anti-diabetic agent except SGLT2 inhibitors, TZDs(thiazolidinediones), DPP4(Dipeptidyl peptidase4) inhibitors and GLP1 RAs(Glucagon-like Peptide 1-Receptor Agonists)", "candidate_expression": "((BMI < 45kg/m2) AND (Dipeptidyl peptidase4 inhibitors) AND (Glucagon-like Peptide 1-Receptor Agonists) AND (HbA1c >6.5%) AND (NASH) AND (Type 2 DM) AND (anti-diabetic agent) AND (biopsy) AND (thiazolidinediones) AND ((DPP4 inhibitors) OR (GLP1 RAs) OR (SGLT2 inhibitors) OR (TZDs)))"}
{"candidate_id": "LLM03367", "doc_id": "NCT02908919_inc", "case_bucket": "or", "source_criterion": "Subjects referred to diagnostic or therapeutic colonoscopy.", "candidate_expression": "((colonoscopy) AND ((diagnostic) OR (therapeutic)))"}
{"candidate_id": "LLM03368", "doc_id": "NCT01884337_inc", "case_bucket": "or", "source_criterion": "Age =18 years Subjects undergoing elective total knee or hip replacement or a revision of at least one component of a total knee or hip replacement", "candidate_expression": "((=18 years) AND (Age) AND (at least one component) AND (elective) AND (undergoing) AND ((total hip replacement) OR (total knee replacement)) AND ((a hip replacement revision of) OR (a total knee replacement revision of)))"}
{"candidate_id": "LLM03369", "doc_id": "NCT02964416_exc", "case_bucket": "or", "source_criterion": "Patients with a history of allergy or hypersensitivity to tramadol. History of epilepsy or convulsions due to any reason. Chronic usage of analgesic drugs. Patients using monoamine oxidase inhibitors. Patients with clinical signs of raised ICP. Obesity (women with a body mass index >35 kg/m2 or men with a body mass index >42 kg/m2) Language barrier. Patients taking B-blockers or Ca channel blockers. Patients above 65 years of age ( Physiology difference)", "candidate_expression": "((B-blockers) AND (Ca channel blockers) AND (ICP raised) AND (Language barrier) AND (Obesity) AND (age above 65 years) AND (allergy) AND (analgesic drugs) AND (body mass index >35 kg/m2) AND (body mass index >42 kg/m2) AND (convulsions) AND (epilepsy) AND (hypersensitivity) AND (men) AND (monoamine oxidase inhibitors) AND (tramadol) AND (women))"}
{"candidate_id": "LLM03370", "doc_id": "NCT03424993_exc", "case_bucket": "or", "source_criterion": "Abnormal resting ECG Current abnormal blood panel (assessed by comprehensive metabolic panel, lipid panel and complete blood count). Hypertension (currently taking anti-hypertensive medications or resting blood pressure >140/90 mmHg) Medical history of cardiovascular disease, malignant cancer, diabetes or kidney disease Obesity (Body Mass Index > 30) Current pregnancy Unable to provide consent", "candidate_expression": "((Body Mass Index > 30) AND (Hypertension) AND (Obesity) AND (Unable to provide consent) AND (anti-hypertensive medications) AND (blood panel Current abnormal) AND (cardiovascular disease) AND (complete blood count) AND (diabetes) AND (kidney disease) AND (lipid panel) AND (malignant cancer) AND (metabolic panel) AND (pregnancy Current) AND (resting ECG Abnormal) AND (resting blood pressure >140/90 mmHg))"}
{"candidate_id": "LLM03371", "doc_id": "NCT02145026_inc", "case_bucket": "or", "source_criterion": "Adult participants with low or intermediate-1 risk MDS No previous treatment with hematopoietic growth factors within 3 months prior to screening Symptomatic anemia (hemoglobin <10 g/dL) as determined by investigator Serum erythropoietin <500 milliunits/milliliter (mU/mL) within 14 days prior to the first dose of study treatment Require no red blood cell transfusion or dependent on <4 units within 8 weeks prior to screening Clinically stable for at least 1 month prior to entry into the study For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception", "candidate_expression": "((<10 g/dL) AND (<4 units) AND (<500 milliunits/milliliter) AND (Adult) AND (For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception) AND (MDS) AND (Serum erythropoietin) AND (Symptomatic) AND (anemia) AND (entry into the study) AND (for at least 1 month prior to entry into the study) AND (hematopoietic growth factors) AND (hemoglobin) AND (no) AND (red blood cell transfusion) AND (screening) AND (stable) AND (within 14 days prior to the first dose of study treatment) AND (within 3 months prior to screening) AND (within 8 weeks prior to screening) AND ((intermediate-1 risk) OR (low risk)))"}
{"candidate_id": "LLM03372", "doc_id": "NCT00502567_inc", "case_bucket": "or", "source_criterion": "histologically confirmed metastatic cancer that is not amenable to surgery or radiation therapy with curative intent measurable lesion by CT or other techniques according to RECIST", "candidate_expression": "((CT) AND (histologically confirmed) AND (measurable lesion) AND (metastatic cancer) AND ((radiation therapy not amenable) OR (surgery not amenable)))"}
{"candidate_id": "LLM03373", "doc_id": "NCT02046395_exc", "case_bucket": "or", "source_criterion": "Pregnancy Patients with chronic kidney disease stage with eGFR < 30 ml/min (CKD stage IV and V) Nephrotic range proteinuria (urinary protein > 3.5 gm/day) History or renal transplantation History of multiple myeloma Known history of hypersensitivity reaction or intolerability to Ace Inh or ARB.", "candidate_expression": "((< 30 ml/min) AND (> 3.5 gm/day) AND (ARB) AND (Ace Inh) AND (CKD) AND (History) AND (Nephrotic range) AND (Pregnancy) AND (chronic kidney disease) AND (eGFR) AND (history) AND (hypersensitivity reaction) AND (intolerability) AND (multiple myeloma) AND (proteinuria) AND (renal transplantation) AND (stage IV) AND (stage V) AND (urinary protein))"}
{"candidate_id": "LLM03374", "doc_id": "NCT00806936_inc", "case_bucket": "other", "source_criterion": "After the investigator has taken the decision to use human insulin or insulin analogues to treat the subject, any type 2 diabetic previously inadequately controlled with two or more OADs is eligible for the study The selection of the subjects will be at the discretion of the individual investigator", "candidate_expression": "((OADs) AND (inadequately controlled) AND (previously) AND (two or more) AND (type 2 diabetic))"}
{"candidate_id": "LLM03375", "doc_id": "NCT01857167_inc", "case_bucket": "or", "source_criterion": "1. Fasting glucose > 7.0 or have diabetes medication; 2. Male, 35-80 years; female, postmenopausal to 80 years; 3. Agree to participant in the trial.", "candidate_expression": "((35-80 years) AND (> 7.0) AND (Agree to participant in the trial.) AND (Fasting glucose) AND (Male) AND (diabetes) AND (diabetes medication) AND (female) AND (postmenopausal) AND (to 80 years))"}
```
