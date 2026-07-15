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
{"candidate_id": "LLM05151", "doc_id": "NCT03263481_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05152", "doc_id": "NCT02224040_exc", "case_bucket": "or", "source_criterion": "Allergy to ceftriaxone or macrolides Major typhoid fever-associated complications Inability to swallow oral medication Underlying illness Pregnancy Lactation Treatment within the past 4 days with an antibiotic that may be effective against typhoid fever", "candidate_expression": "((Allergy) AND (Inability to swallow oral medication) AND (Lactation) AND (Major) AND (Pregnancy) AND (Underlying illness) AND (antibiotic within the past 4 days effective against typhoid fever) AND (complications typhoid fever-associated) AND (oral medication) AND (typhoid fever) AND (typhoid fever Major) AND ((ceftriaxone) OR (macrolides)))"}
{"candidate_id": "LLM05153", "doc_id": "NCT00502567_inc", "case_bucket": "or", "source_criterion": "histologically confirmed metastatic cancer that is not amenable to surgery or radiation therapy with curative intent measurable lesion by CT or other techniques according to RECIST", "candidate_expression": "((CT) AND (confirmed) AND (histologically) AND (measurable lesion) AND (metastatic cancer) AND (not amenable) AND (radiation therapy) AND (surgery))"}
{"candidate_id": "LLM05154", "doc_id": "NCT02893293_exc", "case_bucket": "or", "source_criterion": "Contraindications for magnetic resonance imaging Hemosiderosis/hemochromatosis ( patients can still be included in the non-ferumoxytol arm)", "candidate_expression": "((Contraindications) AND (Hemosiderosis) AND (hemochromatosis) AND (magnetic resonance imaging))"}
{"candidate_id": "LLM05155", "doc_id": "NCT02035800_exc", "case_bucket": "other", "source_criterion": "Patients not capable or willing to provide informed consent Patients starting Adalimumab less than five half-lives after the interruption of a previous anti-TNF therapy.", "candidate_expression": "((Adalimumab less than five half-lives after the interruption of a previous anti-TNF therapy) AND (anti-TNF therapy previous))"}
{"candidate_id": "LLM05156", "doc_id": "NCT02541955_inc", "case_bucket": "other", "source_criterion": "Patient must meet 1987 ACR criteria Age > 18 years of age Baseline DAS28/Erythrocyte Sedimentation Rate (ESR) >=3.2 Stable concomitant Disease Modifying Anti-Rheumatic Drugs (DMARDs) Stable prednisone <10mg or equivalent Power Doppler score of >=10", "candidate_expression": "((1987 ACR criteria) AND (Age > 18 years of age) AND (DAS28/Erythrocyte Sedimentation Rate (ESR) Baseline >=3.2) AND (Disease Modifying Anti-Rheumatic Drugs (DMARDs) Stable concomitant) AND (Power Doppler score >=10) AND (prednisone Stable <10mg))"}
{"candidate_id": "LLM05157", "doc_id": "NCT01051414_inc", "case_bucket": "other", "source_criterion": "Subjects chronically infected with HCV Genotype 1 HCV RNA viral load of ≥ 10*5* IU/mL (100,000 IU/mL) at screening", "candidate_expression": "((HCV RNA viral load ≥ 10*5* IU/mL at screening 100,000 IU/mL screening) AND (HCV chronically Genotype 1 chronically))"}
{"candidate_id": "LLM05158", "doc_id": "NCT03255044_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to statin Treatment with statins during the past month prior to study. Serum creatinine > 3 mg/dl Significant liver disease: liver enzymes 2.5 folds the upper normal limit Malignancy Pregnancy or lactation", "candidate_expression": "((2.5 folds the upper normal limit) AND (> 3 mg/dl) AND (Malignancy) AND (Pregnancy) AND (Serum creatinine) AND (Significant) AND (during the past month prior to study) AND (hypersensitivity) AND (lactation) AND (liver disease) AND (liver enzymes) AND (statin) AND (statins) AND (the past month prior to study))"}
{"candidate_id": "LLM05159", "doc_id": "NCT03444142_inc", "case_bucket": "other", "source_criterion": "Patients both sexes Age between 31 and 60 years Diagnosis of diabetes according ADA criteria:", "candidate_expression": "((Age) AND (between 31 and 60 years) AND (both sexes) AND (diabetes ADA criteria))"}
{"candidate_id": "LLM05160", "doc_id": "NCT02502734_exc", "case_bucket": "or", "source_criterion": "A history of life-threatening asthma defined for this protocol as an asthma episode that required intubation, hypercapnea requiring non-invasive ventilatory support, respiratory arrest, hypoxic seizures or asthma-related syncopal episode(s). Subjects with a history of asthma exacerbation requiring the use of systemic corticosteroids (tablets, suspension, or injection) for at least 3 days or a depot corticosteroid injection or emergency room attendance (within 3 months) or requiring hospitalization for asthma (within 6 months) prior to screening. Significant, non-reversible active pulmonary disease (e.g. cystic fibrosis, bronchiectasis, tuberculosis). Culture-documented or suspected bacterial or viral infection of the upper or lower respiratory tract, sinus or middle ear that is not resolved within 4 weeks of Visit 1 and led to a change in asthma management or, in the opinion of the Investigator, is expected to affect the subject's asthma status or the subject's ability to participate in the study. Any fracture in the leg to be measured within 6 months prior to the screening visit. Any metabolic disorders or other diseases that may impact on normal growth patterns. No major surgery requiring general anaesthesia for at least 3 months prior to the screening visit. No febrile illnesses with temperature >39 degree celsius for more than five consecutive days within the week preceding the Screening Visit. Any significant abnormality or medical condition identified at the screening medical assessment (including serious psychological disorder) that in the Investigator's opinion, preclude entry into the study due to risk to the subject or that may interfere with the outcome of the study. Clinical visual evidence of candidiasis at Visit 1 (Screening). Use of any of the prohibited medications listed in protocol. Strenuous physical exercise within 3 hours of Visit 1 (Screening) Drug allergies: Any adverse reaction including immediate or delayed hypersensitivity to any intranasal, inhaled, or systemic corticosteroid therapy. Known or suspected sensitivity to the constituents of the ELLIPTA Inhaler (i.e., lactose, FF). Milk Protein Allergy: History of severe milk protein allergy. The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 30 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer). Exposure to more than 4 investigational medicinal products within 12 months prior to the first dosing day. Unable to use the ELLIPTA inhaler and peak flow meter correctly. An affiliation with the Investigator site: the parents/guardians or child is an immediate family member of the participating Investigator, sub-Investigator, study coordinator, or employee of the participating Investigator. The Parent or Guardian has a history of psychiatric disease, intellectual deficiency, substance abuse or other condition (e.g. inability to read, comprehend or write) which may affect: validity of consent to participate in the study; adequate supervision of the subject during the study; compliance of subject with study medication and study procedures (e.g. completion of daily diary, attending scheduled clinic visits); subject safety and well-being. Children in care: Children who are wards of the government or state are not eligible for participation in this study.", "candidate_expression": "((Any significant abnormality or medical condition identified at the screening medical assessment (including serious psychological disorder) that in the Investigator's opinion, preclude entry into the study due to risk to the subject or that may interfere with the outcome of the study.) AND (Drug allergies) AND (ELLIPTA inhaler) AND (Milk Protein Allergy) AND (Significant) AND (Strenuous physical exercise within 3 hours of Visit 1 (Screening)) AND (The Parent or Guardian has a history of psychiatric disease, intellectual deficiency, substance abuse or other condition (e.g. inability to read, comprehend or write) which may affect: validity of consent to participate in the study; adequate supervision of the subject during the study; compliance of subject with study medication and study procedures (e.g. completion of daily diary, attending scheduled clinic visits); subject safety and well-being.) AND (The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 30 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer).) AND (Unable to use the ELLIPTA inhaler and peak flow meter correctly.) AND (adverse reaction) AND (asthma) AND (asthma exacerbation history) AND (asthma history life-threatening) AND (asthma management) AND (candidiasis at Visit 1 (Screening)) AND (constituents of the ELLIPTA Inhaler) AND (fracture in the leg within 6 months prior to the screening visit) AND (general anaesthesia for at least 3 months prior to the screening visit) AND (in the opinion of the Investigator) AND (intubation) AND (investigational medicinal products more than 4 within 12 months prior to the first dosing day) AND (may impact on normal growth patterns) AND (milk protein allergy severe) AND (non-invasive ventilatory support) AND (peak flow meter) AND (prohibited medications listed in protocol) AND (pulmonary disease Significant non-reversible active) AND (sensitivity) AND (significant) AND (subject's ability to participate in the study) AND (temperature >39 degree celsius for more than five consecutive days within the week preceding the Screening Visit) AND (visual evidence) AND NOT (major surgery) AND NOT (febrile illnesses) AND ((delayed hypersensitivity) OR (immediate hypersensitivity)) AND ((FF) OR (lactose)) AND ((depot corticosteroid injection) OR (emergency room attendance within 3 months) OR (hospitalization within 6 months) OR (systemic corticosteroids for at least 3 days)) AND ((bronchiectasis) OR (cystic fibrosis) OR (tuberculosis)) AND ((bacterial infection of the lower respiratory tract) OR (bacterial infection of the middle ear) OR (bacterial infection of the sinus) OR (bacterial infection of the upper respiratory tract) OR (viral infection of the lower respiratory tract) OR (viral infection of the middle ear) OR (viral infection of the sinus) OR (viral infection of the upper respiratory tract)) AND ((Culture) OR (suspected)) AND ((asthma episode) OR (asthma-related syncopal episode) OR (hypercapnea) OR (hypoxic seizures) OR (respiratory arrest)) AND ((metabolic disorders) OR (other diseases)) AND ((abnormality) OR (medical condition)) AND ((inhaled corticosteroid) OR (intranasal corticosteroid) OR (systemic corticosteroid)))"}
{"candidate_id": "LLM05161", "doc_id": "NCT01322464_exc", "case_bucket": "or", "source_criterion": "Subjects were not to have a history or presence of significant cardiovascular, pulmonary, hepatic, renal, haematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease. Subjects were not to have any history or presence or family history of schizophrenia, other psychotic illness, severe personality disorder, depression, or other significant psychiatric disorder. Subjects were not to have a postural drop of 20 mmHg or more in systolic blood pressure at screening. Subjects were not to have participated in a previous clinical trial within 90 days prior to study initiation. Subjects were not to have donated plasma within 90 days prior to study initiation. Subjects were not to have donated blood within 90 days prior to study initiation. Subjects were not to have had an abnormal diet or substantial changes in eating habits within 30 days prior to study initiation. Subjects were not to have had treatment with any known enzyme-altering agents (barbiturates, phenothiazines, cimetidine etc.) within 30 days prior to or during the study. Subjects were to have no history of known hypersensitivity or idiosyncratic reaction to the study drug or related compounds. Subjects were not to use any prescription medication within 14 days prior to or during the study. Subjects were not to use any over-the-counter medication within 7 days prior to or during the study. Subjects were not to have a history of alcohol or drug abuse within 2 years prior to the study (subjects with a history of previous use of cannabis were not excluded unless they had used cannabis or cannabinoid based medicine within 30 days prior to study drug administration or were unwilling to abstain for the duration of the study).", "candidate_expression": "((90 days prior to study initiation) AND (abnormal diet) AND (alcohol abuse) AND (at screening) AND (barbiturates) AND (changes in eating habits) AND (cimetidine) AND (depression) AND (donated blood) AND (donated plasma) AND (drug abuse) AND (during the study) AND (enzyme-altering agents) AND (family history) AND (history) AND (hypersensitivity) AND (idiosyncratic reaction) AND (no) AND (not) AND (not excluded) AND (over-the-counter medication) AND (participated in a previous clinical trial) AND (phenothiazines) AND (postural drop of 20 mmHg) AND (prescription medication) AND (presence) AND (psychiatric disorder) AND (psychotic illness) AND (schizophrenia) AND (severe personality disorder) AND (significant) AND (study drug) AND (study initiation) AND (substantial) AND (systolic blood pressure) AND (the study) AND (use of cannabis) AND (within 14 days prior to the study) AND (within 2 years prior to the study) AND (within 30 days prior to or during the study) AND (within 30 days prior to study initiation) AND (within 7 days prior to the study) AND (within 90 days prior to study initiation))"}
{"candidate_id": "LLM05162", "doc_id": "NCT00344318_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days preceding the first dose of study vaccine, or planned use during the study period Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first vaccine dose. Planned administration/ administration of a vaccine not foreseen by the study protocol during the period starting one month before each dose of vaccine(s) and ending 7 days after dose 1 and dose 2 or 1 month after dose 3. Previous vaccination against diphtheria, tetanus, pertussis, polio, hepatitis B, Haemophilus influenzae type b, and/or S. pneumoniae with the exception of vaccines where the first dose can be given within the first two weeks of life according to the national recommendations History of or intercurrent diphtheria, tetanus, pertussis, hepatitis B, polio, and Haemophilus influenzae type b diseases. History of allergic disease or reactions likely to be exacerbated by any component of the vaccines. History of seizures (this criterion does not apply to subjects who have had a single, uncomplicated febrile convulsion in the past) or neurological disease. Acute disease at the time of enrolment Any confirmed or suspected immunosuppressive or immunodeficient condition based on medical history and physical A family history of congenital or hereditary immunodeficiency. Major congenital defects or serious chronic illness. Administration of immunoglobulins and/or any blood products since birth or planned administration during the active phase of the study.", "candidate_expression": "((Acute disease at the time of enrolment) AND (Haemophilus influenzae type b) AND (History) AND (Major congenital defects) AND (Planned) AND (S. pneumoniae) AND (allergic disease) AND (any blood products since birth) AND (congenital immunodeficiency) AND (diphtheria) AND (dose 1 ending 7 days after dose 1 and dose 2) AND (dose 2 1 month after dose 3) AND (dose 3) AND (drug) AND (family history) AND (hepatitis B) AND (hereditary immunodeficiency) AND (immunodeficient condition) AND (immunoglobulins) AND (immunosuppressants more than 14 days) AND (immunosuppressive condition) AND (neurological disease) AND (non-registered product any other than the study vaccine(s)) AND (other immune-modifying drugs) AND (pertussis) AND (planned during the active phase of the study) AND (planned use during the study period) AND (polio) AND (product any investigational other than the study vaccine(s)) AND (reactions allergic) AND (seizures) AND (serious chronic illness) AND (tetanus) AND (vaccination) AND (vaccine) AND (vaccine not foreseen by the study protocol period starting one month before each dose of vaccine(s)) AND NOT (vaccines first dose can be given) AND NOT (febrile convulsion single uncomplicated))"}
{"candidate_id": "LLM05163", "doc_id": "NCT02566863_exc", "case_bucket": "or", "source_criterion": "patient's refusal contraindications to dexmedetomidine diseases/drugs that influence on autonomic nervous system activity", "candidate_expression": "((contraindications) AND (dexmedetomidine) AND (diseases) AND (drugs) AND (influence on autonomic nervous system activity) AND (patient's refusal))"}
{"candidate_id": "LLM05164", "doc_id": "NCT01978028_exc", "case_bucket": "or", "source_criterion": "Hemochromatosis, iron overload, defined as TSAT > 45% Known hypersensitivity to Ferinject®. Known active infection, CRP>20 mg/L, clinically significant bleeding, active malignancy. Chronic liver disease and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) above three times the upper limit of the normal range. Immunosuppressive therapy or renal dialysis (current or planned within the next 6 months). History of erythropoietin, i. v. or oral iron therapy, and blood transfusion in previous 12 weeks and/or such therapy planned within the next 6 months. Unstable angina pectoris as judged by the investigator, clinically significant uncorrected valvular disease or left ventricular outflow obstruction, obstructive cardiomyopathy, poorly controlled fast atrial fibrillation or flutter, poorly controlled symptomatic brady- or tachyarrhythmias. Acute myocardial infarction or acute coronary syndrome, transient ischemic attack or stroke within the last 3 months. Coronary-artery bypass graft, percutaneous intervention (e.g. cardiac, cerebrovascular, aortic; diagnostic catheters are allowed) or major surgery, including thoracic and cardiac surgery, within the last 3 months. Participation in a CHF training program. Known HIV/AIDS. Inability to fully comprehend and/or perform study procedures in the investigator's opinion. Vitamin B12 and/or serum folate deficiency according to the laboratory (re-screening is possible after substitution therapy). Pregnancy or lactation. Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study. Anticoagulation", "candidate_expression": "((AIDS) AND (Anticoagulation) AND (CRP >20 mg/L) AND (Chronic liver disease) AND (Ferinject®) AND (Hemochromatosis) AND (Inability to fully comprehend and/or perform study procedures in the investigator's opinion) AND (Known HIV) AND (Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study.) AND (TSAT > 45%) AND (Unstable angina pectoris the next 6 months clinically significant) AND (hypersensitivity) AND (iron overload) AND ((alanine transaminase (ALT)) OR (aspartate transaminase (AST))) AND ((Immunosuppressive therapy) OR (renal dialysis)) AND ((current) OR (planned)) AND ((blood transfusion) OR (erythropoietin) OR (i. v. iron therapy) OR (oral iron therapy)) AND ((in previous 12 weeks) OR (within the next 6 months planned)) AND ((left ventricular outflow obstruction) OR (obstructive cardiomyopathy) OR (valvular disease)) AND ((fast atrial fibrillation) OR (fast atrial flutter)) AND ((brady-) OR (tachyarrhythmias)) AND ((Acute myocardial infarction) OR (acute coronary syndrome) OR (stroke) OR (transient ischemic attack)) AND ((Coronary-artery bypass graft) OR (major surgery) OR (percutaneous intervention)) AND ((cardiac surgery) OR (thoracic surgery)) AND ((Vitamin B12 deficiency) OR (serum folate deficiency)) AND ((Pregnancy) OR (lactation)) AND ((active infection) OR (bleeding clinically significant) OR (malignancy active)))"}
{"candidate_id": "LLM05165", "doc_id": "NCT02156999_inc", "case_bucket": "other", "source_criterion": "Osteoporosis", "candidate_expression": "(Osteoporosis)"}
{"candidate_id": "LLM05166", "doc_id": "NCT03241368_exc", "case_bucket": "or", "source_criterion": "Subject has indeterminate, ulcerative, antibiotic-associated colitis. Subject has stool positive for ova and parasite and for Clostridium difficule toxins within 3 months prior to enrollment. Subject with other known infectious cause of abdominal symptoms. Subject with clinical evidence of renal disease with the past 6 months, defined as estimated glomerular filtration rate (GFR) outside the normal reference range. Subject with known history of intestinal obstruction or current obstructive symptoms, such as severe abdominal pain with accompanying nausea or vomiting, based on investigator judgment. Subject with a diagnosis of gastroparesis or small bowel or large bowel dysmotility. Subjects with a history of small bowel or colonic resection. Subject with any current condition believed to have an increased risk of capsule retention such as suspected or known bowel obstruction, stricture, or fistula. Subject has used non-steroidal anti-inflammatory drugs including aspirin, two times per week, during the 4 weeks preceding enrollment. Low dose aspirin regimens (< 100 mg daily) are acceptable and not exclusionary. Subject suffers from any condition, such as swallowing problems, that precludes compliance with study and/or device instructions. Subject with cardiac pacemaker or other implanted electromedical device. Subject has an allergy or other known contraindication to the medications used in the study. Subject is pregnant (documented by a positive pregnancy test) or is actively breast-feeding. Subject is considered to be a part of a vulnerable population (eg. prisoners or those without sufficient mental capacity). Subject has a known contraindication to MRE or IC. Subject has participated in a drug or device research study within 30 days of enrollment that may interfere with the subject's safety or ability to participate in the study. Subject has any medical condition that would make it unsafe for them to participate, per Investigator's descretion", "candidate_expression": "((< 100 mg daily) AND (Clostridium difficule toxins positive for) AND (IC) AND (Low dose) AND (MRE) AND (Subject has participated in a drug or device research study within 30 days of enrollment that may interfere with the subject's safety or ability to participate in the study.) AND (actively) AND (allergy) AND (antibiotic-associated) AND (aspirin) AND (breast-feeding) AND (cardiac pacemaker) AND (colitis) AND (colonic resection) AND (compliance with device instructions) AND (compliance with study) AND (condition) AND (contraindication) AND (current) AND (during the 4 weeks preceding) AND (enrollment) AND (estimated glomerular filtration rate (GFR)) AND (gastroparesis) AND (history) AND (implanted electromedical device) AND (indeterminate) AND (intestinal obstruction) AND (large bowel dysmotility) AND (medications used in the study) AND (nausea) AND (non-steroidal anti-inflammatory drugs) AND (normal reference range) AND (obstructive symptoms) AND (outside) AND (parasite positive for) AND (part of a vulnerable population) AND (positive) AND (positive for ova) AND (precludes) AND (pregnancy test) AND (pregnant) AND (prisoners) AND (renal disease) AND (severe abdominal pain) AND (small bowel) AND (small bowel resection) AND (stool) AND (swallowing problems) AND (two times per week) AND (ulcerative) AND (vomiting) AND (with the past 6 months) AND (within 3 months prior) AND (without sufficient mental capacity))"}
{"candidate_id": "LLM05167", "doc_id": "NCT02509091_exc", "case_bucket": "or", "source_criterion": "Active bleeding without control; Receiving nasal or facial surgery recently; With severe cardio-pulmonary dysfunction, such as left heart failure, unstable arrhythmia, etc. With other respiratory diseases: such as active pulmonary tuberculosis, non-tuberculosis mycobacteria (NTM) pulmonary disease, pulmonary aspergillosis, etc. Be allergic to amikacin", "candidate_expression": "((Active) AND (NTM) AND (active) AND (allergic) AND (amikacin) AND (bleeding) AND (cardio-pulmonary dysfunction) AND (respiratory diseases) AND (severe) AND (unstable) AND ((non-tuberculosis mycobacteria pulmonary disease) OR (pulmonary aspergillosis) OR (pulmonary tuberculosis)) AND ((facial surgery) OR (nasal surgery)) AND ((arrhythmia) OR (left heart failure)))"}
{"candidate_id": "LLM05168", "doc_id": "NCT03164304_exc", "case_bucket": "or", "source_criterion": "Women with Non-proteinuric hypertension severe renal impairment Myasthenia gravis High amount of magnesium in blood Low or high amount of calcium in blood Myocardial damage, diabetic coma, heart block", "candidate_expression": "((Myasthenia gravis) AND (Myocardial damage) AND (Non-proteinuric hypertension) AND (Women) AND (calcium in blood) AND (diabetic coma) AND (heart block) AND (magnesium in blood High amount Low amount high amount) AND (renal impairment severe))"}
{"candidate_id": "LLM05169", "doc_id": "NCT00356148_inc", "case_bucket": "scope", "source_criterion": "Women at any age with early stage breast cancer (stage I-II) and American Society of Anesthesiologists (ASA) score of I-II.", "candidate_expression": "((American Society of Anesthesiologists (ASA) score) AND (I-II) AND (Women) AND (any age) AND (breast cancer) AND (early) AND (stage))"}
{"candidate_id": "LLM05170", "doc_id": "NCT02634541_exc", "case_bucket": "or", "source_criterion": "Psoriasis or psoriasis arthropathy Inflammatory bowel disease Unwillingness to participate in the study with additional imaging protocols Expected life-span less than <1 year Diabetes (to improve the PET imaging quality) Probable noncompliance Pregnancy Age <18 years or >75 years Contraindication for adalimumab Methotrexate used within the previous 6 months A biologic medicine used within the previous 6 months", "candidate_expression": "((<18 years) AND (>75 years) AND (Age) AND (Contraindication) AND (Diabetes) AND (Expected life-span) AND (Inflammatory bowel disease) AND (Methotrexate) AND (PET imaging quality) AND (Pregnancy) AND (Probable) AND (Psoriasis) AND (Unwillingness to participate in the study with additional imaging protocols) AND (adalimumab) AND (biologic medicine) AND (less than <1 year) AND (noncompliance) AND (psoriasis arthropathy) AND (within the previous 6 months))"}
{"candidate_id": "LLM05171", "doc_id": "NCT01313676_exc", "case_bucket": "or", "source_criterion": "Pregnancy: Women who are pregnant or lactating. Asthma: Subjects with a current diagnosis of asthma. (Subjects with a prior history of asthma are eligible if they also have a current diagnosis of COPD). alpha 1-antitrypsin deficiency: Subjects with known alpha-1 antitrypsin deficiency as the underlying cause of COPD. Other respiratory disorders: Subjects with active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, pulmonary fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. Lung resection or transplantation: Subjects with lung volume reduction surgery within the 12 months prior to Screening or having had a lung transplant. A moderate/severe COPD exacerbation that has not resolved at least 14 days prior to Visit 1 and at least 30 days following the last dose of oral corticosteroids (if applicable). Current severe heart failure (New York Heart Association class IV). Subjects will also be excluded if they have a known ejection fraction of <30% or if they have an implantable cardioverter defibrillator (ICD). Other diseases/abnormalities: Any life-threatening condition with life expectancy <3 years, other than vascular disease or COPD, that might prevent the subject from completing the study. End stage chronic renal disease: Subjects will be excluded if on renal replacement therapy (hemodialysis or peritoneal). Drug/food allergy: Subjects with a history of hypersensitivity to any of the study medications (e.g. beta-agonists, corticosteroid) or components of the inhalation powder (e.g. lactose, magnesium stearate). In addition, patients with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates the subject's participation will also be excluded. Drug/alcohol abuse: Subjects with a known or suspected history of alcohol or drug abuse within the last 2 years. Oxygen therapy: Subjects receiving treatment with long-term oxygen therapy (LTOT) or nocturnal oxygen therapy required for greater than 12 hours a day. Oxygen prn use (i.e. <=12 hours per day) is not exclusionary. Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures. Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study. Additional medication: Use of the following medications within the following time intervals prior to Visit 1 or during the study (unless otherwise specified): Medication No use within the following time intervals prior to Screening or thereafter at any time during the study (unless otherwise specified) Inhaled Long acting beta-agonists (LABA) 48 hours ICS/LABA combination products 48 hours Inhaled corticosteroids 48 hours Tiotropium 1 week Systemic, Oral, parenteral, intra-articular corticosteroids 30 days (oral and systemic corticosteroids may be used to treat COPD exacerbations during the study) Cytochrome P450 3A4 strong inhibitors including but not limited to antiretrovirals (protease inhibitors) (e.g.Indinavir, Nelfinavir, Ritonavir, Saquinavir); Imidazole and Triazole anti-fungals (e.g. Ketaconazole, Itraconazole); Clarithromycin, Telithromycin, Amiodarone, and Nefazodone 6 weeks Grapefruit is allowed up to Visit 1, then limited to no more than one glass of grapefruit juice (250 mL/ 8 ounces) or one grapefruit per day Any other investigational drug 30 days or 5 half lives whichever is longer.", "candidate_expression": "((1 week) AND (30 days) AND (48 hours) AND (5 half lives) AND (6 weeks) AND (<3 years) AND (<30%) AND (Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study.) AND (Amiodarone) AND (Asthma) AND (COPD) AND (COPD exacerbation) AND (COPD exacerbations) AND (Clarithromycin) AND (Cytochrome P450 3A4 strong inhibitors) AND (Drug abuse) AND (Drug allergy) AND (End stage chronic renal disease) AND (Grapefruit) AND (ICS/LABA combination products) AND (Imidazole anti-fungals) AND (Indinavir) AND (Inhaled Long acting beta-agonists (LABA)) AND (Inhaled corticosteroids) AND (Itraconazole) AND (Ketaconazole) AND (Lung resection) AND (Nefazodone) AND (Nelfinavir) AND (New York Heart Association) AND (No) AND (Oral) AND (Other respiratory disorders) AND (Pregnancy: Women who are pregnant or lactating.) AND (Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures.) AND (Ritonavir) AND (Saquinavir) AND (Screening) AND (Systemic) AND (Telithromycin) AND (Tiotropium) AND (Triazole anti-fungals) AND (active pulmonary diseases) AND (alcohol abuse) AND (alpha 1-antitrypsin deficiency) AND (alpha-1 antitrypsin deficiency) AND (antiretrovirals) AND (any time during the study) AND (asthma) AND (at least 14 days prior to Visit 1) AND (at least 30 days following the last dose of oral corticosteroids) AND (beta-agonists) AND (bronchiectasis) AND (class IV) AND (components of the inhalation powder) AND (corticosteroid) AND (corticosteroids) AND (current) AND (drug abuse) AND (during the study) AND (ejection fraction) AND (food allergy) AND (greater than 12 hours a day) AND (having had a lung transplant) AND (heart failure) AND (hemodialysis) AND (history) AND (hypersensitivity) AND (implantable cardioverter defibrillator (ICD)) AND (in the opinion of the study physician, contraindicates the subject's participation will also be excluded) AND (interstitial lung diseases) AND (intra-articular) AND (investigational drug) AND (lactose) AND (life expectancy) AND (life-threatening condition) AND (long-term oxygen therapy (LTOT)) AND (lung cancer) AND (lung transplant) AND (lung volume reduction surgery) AND (magnesium stearate) AND (milk protein allergy) AND (moderate) AND (nocturnal oxygen therapy) AND (not) AND (oral) AND (other than) AND (parenteral) AND (peritoneal) AND (prior) AND (protease inhibitors) AND (pulmonary fibrosis) AND (pulmonary hypertension) AND (renal replacement therapy) AND (resolved) AND (sarcoidosis) AND (severe) AND (study medications) AND (systemic) AND (that might prevent the subject from completing the study) AND (the last dose of oral corticosteroids) AND (the study) AND (transplantation) AND (treat COPD exacerbations) AND (tuberculosis) AND (vascular disease) AND (with lung volume reduction surgery) AND (within the 12 months prior to Screening) AND (within the last 2 years))"}
{"candidate_id": "LLM05172", "doc_id": "NCT02557412_inc", "case_bucket": "or", "source_criterion": "Diagnosis of dyslipidemia: The existence of a previous clinical diagnostic of dyslipidemia associated with lipid-lowering therapy. It is also considered patients who have an altered analytical, using the following cutoffs: total cholesterol = 200 mg / dl, triglycerides = 180 mg / dl, HDL-cholesterol = 40 mg / dl or LDL-cholesterol = 150 mg / dl. Lipid-lowering treatment and diet, stable in the last month. A concentration of LDL-cholesterol above 100 mg / dl, in the month prior to inclusion. An apnea-hypopnea index between 5-30 h-1", "candidate_expression": "((HDL-cholesterol = 40 mg / dl) AND (LDL-cholesterol = 150 mg / dl) AND (LDL-cholesterol above 100 mg / dl in the month prior to inclusion) AND (Lipid-lowering diet stable) AND (Lipid-lowering treatment) AND (altered analytical) AND (apnea-hypopnea index between 5-30 h-1) AND (dyslipidemia) AND (lipid-lowering therapy) AND (total cholesterol = 200 mg / dl) AND (triglycerides = 180 mg / dl))"}
{"candidate_id": "LLM05173", "doc_id": "NCT02425774_inc", "case_bucket": "or", "source_criterion": "patients undergoing partial or full resection of the pancreas due to a benign or malignant tumor", "candidate_expression": "((full resection of the pancreas) AND (partial resection of the pancreas) AND ((benign tumor) OR (malignant tumor)))"}
{"candidate_id": "LLM05174", "doc_id": "NCT02804126_exc", "case_bucket": "or", "source_criterion": "coagulopathy allergy to to local anesthetics depression, antidepressant drugs treatment epilepsy usage of painkiller before surgery addiction to alcohol or recreational drugs", "candidate_expression": "((addiction to alcohol) AND (addiction to recreational drugs) AND (allergy) AND (antidepressant drugs) AND (before surgery) AND (coagulopathy) AND (depression) AND (epilepsy) AND (local anesthetics) AND (painkiller))"}
{"candidate_id": "LLM05175", "doc_id": "NCT03221231_exc", "case_bucket": "or", "source_criterion": "Currently dependent on any substance other than cannabis, alcohol or nicotine; History of any major internal disease (including diabetes, cardiovascular disease, lung disease, liver or kidney disease); An active or any history of neurological disorder, including but not limited to seizure disorder, epilepsy, stroke, neurological disease, cognitive impairment, head trauma with prolonged loss of consciousness (>10 minutes), or migraine headaches; An active or a history of a psychiatric disorder including, but not limited to, depression, schizophrenia, bipolar disorder, anxiety, or other psychiatric disorders; Asthma; Known hypersensitivity or allergy to n-acetylcysteine, or receiving chronic therapy with medication that could interact adversely with n-acetylcysteine within 30 days prior to randomization (i.e., nitroglycerin, ACE inhibitors or antihypertensive drugs, anti-coagulants); Exclusion criteria for MRI: having metal in the body and/or having claustrophobia", "candidate_expression": "((>10 minutes) AND (Asthma) AND (Exclusion criteria for MRI) AND (chronic therapy) AND (dependent) AND (major internal disease) AND (n-acetylcysteine) AND (neurological disorder) AND (other) AND (other than) AND (prolonged loss of consciousness) AND (psychiatric disorder) AND (substance) AND (within 30 days prior to randomization) AND ((cardiovascular disease) OR (diabetes) OR (kidney disease) OR (liver disease) OR (lung disease)) AND ((active) OR (history)) AND ((cognitive impairment) OR (epilepsy) OR (head trauma) OR (migraine headaches) OR (neurological disease) OR (seizure disorder) OR (stroke)) AND ((anxiety) OR (bipolar disorder) OR (depression) OR (psychiatric disorders) OR (schizophrenia)) AND ((allergy) OR (hypersensitivity)) AND ((ACE inhibitors) OR (anti-coagulants) OR (antihypertensive drugs) OR (nitroglycerin)) AND ((alcohol) OR (cannabis) OR (nicotine)) AND ((claustrophobia) OR (metal in the body)))"}
```
