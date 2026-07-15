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
{"candidate_id": "LLM05876", "doc_id": "NCT03615508_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05877", "doc_id": "NCT01320579_exc", "case_bucket": "or", "source_criterion": "History of other significant skin disease, or skin manifestations of allergic illness or other dermatologic condition, except chronic moderate or severe atopic dermatitis, that would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator Present symptoms of other skin diseases, except chronic atopic dermatitis, that could disturb the study assessment and evaluation of the skin Current use of any active systemic medication for chronic atopic dermatitis within one month Current use of active topical medication in the planned investigational area for chronic atopic dermatitis within two weeks History of a sunny holiday, UV-light therapy or solarium use within one month before beginning of study treatments, or planning such during the study or within 7 days after the study Allergy to cis-UCA, or any constituents of the placebo emulsion cream or any constituents of Protopic® ointment History of any skin-related cancer Congenital or acquired immunodeficiency or ongoing therapy that cause immunosuppression Earlier participation in a clinical study performed with cis-UCA Any clinically significant laboratory test result Suspected current drug or alcohol abuse Clinically significant illness during the 4 weeks prior to the first dose administration Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient Unwillingness or doubtful capacity to comply with the protocol Doubtful availability to complete the study", "candidate_expression": "((Allergy) AND (Any clinically significant laboratory test result) AND (Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient) AND (Clinically significant) AND (Clinically significant illness during the 4 weeks prior to the first dose administration) AND (Doubtful availability to complete the study) AND (History) AND (Protopic® ointment) AND (Suspected) AND (UV-light therapy) AND (Unwillingness or doubtful capacity to comply with the protocol) AND (acquired immunodeficiency) AND (active) AND (alcohol abuse) AND (allergic illness) AND (atopic dermatitis) AND (beginning of study treatments) AND (chronic atopic dermatitis) AND (chronic moderate) AND (cis-UCA) AND (clinically significant) AND (could disturb the study assessment and evaluation of the skin) AND (current) AND (dermatologic condition) AND (drug abuse) AND (during the 4 weeks prior to the first dose administration) AND (during the study) AND (except) AND (illness) AND (immunodeficiency Congenital) AND (immunosuppression) AND (laboratory test) AND (ongoing) AND (placebo emulsion cream) AND (planning) AND (severe) AND (significant) AND (skin disease) AND (skin diseases) AND (skin manifestations) AND (skin-related cancer) AND (solarium use) AND (sunny holiday) AND (systemic medication) AND (that cause immunosuppression) AND (the first dose administration) AND (therapy that cause immunosuppression) AND (topical medication) AND (within 7 days after the study) AND (within one month) AND (within one month before beginning of study treatments) AND (within two weeks) AND (would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator))"}
{"candidate_id": "LLM05878", "doc_id": "NCT02607163_inc", "case_bucket": "or", "source_criterion": "the patients undergoing ascending, arch and/or proximal descending aorta surgery with cardiopulmonary bypass 20 - 100 yrs old", "candidate_expression": "((cardiopulmonary bypass) AND (old 20 - 100 yrs) AND ((arch aorta surgery) OR (ascending aorta surgery) OR (proximal descending aorta surgery)))"}
{"candidate_id": "LLM05879", "doc_id": "NCT03400735_exc", "case_bucket": "or", "source_criterion": "Pregnancy or breastfeeding Allergy against to penicillin or cephalosporins Renal impairment Active hepatic disease Antibiotic use except study drugs Immunosuppressive therapy before 6 months of study initiation Use of probenecid like drugs", "candidate_expression": "((Allergy) AND (Antibiotic) AND (Immunosuppressive therapy before 6 months of study initiation) AND (Renal impairment) AND (hepatic disease Active) AND (probenecid like drugs) AND (probenecid probenecid like) AND NOT (study drugs) AND ((Pregnancy) OR (breastfeeding)) AND ((cephalosporins) OR (penicillin)))"}
{"candidate_id": "LLM05880", "doc_id": "NCT00954850_inc", "case_bucket": "or", "source_criterion": "Adults (18 and older) with physiologically confirmed SA or mild-moderate asthma and followed by an asthma specialist for at least 6 months. Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma). Must have good compliance with medications Patients with asthma and COPD.", "candidate_expression": "((18 and older) AND (Adults) AND (COPD) AND (Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma).) AND (SA) AND (asthma) AND (followed by an asthma specialist) AND (for at least 6 months) AND (good compliance) AND (medications) AND (mild) AND (moderate))"}
{"candidate_id": "LLM05881", "doc_id": "NCT01803828_exc", "case_bucket": "or", "source_criterion": "congenital or valvular cardiomyopathy; ischemic heart disease; endocrine diseases: male hypogonadism, hyperthyroidism, adrenal diseases, pituitary diseases proliferative retinopathy or autonomic neuropathy; contraindications to sildenafil use or CMR imaging;", "candidate_expression": "((CMR imaging) AND (adrenal diseases) AND (autonomic neuropathy) AND (cardiomyopathy congenital valvular) AND (contraindications) AND (endocrine diseases) AND (hyperthyroidism) AND (ischemic heart disease) AND (male hypogonadism) AND (pituitary diseases) AND (proliferative retinopathy) AND (sildenafil))"}
{"candidate_id": "LLM05882", "doc_id": "NCT02958566_exc", "case_bucket": "or", "source_criterion": "History of constipation Pre-existing use of narcotics or opioids Pre-existing renal or hepatic failure Mental illness, mental retardation, or inability to participate in informed consent due to mental status Pre-existing dementia Allergy to any protocol medication Emergency operation Subjects who are incarcerated or wards of the state Minors Subjects with inflammatory bowel disease, active colitis, or pre-existing intra-abdominal inflammation. Diverticulitis without active infection/inflammation will not be excluded.", "candidate_expression": "((Allergy) AND (Diverticulitis) AND (Emergency) AND (Minors) AND (Pre-existing) AND (active) AND (constipation) AND (dementia) AND (mental status) AND (not be excluded) AND (operation) AND (pre-existing) AND (without) AND ((Mental illness) OR (inability to participate in informed consent) OR (mental retardation)) AND ((narcotics) OR (opioids)) AND ((colitis) OR (inflammatory bowel disease) OR (intra-abdominal inflammation)) AND ((infection) OR (inflammation)) AND ((hepatic failure) OR (renal failure)))"}
{"candidate_id": "LLM05883", "doc_id": "NCT01631058_exc", "case_bucket": "or", "source_criterion": "Allergy to any of proposed medications Patients with any active infection including HBV, HCV and HIV.", "candidate_expression": "((Allergy) AND (HBV) AND (HCV) AND (HIV) AND (active infection) AND (proposed medications))"}
{"candidate_id": "LLM05884", "doc_id": "NCT03249311_exc", "case_bucket": "or", "source_criterion": "Lifetime personal history of diagnosis of major depressive disorder according to the DSM-V (American Psychiatric Association, 2013) using the Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition (SCID-5-RV for DSM-V; First et al., 2015) A history of suicidal ideation and behaviour, including self-harm and/or harm to others. A history of substance abuse and/or dependence. A positive drug screen for illicit drugs Substantial alcohol use Current use of Monoamine Oxidase Inhibitors (MAOIs), including the antibiotic linezolid and the thiazine dye methylthioninium chloride (methylene blue) Current use of serotonin-precursors (such as L-tryptophan, oxitriptan) Current use of serotonergic drugs (triptans, certain tricyclic antidepressants, lithium, tramadol, St. John's Wort) Concomitant use of NSAIDS, ASA, and other anticoagulants. Current use of Thioridazine Current use of CYP1A2 Inhibitors Current use of Triptans (5HT1 Agonists) Blood pressure greater than 140/90 and/or a pulse rate greater than 90 bpm Recent history of myocardial infarction, cerebrovascular accident, cardiac arrhythmias, or unstable heart disease. Evidence of significant physical illness contraindicating the use of levomilnacipran and duloxetine found on the physical exam or in the laboratory data obtained during the first week of the study Current use of medication that may affect voiding (ie- anticholinergics) History of obstructive urinary disorders and dysuria, prostatic hypertrophy, prostatitis, and other lower urinary tract obstructive disorders. History of Stevens-Johnson Syndrome and Erythema multiforme. Diabetes Type I and II Fructose intolerance, glucose-galactose malabsorption or sucrose-isomaltase insufficiency. Hepatic Impairment Uncontrolled narrow-angle glaucoma Severe renal impairment History of seizure disorder Anatomically narrow ocular angles. Osteoporosis or major risk for bone fractures.", "candidate_expression": "((5HT1 Agonists) AND (ASA) AND (Anatomically narrow ocular angles) AND (Blood pressure greater than 140/90) AND (CYP1A2 Inhibitors) AND (Diabetes Type I) AND (Diabetes Type II) AND (Erythema multiforme) AND (Fructose intolerance) AND (Hepatic Impairment) AND (L-tryptophan) AND (Monoamine Oxidase Inhibitors (MAOIs)) AND (NSAIDS) AND (Osteoporosis) AND (St. John's Wort) AND (Stevens-Johnson Syndrome) AND (Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition) AND (Substantial alcohol use) AND (Thioridazine) AND (Triptans) AND (affect voiding) AND (antibiotic linezolid) AND (anticholinergics) AND (anticoagulants other) AND (bone fractures major risk) AND (cardiac arrhythmias) AND (cerebrovascular accident) AND (contraindicating) AND (drug screen for illicit drugs positive) AND (duloxetine) AND (dysuria) AND (glucose-galactose malabsorption) AND (harm to others) AND (laboratory) AND (levomilnacipran) AND (lithium) AND (lower urinary tract obstructive disorders other) AND (major depressive disorder DSM-V) AND (medication Current) AND (methylene blue) AND (methylthioninium chloride) AND (myocardial infarction) AND (narrow-angle glaucoma Uncontrolled) AND (obstructive urinary disorders) AND (oxitriptan) AND (physical exam) AND (physical illness) AND (prostatic hypertrophy) AND (prostatitis) AND (pulse rate greater than 90 bpm) AND (renal impairment Severe) AND (seizure disorder History) AND (self-harm) AND (serotonergic drugs) AND (serotonin-precursors) AND (substance abuse) AND (substance dependence) AND (sucrose-isomaltase insufficiency) AND (suicidal behaviour) AND (suicidal ideation) AND (thiazine dye) AND (tramadol) AND (tricyclic antidepressant) AND (triptans) AND (unstable heart disease))"}
{"candidate_id": "LLM05885", "doc_id": "NCT01774019_exc", "case_bucket": "or", "source_criterion": "Biliary strictures caused by confirmed benign tumors Biliary strictures caused by malignancies other than pancreatic cancer, distal CBD cholangiocarcinoma and other periampullary cancers Surgically altered biliary tract anatomy, not including prior cholecystectomy Neoadjuvant chemotherapy for current malignancy Palliative indication due to reasons other than surgical candidate status Previous biliary drainage by ERCP/PTC Patients for whom endoscopic techniques are contraindicated Participation in another investigational trial within 90 days Pregnancy", "candidate_expression": "((Biliary strictures) AND (Neoadjuvant chemotherapy) AND (Pregnancy) AND (Previous) AND (Surgically altered biliary tract anatomy) AND (benign tumors) AND (biliary drainage by ERCP/PTC) AND (cholecystectomy) AND (confirmed) AND (contraindicated) AND (endoscopic techniques) AND (malignancies) AND (malignancy) AND (not) AND (other than) AND (prior) AND ((distal CBD cholangiocarcinoma) OR (other periampullary cancers) OR (pancreatic cancer)))"}
{"candidate_id": "LLM05886", "doc_id": "NCT01322464_inc", "case_bucket": "or", "source_criterion": "Healthy males between 18 and 45 years of age (inclusive). Body mass index to be between 18 to 30 kg/m2 (inclusive) as calculated by weight(Kg)/height(m2). Subjects were to have no clinically significant abnormal findings on physical examination, ECG, medical history, or clinical laboratory results during screening. Subjects were to, in the opinion of the investigator, have no clinically significant abnormal findings of renal and hepatic function as determined by serum creatinine, total bilirubin, and transaminase levels. Subjects were to be non-users of tobacco products (minimum of 6 months prior to the start of the study). Subjects were to have a negative screen for HIV I and II, HBsAg, and antibody to Hepatitis C virus. Subjects were to have a negative urine screen for alcohol, drugs of abuse (screening only), and cotinine. Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug. Subjects were able to comply with the protocol and the restrictions and assessments therein. Subjects were to give voluntary written informed consent to participate in the trial.", "candidate_expression": "((Body mass index) AND (ECG) AND (HBsAg) AND (Healthy) AND (Subjects were able to comply with the protocol and the restrictions and assessments therein.) AND (Subjects were to give voluntary written informed consent to participate in the trial) AND (Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug.) AND (abnormal findings) AND (age) AND (antibody to Hepatitis C virus) AND (between 18 and 45 years) AND (between 18 to 30 kg/m2) AND (clinical laboratory) AND (clinically significant) AND (during screening) AND (hepatic function) AND (in the opinion of the investigator) AND (medical history) AND (minimum of 6 months prior to the start of the study) AND (negative) AND (no) AND (non) AND (physical examination) AND (renal function) AND (screen for HIV I) AND (screen for HIV II) AND (serum creatinine) AND (the start of the study) AND (total bilirubin) AND (transaminase levels) AND (urine screen for alcohol) AND (urine screen for cotinine) AND (urine screen for drugs of abuse) AND (users of tobacco products))"}
{"candidate_id": "LLM05887", "doc_id": "NCT02394158_exc", "case_bucket": "or", "source_criterion": "Established pre-existing diabetes (including unrecognised diabetes defined as a fasting plasma glucose = 7.0mmol/L and/ or HbA1c = 48mmol/mol); Contraindications to metformin therapy (creatinine = 130µmol/L/ alanine transaminase = 2.0 x upper limit normal/ previous intolerance to metformin) Planned continued antenatal care/ delivery at centre not included in trial Planned fast for cultural/ religious reasons e.g. Ramadan", "candidate_expression": "((Contraindications) AND (Planned continued antenatal care/ delivery at centre not included in trial) AND (diabetes) AND (metformin) AND ((alanine transaminase = 2.0 x upper limit normal) OR (creatinine = 130µmol/L/) OR (intolerance)) AND ((HbA1c = 48mmol/mol)) OR (fasting plasma glucose = 7.0mmol/L)))"}
{"candidate_id": "LLM05888", "doc_id": "NCT03099408_exc", "case_bucket": "or", "source_criterion": "Presence of another vaginal infection or STD Allergy to metronidazole Pregnant or nursing Use of oral or intravaginal antibiotics within the past 2 weeks HIV or other chronic disease Inability to keep return appointments Contraindications for Lactobacillus Vaginal Suppositories(those without sexual history)", "candidate_expression": "((Allergy) AND (Contraindications) AND (Inability to keep return appointments) AND (Lactobacillus Vaginal Suppositories) AND (metronidazole) AND NOT (sexual history) AND ((HIV) OR (chronic disease other)) AND ((STD) OR (vaginal infection)) AND ((Pregnant) OR (nursing)) AND ((intravaginal antibiotics) OR (oral antibiotics)))"}
{"candidate_id": "LLM05889", "doc_id": "NCT02426034_exc", "case_bucket": "or", "source_criterion": "Subjects with poor-controlled arterial hypertension (systolic blood pressure> 140 mmHg and diastolic blood pressure > 90 mm Hg) despite standard medical management; Coronary heart disease greater than ClassII; II-level arrhythmia (including QT interval prolongation, for man = 450 ms, for woman = 470 ms) together with Class II cardiac dysfunction; Factors that could have an effect on oral medication (such as inability to swallow, chronic diarrhea and intestinal obstruction); Subjects with high gastrointestinal bleeding risk, including the following conditions: local active ulcer lesions with positive fecal occult blood test (++); history of black stool, or vomiting blood in the past 3 months;unresected primary lesion in stomach with positive fecal occult blood test (+), ulcerated gastric carcinoma with massive alimentary tract bleeding risk judged by PIs based on gastric endoscopy result; Abnormal Coagulation (INR>1.5<U+3001>APTT>1.5 UNL), with tendency of bleed; Associated with CNS (central nervous system) metastases; Pregnant or lactating women; Other conditions regimented at investigators' discretion.", "candidate_expression": "((+) AND (++) AND (> 140 mmHg) AND (> 90 mm Hg) AND (>1.5) AND (>1.5 UNL) AND (APTT) AND (Abnormal Coagulation) AND (Class II) AND (Coronary heart disease) AND (II-level) AND (INR) AND (Pregnant or lactating women) AND (QT interval prolongation) AND (Subjects) AND (active) AND (alimentary tract) AND (arrhythmia) AND (arterial hypertension) AND (black stool) AND (bleeding risk) AND (cardiac dysfunction) AND (chronic diarrhea) AND (diastolic blood pressure) AND (fecal occult blood test) AND (gastrointestinal bleeding risk) AND (greater than ClassII) AND (high) AND (inability to swallow) AND (intestinal obstruction) AND (massive) AND (metastases CNS) AND (past 3 months) AND (poor-controlled) AND (positive) AND (primary lesion) AND (stomach) AND (systolic blood pressure) AND (tendency of bleed) AND (ulcer lesions) AND (ulcerated gastric carcinoma) AND (vomiting blood))"}
{"candidate_id": "LLM05890", "doc_id": "NCT02365870_inc", "case_bucket": "other", "source_criterion": "Diagnosis of DSM 5 Anxiety Disorder Stable medical history and general health On stable anti-parkinsonian therapy for 2 weeks before enrollment", "candidate_expression": "((DSM 5 Anxiety Disorder) AND (Stable general health) AND (Stable medical history) AND (anti-parkinsonian therapy stable for 2 weeks before enrollment))"}
{"candidate_id": "LLM05891", "doc_id": "NCT03082573_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05892", "doc_id": "NCT02437084_inc", "case_bucket": "other", "source_criterion": "Healthy adults 30- 65 years old, BMI 25-35 kg/m2, nondiabetic as defined by fasting plasma glucose <126 mg/dL Lipids: one group with an LDL =/>130 and Triglycerides < 150 mg/dL The 2nd group will have and LDL=/>130 mg/dL and Triglycerides =/>150 mg/dL but less than 400 mg/dL.", "candidate_expression": "((BMI 25-35 kg/m2) AND (Healthy) AND (LDL =/>130) AND (Triglycerides < 150 mg/dL) AND (adults) AND (fasting plasma glucose <126 mg/dL) AND (nondiabetic) AND (old 30- 65 years old))"}
{"candidate_id": "LLM05893", "doc_id": "NCT02529475_inc", "case_bucket": "other", "source_criterion": "Major subjects of over 40 years (mean age of Meniere's disease 40 to 50 years) Informed consent signed Medical examination performed prior to participation in research Patients without history of inner ear disease Recipient of a French social security scheme", "candidate_expression": "((Medical examination) AND (history) AND (inner ear disease) AND (over 40 years) AND (prior to participation in research) AND (without) AND (years))"}
{"candidate_id": "LLM05894", "doc_id": "NCT01884337_inc", "case_bucket": "or", "source_criterion": "Age =18 years Subjects undergoing elective total knee or hip replacement or a revision of at least one component of a total knee or hip replacement", "candidate_expression": "((Age =18 years) AND (a hip replacement revision of) AND (a total knee replacement revision of) AND (total hip replacement) AND (total knee replacement))"}
{"candidate_id": "LLM05895", "doc_id": "NCT03125057_exc", "case_bucket": "or", "source_criterion": "Therapy area located outside of head and neck; Other skin diseases that might interfere with the efficacy evaluation; Therapy area was previously received isotope or PDT or other treatment which might interfere with the efficacy evaluation; Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Immunocompromised conditions; Electrocardiographic abnormalities or organic heart diseases; Coagulation disorders; Hepatic or renal functions abnormal (alanine aminotransferase or aspartate transaminase or total bilirubin > 1.5 upper limit of normal [ULN], or serum creatinine or blood urea nitrogen > 1.5 ULN); Psychiatric diseases; Severe endocrinopathies; Previous therapy of PWS within the last 4 weeks; Participation in any clinical studies within the last 4 weeks; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((> 1.5 ULN) AND (> 1.5 upper limit of normal [ULN]) AND (Allergic constitution) AND (Allergy) AND (Coagulation disorders) AND (Electrocardiographic) AND (Electrocardiographic abnormalities) AND (Hepatic functions) AND (Immunocompromised conditions) AND (PDT) AND (PWS) AND (Participation in any clinical studies) AND (Photosensitivity) AND (Porphyria) AND (Previous) AND (Psychiatric diseases) AND (Scar diathesis) AND (Severe) AND (abnormal) AND (alanine aminotransferase) AND (analogues) AND (aspartate transaminase) AND (blood urea nitrogen) AND (endocrinopathies) AND (heart diseases) AND (interfere with the efficacy evaluation) AND (isotope) AND (might interfere with the efficacy evaluation) AND (organic) AND (porphyrins) AND (renal functions) AND (serum creatinine) AND (skin diseases) AND (therapy) AND (total bilirubin) AND (treatment) AND (within the last 4 weeks))"}
{"candidate_id": "LLM05896", "doc_id": "NCT02566226_exc", "case_bucket": "other", "source_criterion": "planned surgical duration more than 3 hours contraindication to spinal anaesthesia severe respiratory disease patient known and treated for sleep apnea syndrome", "candidate_expression": "((contraindication) AND (planned surgical duration more than 3 hours) AND (respiratory disease severe) AND (sleep apnea syndrome) AND (spinal anaesthesia) AND (treated))"}
{"candidate_id": "LLM05897", "doc_id": "NCT02431559_exc", "case_bucket": "or", "source_criterion": "1. Prior exposure to doxorubicin, PLD or any other anthracycline, motolimod and other TLR agonists, MEDI4736 or checkpoint inhibitors, such as anti-CTLA4 and anti-PD1/anti-PD-L1 antibodies. 2. Subjects with platinum-refractory disease, defined as disease progression while receiving first line platinum-based therapy. 3. Clinically significant persistent immune-related adverse events following prior therapy. 4. Subjects with history or evidence upon physical examination of CNS disease, including primary brain tumor, seizures not controlled with standard medical therapy, any brain metastases, or, within six months prior to Day 1 of this study, history of cerebrovascular accident (CVA, stroke), transient ischemic attack (TIA) or subarachnoid hemorrhage. 5. Subjects with clinically significant cardiovascular disease. This includes: 1. Resisted hypertension 2. Myocardial infarction or unstable angina within 6 months prior to Day 1 of the study. 3. History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation) or cardiac arrhythmias requiring anti-arrhythmic medications, except for atrial fibrillation that is well controlled with anti-arrhythmic medication. 4. Baseline ejection fraction ≤ 50% as assessed by echocardiogram or MUGA. 5. New York Heart Association (NYHA) Class II or higher congestive heart failure. 6. Grade 2 or higher peripheral ischemia, except for brief (< 24 hrs) episodes of ischemia managed non-surgically and without permanent deficit. 6. History of pneumonitis or interstitial lung disease. 7. Active, suspected or prior documented autoimmune disease (including inflammatory bowel disease, celiac disease, Wegner's granulomatosis, active Hashimoto's thyroiditis, rheumatoid arthritis, lupus, scleroderma and its variants, multiple sclerosis, myasthenia gravis). Vitiligo, type I diabetes mellitus, residual hypothyroidism due to autoimmune condition only requiring hormone replacement, psoriasis not requiring systemic treatment, or conditions not expected to recur in the absence of an external trigger are permitted. 8. Other malignancy within 2 years prior to Day 1 of the study, except for those treated with surgical intervention only. 9. Subjects with clinical symptoms or signs of gastrointestinal obstruction and/or who require drainage gastrostomy tube and/or parenteral hydration or nutrition. 10. Known immunodeficiency or HIV, Hepatitis B or Hepatitis C positivity. 11. History of severe allergic reactions to any unknown allergens or components of the study drugs. 12. Other serious illnesses (e.g., serious infections requiring antibiotics, bleeding disorders). 13. Prior treatment in any other interventional clinical trial within 4 weeks prior to Day 1 of the study. 14. Mental impairment that may compromise compliance with the requirements of the study. 15. Lack of availability for immunological and clinical follow-up assessment. 16. Women who are breastfeeding or pregnant as evidenced by positive serum pregnancy test 17. Subjects unwilling to use acceptable methods of contraception. -Female subjects should refrain from breastfeeding throughout this period. 18. Any condition that, in the clinical judgment of the treating physician, is likely to prevent the subject from complying with any aspect of the protocol or that may put the subject at unacceptable risk. 19. Subjects must not donate blood while on study and for at least 90 days following the last MEDI4736 treatment. 20. History of allogeneic organ transplant", "candidate_expression": "((CNS disease) AND (CVA) AND (Clinically significant) AND (Female breastfeeding) AND (HIV) AND (Hashimoto's thyroiditis) AND (Hepatitis B) AND (Hepatitis C) AND (MEDI4736) AND (MUGA) AND (Mental impairment compromise compliance) AND (Myocardial infarction) AND (New York Heart Association (NYHA) Class II or higher) AND (PLD) AND (Resisted hypertension) AND (TLR agonists) AND (Vitiligo) AND (Wegner's granulomatosis) AND (Women) AND (allergic reactions History severe) AND (allogeneic organ transplant History) AND (anthracycline) AND (anti-CTLA4) AND (anti-PD-L1 antibodies) AND (anti-PD1 antibodies) AND (anti-arrhythmic medication) AND (anti-arrhythmic medications) AND (autoimmune condition requiring hormone replacement) AND (autoimmune disease) AND (bleeding disorders) AND (brain metastases) AND (breastfeeding) AND (cardiac arrhythmias History requiring anti-arrhythmic medications) AND (cardiovascular disease clinically significant) AND (celiac disease) AND (cerebrovascular accident) AND (checkpoint inhibitors) AND (clinical follow-up assessment) AND (clinical symptoms of gastrointestinal obstruction) AND (clinically significant) AND (conditions not expected to recur) AND (congestive heart failure) AND (contraception acceptable) AND (disease progression while receiving first line platinum-based therapy) AND (doxorubicin) AND (drainage gastrostomy tube) AND (echocardiogram) AND (ejection fraction Baseline ≤ 50%) AND (hormone replacement) AND (illnesses serious) AND (immune-related adverse events Clinically significant persistent following prior therapy) AND (immunodeficiency) AND (immunological follow-up assessment) AND (infections requiring antibiotics serious) AND (inflammatory bowel disease) AND (interstitial lung disease History) AND (ischemia brief) AND (lupus) AND (malignancy within 2 years prior to Day 1 of the study) AND (motolimod) AND (multiple sclerosis) AND (myasthenia gravis) AND (not expected to recur) AND (parenteral hydration) AND (parenteral nutrition) AND (peripheral ischemia Grade 2 or higher < 24 hrs) AND (platinum-refractory disease) AND (pneumonitis History) AND (pregnant) AND (primary brain tumor) AND (psoriasis requiring systemic treatment) AND (residual hypothyroidism due to autoimmune condition) AND (rheumatoid arthritis) AND (scleroderma) AND (scleroderma variants) AND (seizures controlled) AND (serious) AND (serum pregnancy test positive) AND (signs of gastrointestinal obstruction) AND (standard medical therapy) AND (stroke) AND (subarachnoid hemorrhage) AND (systemic treatment) AND (those) AND (to any unknown allergens or components of the study drugs) AND (transient ischemic attack (TIA)) AND (treatment Prior) AND (type I diabetes mellitus) AND (unstable angina) AND (unwilling) AND (ventricular arrhythmia History serious) AND (ventricular fibrillation) AND (ventricular tachycardia) AND NOT (surgically) AND NOT (permanent deficit) AND NOT (surgical intervention) AND NOT (donate blood while on study for at least 90 days following the last MEDI4736 treatment) AND NOT (atrial fibrillation well controlled with anti-arrhythmic medication))"}
{"candidate_id": "LLM05898", "doc_id": "NCT02330705_exc", "case_bucket": "or", "source_criterion": "Advanced male factor infertility. Polycystic ovary syndrome (PCOS) as defined by the Rotterdam criteria. Endometriosis. Tubal disease. Uterine abnormalities or myoma. Previous uterine surgery. Metabolic or hormonal abnormalities.", "candidate_expression": "((Endometriosis) AND (Polycystic ovary syndrome (PCOS) Rotterdam criteria) AND (Tubal disease) AND (male factor infertility Advanced) AND (uterine surgery Previous) AND ((Metabolic abnormalities) OR (hormonal abnormalities)) AND ((Uterine abnormalities) OR (myoma)))"}
{"candidate_id": "LLM05899", "doc_id": "NCT03196843_exc", "case_bucket": "or", "source_criterion": "Patients with a history of any other malignancy. Concomitant treatment with any other anticancer therapy. Patient have contraindication to chemotherapy(eg.uncontrolled coronarism and heart failure; History of myocardial infarction within the past 6 months, Chronic obstructive pulmonary, uncontrolled epileptic attack and other disease that investigator consider it unsuitable for the chemotherapy)", "candidate_expression": "((anticancer therapy any other) AND (chemotherapy) AND (contraindication) AND (malignancy history any other) AND (treatment Concomitant) AND (unsuitable for the chemotherapy) AND ((coronarism) OR (heart failure)) AND ((Chronic obstructive pulmonary) OR (disease other) OR (epileptic attack uncontrolled) OR (myocardial infarction History within the past 6 months)))"}
{"candidate_id": "LLM05900", "doc_id": "NCT02944604_inc", "case_bucket": "or", "source_criterion": "Severe or uncontrolled infection. Sensitive to the product or other genetically engineered biological products from Escherichia coli strains. Mental or nervous system disorders. Severe heart, lung and central nervous system disorders. Pregnant or lactating women. TBIL(total bilirubin ), ALT(alanine aminotransferase),AST(glutamic-oxalacetic transaminase) > 2.5×ULN(upper limit of normal); if it were caused by liver metastases, TBIL, ALT,AST >5×ULN. Cr(creatinine) >1.5×ULN.", "candidate_expression": "((> 2.5×ULN) AND (>1.5×ULN) AND (>5×ULN) AND (ALT) AND (AST) AND (Cr) AND (Escherichia coli strains) AND (Mental disorders) AND (Pregnant) AND (Sensitive) AND (Severe) AND (TBIL) AND (alanine aminotransferase) AND (creatinine) AND (entral nervous system disorders) AND (genetically engineered biological products) AND (glutamic-oxalacetic transaminase) AND (heart disorders) AND (infection) AND (lactating) AND (liver metastases) AND (lung disorders) AND (nervous system disorders) AND (other) AND (the product) AND (total bilirubin) AND (uncontrolled) AND (women))"}
```
