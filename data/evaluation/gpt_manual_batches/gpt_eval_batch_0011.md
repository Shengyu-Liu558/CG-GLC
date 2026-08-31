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
{"candidate_id": "LLM00251", "doc_id": "NCT03228498_inc", "case_bucket": "or", "source_criterion": "1. Cognitive impairment from mild to moderate degree defined by a Clinical Deterioration Rating (CDR) score range between 0.5 and 2.0. 2. Evidence on brain MRI of white matter hyperintensities (leukoaraiosis of moderate or severe degree according to the modified Fazekas visual scale and/or presence of lacunar infarcts). 3. Consent to participation in the study.", "candidate_expression": "((Clinical Deterioration Rating (CDR) score range between 0.5 and 2.0) AND (Cognitive impairment mild to moderate) AND (brain MRI white matter hyperintensities) AND (lacunar infarcts) AND (leukoaraiosis) AND (modified Fazekas visual scale moderate or severe degree))"}
{"candidate_id": "LLM00252", "doc_id": "NCT02678377_exc", "case_bucket": "other", "source_criterion": "History of recurrent UTI (defined as three culture proven UTIs within last 12 months) Systemic neuromuscular disease known to affect the lower urinary tract Undergoing concomitant prolapse surgery Previous incontinence surgery Treatment with anticholinergic medication in the last 2 months Previous bladder injection with onabotulinumtoxinA Prisoner Status Pregnancy", "candidate_expression": "((Pregnancy) AND (Prisoner) AND (anticholinergic medication last 2 month) AND (culture three) AND (incontinence surgery) AND (neuromuscular disease) AND (onabotulinumtoxinA bladder injection) AND (prolapse surgery) AND (recurrent UTI within last 12 months))"}
{"candidate_id": "LLM00253", "doc_id": "NCT02780427_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitive reaction to dexmedetomidine Organ dysfunction, and significant developmental delays or behavior problems Cardiac arrhythmia Known. acyanotic congenital heart disease or children after cardiac interventional procedures for follow-up examination.", "candidate_expression": "((Cardiac arrhythmia) AND (after cardiac interventional procedures) AND (cardiac interventional procedures) AND (children) AND (dexmedetomidine) AND (follow-up examination) AND (for follow-up examination) AND (significant) AND ((allergy) OR (hypersensitive)) AND ((acyanotic congenital heart disease) OR (cardiac interventional procedures)) AND ((Organ dysfunction) OR (behavior problems) OR (developmental delays)))"}
{"candidate_id": "LLM00254", "doc_id": "NCT01602081_exc", "case_bucket": "or", "source_criterion": "Patients with prior fistulotomy, fistulectomy, LIFT, cutting seton or advancement flap procedure Fistula with multiple tracts Recto-vaginal fistula Active infection in the anal fistula Physical allergies or cultural objections to porcine products Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician Previous diagnosis of collagen disorder History of Crohn's Disease, Irritable Bowel Syndrome, radiation therapy in the rectoanal region", "candidate_expression": "((Crohn's Disease) AND (Fistula) AND (History) AND (Irritable Bowel Syndrome) AND (LIFT) AND (Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician) AND (Recto-vaginal fistula) AND (advancement flap procedure) AND (anal fistula) AND (collagen disorder) AND (cutting seton) AND (fistulectomy) AND (fistulotomy) AND (infection in the anal fistula) AND (multiple tracts) AND (radiation therapy) AND (rectoanal region))"}
{"candidate_id": "LLM00255", "doc_id": "NCT03637946_inc", "case_bucket": "or", "source_criterion": "Over 18 years of age; Systemically healthy; Non-smoking; With good oral hygiene; Absent irreversible pulpal alteration; With the presence of a non-carious cervical lesion (LCNCs) that needs to be restored. This lesion should be non-carious, non-retentive, with at least 1 mm and up to 3 mm depth, should involve both enamel and dentin of vital teeth without mobility, and present hypersensitivity; Presence a natural tooth of the same position of the restored tooth, but in the opposite arch of the same jaw to be considered for the positive control; Periodontal parameters : Depth Probing (PS), Visible Plaque Index (IPV), Gingival Index (GI) and Probing Bleed Index (SS). The normal included were: PS = 1 to 3 mm, GI = 0, IPV = score 0 e SS = score 0.", "candidate_expression": "((= 0) AND (= 1 to 3 mm) AND (Absent) AND (Non-smoking) AND (Over 18 years) AND (PS) AND (Systemically healthy) AND (age) AND (at least 1 mm and up to 3 mm) AND (depth) AND (good oral hygiene) AND (hypersensitivity) AND (involve both enamel and dentin) AND (irreversible pulpal alteration) AND (lesion) AND (needs to be) AND (non-carious) AND (non-retentive) AND (score 0) AND ((Depth Probing (PS)) OR (Gingival Index (GI)) OR (Probing Bleed Index (SS)) OR (Visible Plaque Index (IPV))) AND ((GI) OR (IPV) OR (SS)) AND ((non-carious cervical lesion (LCNCs)) OR (restored)))"}
{"candidate_id": "LLM00256", "doc_id": "NCT02650024_exc", "case_bucket": "or", "source_criterion": "Amiodarone P-glycoprotein (P-gp) inducers (e.g., rifampin, St. John's wort) Liver biopsy at any time showing mHAI stage 4 or higher fibrosis OR FibroScan within 12 months demonstrating liver stiffness of =9.5 kilo Pascal or AST to platelet ratio index (APRI) =2.0 and Fibrosis-4 (FIB-4) =3.25 NOTE: If APRI and FIB-4 are discordant one of the other forms of fibrosis staging must be used. Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation. Hemochromatosis Alpha-1 antitrypsin deficiency Wilson's disease Autoimmune hepatitis Alcoholic liver disease Drug-related liver disease Severe NC confounding conditions (stroke, head injury, or developmental learning disability). Regular use of anti-inflammatory drugs. Current or recent treatment with pegylated interferon (PEG-IFN). Other active inflammatory process (major infection, malignancy, rheumatoid arthritis/autoimmune disorder) within the prior 28 days. Contraindications to magnetic resonance imaging (MRI). Bleeding diathesis, thrombocytopenia, or use of anticoagulants that would contraindicate lumbar puncture. Uncontrolled or active depression or other psychiatric disorder that in the opinion of the site investigator might preclude adherence to study requirements or impact NC functioning and assessments. Active drug or alcohol use or dependence that, in the opinion of the site investigator, would interfere with adherence to study requirements. Presence of active or acute AIDS-defining opportunistic infections within 12 weeks prior to study entry.", "candidate_expression": "((4 or higher) AND (=2.0) AND (=3.25) AND (=9.5 kilo Pascal) AND (AIDS-defining opportunistic infections) AND (AST to platelet ratio index (APRI)) AND (Active) AND (Alcoholic liver disease) AND (Alpha-1 antitrypsin deficiency) AND (Amiodarone) AND (Autoimmune hepatitis) AND (Bleeding diathesis) AND (Contraindications) AND (Current) AND (Drug-related liver disease) AND (FibroScan) AND (Fibrosis-4 (FIB-4)) AND (Hemochromatosis) AND (Liver biopsy) AND (NC confounding conditions) AND (Other) AND (P-glycoprotein (P-gp) inducers) AND (PEG-IFN) AND (St. John's wort) AND (Uncontrolled) AND (Wilson's disease) AND (active) AND (active inflammatory process) AND (acute) AND (alcohol use or dependence) AND (allergy) AND (anti-inflammatory drugs) AND (anticoagulants) AND (any time) AND (autoimmune disorder) AND (components of study drugs) AND (contraindicate) AND (depression) AND (developmental learning disability) AND (drug use or dependence) AND (head injury) AND (hypersensitivity) AND (liver stiffness) AND (lumbar puncture) AND (mHAI stage) AND (magnetic resonance imaging (MRI)) AND (major infection) AND (malignancy) AND (other) AND (pegylated interferon) AND (psychiatric disorder) AND (recent) AND (rheumatoid arthritis) AND (rifampin) AND (sensitivity) AND (stroke) AND (thrombocytopenia) AND (treatment) AND (within 12 months) AND (within 12 weeks prior to study entry) AND (within the prior 28 days))"}
{"candidate_id": "LLM00257", "doc_id": "NCT01322464_exc", "case_bucket": "or", "source_criterion": "Subjects were not to have a history or presence of significant cardiovascular, pulmonary, hepatic, renal, haematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease. Subjects were not to have any history or presence or family history of schizophrenia, other psychotic illness, severe personality disorder, depression, or other significant psychiatric disorder. Subjects were not to have a postural drop of 20 mmHg or more in systolic blood pressure at screening. Subjects were not to have participated in a previous clinical trial within 90 days prior to study initiation. Subjects were not to have donated plasma within 90 days prior to study initiation. Subjects were not to have donated blood within 90 days prior to study initiation. Subjects were not to have had an abnormal diet or substantial changes in eating habits within 30 days prior to study initiation. Subjects were not to have had treatment with any known enzyme-altering agents (barbiturates, phenothiazines, cimetidine etc.) within 30 days prior to or during the study. Subjects were to have no history of known hypersensitivity or idiosyncratic reaction to the study drug or related compounds. Subjects were not to use any prescription medication within 14 days prior to or during the study. Subjects were not to use any over-the-counter medication within 7 days prior to or during the study. Subjects were not to have a history of alcohol or drug abuse within 2 years prior to the study (subjects with a history of previous use of cannabis were not excluded unless they had used cannabis or cannabinoid based medicine within 30 days prior to study drug administration or were unwilling to abstain for the duration of the study).", "candidate_expression": "((90 days prior to study initiation) AND (at screening) AND (depression) AND (donated blood) AND (donated plasma) AND (enzyme-altering agents) AND (history) AND (hypersensitivity) AND (idiosyncratic reaction) AND (no) AND (not) AND (not excluded) AND (over-the-counter medication) AND (participated in a previous clinical trial) AND (postural drop of 20 mmHg) AND (prescription medication) AND (psychiatric disorder) AND (psychotic illness) AND (schizophrenia) AND (severe personality disorder) AND (significant) AND (study drug) AND (study initiation) AND (substantial) AND (systolic blood pressure) AND (the study) AND (use of cannabis) AND (within 2 years prior to the study) AND (within 30 days prior to or during the study) AND (within 30 days prior to study initiation) AND (within 90 days prior to study initiation) AND ((family history) OR (history) OR (presence)) AND ((abnormal diet) OR (changes in eating habits)) AND ((barbiturates) OR (cimetidine) OR (phenothiazines)) AND ((during the study) OR (within 14 days prior to the study)) AND ((during the study) OR (within 7 days prior to the study)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM00258", "doc_id": "NCT02562456_inc", "case_bucket": "or", "source_criterion": "Children aging between 3 and 6 years presenting good health conditions whose parents or legal guardians accept and sign the consent form with at least one occlusal or occlusal proximal caries lesion in primary molars only occlusal and/or occlusal-proximal surfaces with caries lesions with dentin involvement", "candidate_expression": "((Children) AND (aging) AND (at least one) AND (between 3 and 6 years) AND (caries lesion) AND (caries lesions) AND (dentin involvement) AND (good health conditions) AND (occlusal) AND (occlusal proximal) AND (occlusal surfaces) AND (occlusal-proximal surfaces) AND (primary molars) AND (whose parents or legal guardians accept and sign the consent form))"}
{"candidate_id": "LLM00259", "doc_id": "NCT02567214_inc", "case_bucket": "other", "source_criterion": "Age > 50 years Smoking history > 10 packs/year FEV1 30 - 79% of predicted and FEV1/FVC < 70% (GOLD 2-3) FRC > 120 % predicted Borg dyspnea score > 3 during the 3-min constant rate shuttle walking test at V3", "candidate_expression": "((2-3) AND (3-min constant rate shuttle walking test) AND (30 - 79% of predicted) AND (< 70%) AND (> 10 packs/year) AND (> 120 % predicted) AND (> 3) AND (> 50 years) AND (Age) AND (Borg dyspnea score) AND (FEV1) AND (FEV1/FVC) AND (FRC) AND (GOLD) AND (Smoking history) AND (V3))"}
{"candidate_id": "LLM00260", "doc_id": "NCT03019562_exc", "case_bucket": "or", "source_criterion": "Allergic to study drugs Patient with asthma or COPD, patient who is severely respiratory depressed Renal of hepatic insufficiency Epileptic status Intracranial lesion associated with increased intracranial pressure Acute abdomen, patient who has diagnosed paralytic ileus or suspicious ileus Pregnant or lactating women", "candidate_expression": "((Allergic) AND (Epileptic status) AND (Intracranial lesion) AND (Renal insufficiency) AND (hepatic insufficiency) AND (intracranial pressure increased) AND (study drugs) AND (wome) AND ((Acute abdomen) OR (paralytic ileus) OR (suspicious ileus)) AND ((Pregnant) OR (lactating)) AND ((COPD) OR (asthma) OR (respiratory depressed severely)))"}
{"candidate_id": "LLM00261", "doc_id": "NCT03036462_inc", "case_bucket": "other", "source_criterion": "Patients aged at least 18 years Patients with chronic heart failure present for at least 12 months Confirmed presence of iron deficiency Serum haemoglobin of 9.5 to 14.0 g/dL", "candidate_expression": "((Serum haemoglobin 9.5 to 14.0 g/dL) AND (aged at least 18 years) AND (chronic heart failure for at least 12 months) AND (iron) AND (iron deficiency))"}
{"candidate_id": "LLM00262", "doc_id": "NCT02968342_exc", "case_bucket": "or", "source_criterion": "Medical history of chronic psychiatric disease Medical conditions associated with female sexual dysfunction; cardiovascular disease, uncontrolled chronic HT (hypertension) ,DM (diabetes mellitus), History of gynecologic surgery, female gynecological cancer ( breast, ovarian, uterine, cervical) Medications associated with female sexual dysfunction; Antidepressants opiates, beta blockers, Antiepileptics ( gabapentin, topiramate,phenytoin) benzodiazepines", "candidate_expression": "((Antidepressants) AND (Antiepileptics) AND (DM) AND (HT) AND (History) AND (Medical conditions) AND (Medications) AND (associated with female sexual dysfunction) AND (benzodiazepines) AND (beta blockers) AND (breast) AND (cardiovascular disease) AND (cervical) AND (chronic) AND (chronic psychiatric disease) AND (diabetes mellitus) AND (female gynecological cancer) AND (female sexual dysfunction) AND (gabapentin) AND (gynecologic surgery) AND (history) AND (hypertension) AND (opiates) AND (ovarian) AND (phenytoin) AND (topiramate) AND (uncontrolled) AND (uterine))"}
{"candidate_id": "LLM00263", "doc_id": "NCT02277067_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((Women) AND (after 37 weeks) AND (cesarean section) AND (gestation) AND (singleton pregnancy))"}
{"candidate_id": "LLM00264", "doc_id": "NCT02201316_exc", "case_bucket": "or", "source_criterion": "Current or chronic history of liver disease, or known hepatic or biliary abnormalities (with the exception of Gilbert's syndrome or asymptomatic gallstones). History of regular alcohol consumption within 6 months of the study defined as: An average weekly intake of >21 units for males or >14 units for females. One unit is equivalent to 8 gram of alcohol: a half-pint (approximately 240 milliliter [mL]) of beer, 1 glass (100 mL) of wine or 1 (25 mL) measure of spirits. History of sensitivity to heparin or heparin-induced thrombocytopenia. History of sensitivity to any of the study medications, or components thereof or a history of drug or other allergy that, in the opinion of the investigator or GSK Medical Monitor, contraindicates their participation. Gastrointestinal disease or with gastrointestinal surgical history which can affect the absorption of the investigational product. A positive pre-study Hepatitis B surface antigen or positive Hepatitis C antibody result within 3 months of screening Urinary cotinine levels indicative of smoking or history or regular use of tobacco- or nicotine-containing products within 6 months prior to screening. A positive pre-study drug/alcohol screen. A positive test for Human Immunodeficiency Virus (HIV) antibody. Pregnant females as determined by positive serum hCG test at screening or prior to dosing. Where participation in the study would result in donation of blood or blood products in excess of 500 mL within a 90 day period. Lactating females. The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer). Exposure to more than four new chemical entities within 12 months prior to the first dosing day.", "candidate_expression": "((History) AND (Human Immunodeficiency Virus (HIV) antibody positive) AND (Lactating) AND (Pregnant) AND (The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer).) AND (Urinary cotinine levels) AND (average weekly intake) AND (contraindicates their participation) AND (females) AND (gastrointestinal surgical affect the absorption of the investigational product) AND (heparin) AND (heparin heparin-induced) AND (in the opinion of the investigator or GSK Medical Monitor) AND (new chemical entities more than four within 12 months prior to the first dosing day) AND (regular alcohol consumption History within 6 months of the study) AND (serum hCG test positive) AND (study medications) AND (NOT (gallstones asymptomatic) OR NOT (Gilbert's syndrome)) AND ((Current) OR (chronic)) AND ((females >14 units) OR (males >21 units)) AND ((heparin-induced thrombocytopenia) OR (sensitivity to heparin)) AND ((allergy) OR (drug allergy) OR (sensitivity to any of the study medications)) AND ((Gastrointestinal disease) OR (gastrointestinal surgical history)) AND ((Hepatitis B surface antigen positive pre-study) OR (Hepatitis C antibody positive)) AND ((regular use of nicotine-containing products history) OR (regular use of tobacco history) OR (smoking)) AND ((biliary abnormalities) OR (hepatic abnormalities) OR (liver disease history)) AND ((alcohol screen) OR (drug screen)) AND ((at screening screening) OR (prior to dosing dosing)))"}
{"candidate_id": "LLM00265", "doc_id": "NCT01184638_inc", "case_bucket": "or", "source_criterion": "Patients with informed consents Without basal disorders of neurology and psychiatrics", "candidate_expression": "((Patients with informed consents) AND (basal disorders of neurology) AND (basal disorders of psychiatrics))"}
{"candidate_id": "LLM00266", "doc_id": "NCT02102243_inc", "case_bucket": "other", "source_criterion": "Normotensive controls Stage I (140-159/90-99 mmHg) untreated subjects with essential hypertension Patients with PA and stage I (140-159/90-99 mmHg) hypertension", "candidate_expression": "((Normotensive) AND (PA) AND (Stage I) AND (controls) AND (essential hypertension) AND (hypertension) AND (stage I) AND (untreated))"}
{"candidate_id": "LLM00267", "doc_id": "NCT02764476_exc", "case_bucket": "or", "source_criterion": "Nonfluency or inability to communicate in English spoken language Inability to participate or attend biweekly 30 minute session over 14 weeks Frank psychosis Active self harm urges Serious medical illness Active substance or alcohol use or dependence that could interfere with participation Diagnoses of mental retardation, dementia or delirium Pregnant women", "candidate_expression": "((Pregnant) AND (Serious) AND (medical illness Serious) AND (psychosis Frank) AND (that could interfere with participation) AND (women) AND ((alcohol use or dependence) OR (substance use or dependence)) AND ((delirium) OR (dementia) OR (mental retardation)) AND ((Active) OR (self harm urges)))"}
{"candidate_id": "LLM00268", "doc_id": "NCT03506009_inc", "case_bucket": "other", "source_criterion": "18-80 years old; Diagnosis of posterior circulation ischemic stroke; Time from onset to treatment =6 hours; NIHSS: 4-25; Signed informed consent by patient self or legally authorized representatives.", "candidate_expression": "((18-80 years old) AND (4-25) AND (=6 hours) AND (NIHSS) AND (Signed informed consent by patient self or legally authorized representatives.) AND (Time from onset to treatment) AND (old) AND (posterior circulation ischemic stroke))"}
{"candidate_id": "LLM00269", "doc_id": "NCT03193684_inc", "case_bucket": "other", "source_criterion": "eGFR>60 ml/min healthy volunteers type 2 diabetes patients who otherwise healthy", "candidate_expression": "((>60 ml/min) AND (eGFR) AND (healthy) AND (type 2 diabetes))"}
{"candidate_id": "LLM00270", "doc_id": "NCT02257580_inc", "case_bucket": "scope", "source_criterion": "Scheduled for bilateral varus rotational osteotomy (VRO) with or without associated soft tissue and osseous procedures", "candidate_expression": "((Scheduled for) AND (VRO) AND (bilateral) AND (osseous procedures) AND (procedures soft tissue) AND (varus rotational osteotomy))"}
{"candidate_id": "LLM00271", "doc_id": "NCT02823808_inc", "case_bucket": "other", "source_criterion": "Type 2 Diabetes Mellitus patients Patient who had been diagnosed within the previous 12 months with HbA1c levels of 8.0-12.0%, did not have a medical history related to diabetes, and did not display proliferative retinopathy", "candidate_expression": "((HbA1c previous 12 months 8.0-12.0%) AND (Type 2 Diabetes Mellitus) AND NOT (proliferative retinopathy) AND NOT (medical history related to diabetes))"}
{"candidate_id": "LLM00272", "doc_id": "NCT02923700_exc", "case_bucket": "or", "source_criterion": "age > 80 years; Kellgren-Lawrence score at X-ray evaluation > 3; major axial deviation (varus >5° , valgus > 5°), systemic disorders such as diabetes, rheumatoid arthritis, haematological diseases (coagulopathy), severe cardiovascular diseases, infections, immunodepression; patients in therapy with anticoagulants or antiaggregants; use of NSAIDs in the 5 days before blood donation; patients with Hb values < 11 g/dl and platelet values < 150,000/mmc.", "candidate_expression": "((< 11 g/dl) AND (< 150,000/mmc) AND (> 3) AND (> 5°) AND (> 80 years) AND (>5°) AND (Kellgren-Lawrence score) AND (NSAIDs) AND (X-ray evaluation) AND (age) AND (coagulopathy) AND (in the 5 days before blood donation) AND (major axial deviation) AND (severe) AND (systemic disorders) AND (therapy) AND ((cardiovascular diseases) OR (diabetes) OR (haematological diseases) OR (immunodepression) OR (infections) OR (rheumatoid arthritis)) AND ((antiaggregants) OR (anticoagulants)) AND ((Hb) OR (platelet)) AND ((valgus) OR (varus)))"}
{"candidate_id": "LLM00273", "doc_id": "NCT03460002_inc", "case_bucket": "other", "source_criterion": "Children aged 0-59 months living with families registered in the rural Bandim Health Project Health and Demographic Surveillance Site are included, provided a parent/guardian consent.", "candidate_expression": "((Children) AND (Person Surveillance Site) AND (aged 0-59 months) AND (living with families registered in the rural Bandim Health Project Health))"}
{"candidate_id": "LLM00274", "doc_id": "NCT02707809_inc", "case_bucket": "other", "source_criterion": "kidney transplant recipient", "candidate_expression": "(kidney transplant)"}
{"candidate_id": "LLM00275", "doc_id": "NCT02416765_exc", "case_bucket": "or", "source_criterion": "1. Clinically significant microvascular complications: nephropathy (estimated glomerular filtration rate below 40 ml/min), neuropathy (especially diagnosed gastroparesis) or severe proliferative retinopathy as judged by the investigator. 2. Recent (< 3 months) acute macrovascular event e.g. acute coronary syndrome or cardiac surgery. 3. Ongoing pregnancy. 4. Severe hypoglycemic episode within 1 month of screening. 5. Agents affecting gastric emptying (Motilium®, Prandase®, Victoza®, Byetta® and Symlin®) as well as oral anti-diabetic agents (Metformin, SGLT-2 inhibitors and DPP-4 inhibitors) if not at a stable dose for 3 months. Otherwise, these medications are acceptable and will be kept stable during the entire protocol. 6. Oral steroids unless patients present a low stable dose (e.g. 10 mg or less of prednisone per day or physiological doses, less than 35 mg/day, of hydrocortisone Cortef®). Inhale steroids at stable dose in the last month are acceptable. 7. Other serious medical illness likely to interfere with study participation or with the ability to complete the trial by the judgment of the investigator (e.g. unstable psychiatric condition). 8. Failure to comply with team's recommendations (e.g. not willing to change pump parameters, follow algorithm's suggestions, etc). 9. Living or planned travel outside Montreal (> 1h of driving) area during closed-loop procedures.", "candidate_expression": "((Cortef less than 35 mg/day) AND (Inhale steroids stable dose in the last month) AND (Oral steroids low dose stable dose) AND (Other medical illness serious) AND (acute macrovascular event Recent < 3 months) AND (as judged by the investigator) AND (by the judgment of the investigator) AND (closed-loop procedures during closed-loop procedures) AND (estimated glomerular filtration rate below 40 ml/min) AND (gastroparesis) AND (hypoglycemic episode Severe within 1 month of screening) AND (microvascular complications as judged by the investigator) AND (pregnancy Ongoing) AND (psychiatric condition unstable) AND (serious) AND (stable dose for 3 months) AND ((nephropathy) OR (neuropathy) OR (severe proliferative retinopathy)) AND ((acute coronary syndrome) OR (cardiac surgery)) AND ((Agents affecting gastric emptying) OR (oral anti-diabetic agents)) AND ((Byetta) OR (Motilium) OR (Prandase) OR (Symlin) OR (Victoza)) AND ((DPP-4 inhibitors) OR (Metformin) OR (SGLT-2 inhibitors)) AND ((hydrocortisone physiological doses) OR (prednisone 10 mg or less per day)))"}
```
