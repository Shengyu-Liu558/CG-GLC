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
{"candidate_id": "LLM01826", "doc_id": "NCT02632760_inc", "case_bucket": "or", "source_criterion": "Patients with anaemia (males Hb <130 g/L, females <120 g/L) undergoing elective cardiac surgery, and available to receive trial drug 1- 10 weeks prior to surgery", "candidate_expression": "((1- 10 weeks prior to surgery) AND (<120 g/L) AND (<130 g/L) AND (Hb) AND (anaemia) AND (available to receive) AND (cardiac surgery) AND (elective) AND (females) AND (males) AND (surgery) AND (trial drug))"}
{"candidate_id": "LLM01827", "doc_id": "NCT02379156_inc", "case_bucket": "other", "source_criterion": "Duration of SCI =1 year; Level of SCI C3-T1, AIS A & B; Age between 18 and 65 years.", "candidate_expression": "((=1 year) AND (A & B) AND (AIS) AND (Age) AND (C3-T1) AND (Level of SCI) AND (SCI) AND (between 18 and 65 years))"}
{"candidate_id": "LLM01828", "doc_id": "NCT03513874_exc", "case_bucket": "or", "source_criterion": "History of any malignancy or other severe diseases Female patients who are pregnant or breastfeeding before or during the three-year follow-up Poor compliance or refusal to participate.", "candidate_expression": "((Female patients who are pregnant or breastfeeding before or during the three-year follow-up) AND (Poor compliance) AND (malignancy) AND (refusal to participate) AND (severe diseases))"}
{"candidate_id": "LLM01829", "doc_id": "NCT02637076_exc", "case_bucket": "or", "source_criterion": "use of any sedative hypnotics, tranquilizers, anticonvulsants, antihistamines (except non-sedating), benzodiazepines, clonidine or any medication known to affect dopamine at start of baseline period significant unstable or uncontrolled medical/psychiatric disease significant history of head trauma/surgery or seizure disorder radiation exposure exceeding 20mSv in last 12 months pregnancy substance abuse/dependence (including alcohol) have sleep apnea, or are shift workers on a sodium-restricted diet has ever taken Xyrem / sodium oxybate / GHB at any time claustrophobia metal implants / objects in the body that may interfere with MRI succinic semialdehyde dehydrogenase deficiency", "candidate_expression": "((MRI may interfere with) AND (alcohol) AND (claustrophobia) AND (pregnancy) AND (radiation exposure exceeding 20mSv in last 12 months) AND (sodium-restricted diet) AND (succinic semialdehyde dehydrogenase deficiency) AND ((uncontrolled) OR (unstable)) AND ((medical disease) OR (psychiatric disease)) AND ((head surgery) OR (head trauma) OR (seizure disorder)) AND ((substance abuse) OR (substance dependence)) AND ((anticonvulsants) OR (antihistamines non-sedating) OR (benzodiazepines) OR (clonidine) OR (medication known to affect dopamine) OR (sedative hypnotics) OR (tranquilizers)) AND ((shift workers) OR (sleep apnea)) AND ((GHB) OR (Xyrem) OR (sodium oxybate)) AND ((metal implants) OR (metal objects)))"}
{"candidate_id": "LLM01830", "doc_id": "NCT03473132_exc", "case_bucket": "other", "source_criterion": "recent thrombotic event", "candidate_expression": "((recent) AND (thrombotic event))"}
{"candidate_id": "LLM01831", "doc_id": "NCT02620904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01832", "doc_id": "NCT00994786_exc", "case_bucket": "or", "source_criterion": "Patients with any other primary DSM-IV psychiatric diagnosis in addition to Obsessive Compulsive Disorder. Patients who currently fulfil criteria for DSM-IV eating disorder, body dysmorphic disorder, current alcohol or substance abuse, or who have a lifetime history of bipolar disorder. Patients with a history of Schizophrenia and other psychotic disorders, Delirium, Dementia, and Amnestic and other cognitive disorders. Subjects with a concurrent Axis II Cluster A Personality Disorder Borderline or Antisocial Personality Disorder. Subjects who based on history or mental status examination have a significant risk of committing suicide, in the investigator's opinion. Subjects with a history of more than three adequate trials with an SSRI. Subjects who have had an adequate trial of pregabalin. Subjects who have initiated psychotherapy in the last 4 months prior to the first visit. Subjects who, during the course of the study, would be likely to require treatment with prohibited concomitant therapy . Prior use of or a known allergy or hypersensitivity to pregabalin. Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study. Any subject who has been taking benzodiazepines before entering the study who: 1) cannot tolerate being free of benzodiazepines for 4 weeks, or 2) has signs or symptoms of benzodiazepine withdrawal or rebound at the end of those 4 weeks. Should a patient entering the study, who is currently on benzodiazepines develop discontinuation symptoms with discontinuation of their benzodiazepine, we will treat these symptoms with a more gradual benzodiazepine taper. Study will be delayed until the patient is able to tolerate the discontinuation for 4 weeks. Patients with a current seizure disorder, organic brain disorder or a history of seizure disorders (except for febrile seizures in childhood). Patients with thyroid pathology, the treatment of which has not been stabilized for at least three months. Patients on neuroleptic drugs in the two months prior to study entry or cognitive behavioural therapy specific to OCD within four weeks of study entry Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control. Patients with a history or evidence of a medical condition that would expose them to an increased risk of a significant adverse event or interfere with assessments of safety and efficacy during the trial. Patients receiving psychotropics of any kind, including betablockers and other anticonvulsants. Sleep medication such as oral chloral-hydrate or zopiclone are acceptable. Patients using any herbal psychoactive treatments, e.g. St John's Wort, Valerian, Kava Kava, L-tryptophan. Patients with any condition or on any therapy that, in the investigator's opinion, or as indicated in the pregabalin product label, may pose a risk to the subject. Patients who have had a major life event in the past three months, which in the judgement of the investigator is influencing their current condition. Patients having clinically significant abnormal laboratory, or ECG findings not resolved by further examinations.", "candidate_expression": "((Axis II Cluster A) AND (DSM-IV) AND (OCD) AND (Obsessive Compulsive Disorder) AND (Personality Disorder) AND (Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control) AND (Sleep medication) AND (Subjects who have had an adequate trial of pregabalin) AND (Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study.) AND (Subjects with a history of more than three adequate trials with an SSRI) AND (acceptable) AND (any other) AND (at least three months) AND (childhood) AND (except) AND (febrile seizures) AND (first visit) AND (herbal psychoactive treatments) AND (in addition to) AND (in the last 4 months prior to the first visit) AND (in the two months prior to study entry) AND (mental status examination) AND (not) AND (oral) AND (other) AND (pregabalin) AND (primary) AND (psychiatric diagnosis) AND (psychotherapy) AND (psychotropics) AND (risk of committing suicide) AND (significant) AND (significant abnormal) AND (stabilized) AND (study entry) AND (thyroid pathology) AND (treatment) AND (within four weeks of study entry) AND ((alcohol abuse) OR (body dysmorphic disorder) OR (eating disorder) OR (substance abuse)) AND ((Amnestic) OR (Delirium) OR (Dementia) OR (Schizophrenia) OR (bipolar disorder) OR (cognitive disorders) OR (psychotic disorders)) AND ((Antisocial Personality Disorder) OR (Borderline Personality Disorder)) AND ((allergy) OR (hypersensitivity)) AND ((history of seizure disorders) OR (organic brain disorder) OR (seizure disorder)) AND ((cognitive behavioural therapy) OR (neuroleptic drugs)) AND ((anticonvulsants) OR (betablockers)) AND ((chloral-hydrate) OR (zopiclone)) AND ((Kava Kava) OR (L-tryptophan) OR (St John's Wort) OR (Valerian)) AND ((ECG findings) OR (laboratory findings)))"}
{"candidate_id": "LLM01833", "doc_id": "NCT01184638_inc", "case_bucket": "or", "source_criterion": "Patients with informed consents Without basal disorders of neurology and psychiatrics", "candidate_expression": "((Patients with informed consents) AND (Without) AND (basal disorders of neurology) AND (basal disorders of psychiatrics))"}
{"candidate_id": "LLM01834", "doc_id": "NCT02068365_inc", "case_bucket": "or", "source_criterion": "Male & female patients >= 18 and < 70 years of age Positive HBeAg before starting NA treatment Treated by a single NA (lamivudine, adefovir, entecavir or tenofovir) for 6 months to 5 years Developed HBeAg seroconversion (HBeAg negative and ant-HBe negative) with undetectable HBV DNA by PCR based assay on NA treatment. Negative urine or serum pregnancy test (for women of childbearing potential) documented within the 24-hour period prior to the first dose of test drug. Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion", "candidate_expression": "((>= 18 and < 70 years) AND (Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion) AND (HBV DNA) AND (HBeAg) AND (Male) AND (NA) AND (Negative) AND (PCR based assay) AND (Positive) AND (Treated) AND (adefovir) AND (age) AND (ant-HBe) AND (before starting NA treatment) AND (childbearing potential) AND (entecavir) AND (female) AND (for 6 months to 5 years) AND (lamivudine) AND (negative) AND (seroconversion) AND (serum pregnancy test) AND (single) AND (starting NA treatment) AND (tenofovir) AND (the first dose of test drug) AND (treatment) AND (undetectable) AND (urine pregnancy test) AND (within the 24-hour period prior to the first dose of test drug) AND (women))"}
{"candidate_id": "LLM01835", "doc_id": "NCT02312076_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Myoma Previous) AND (Uterine abnormalities) AND (endometriosis Moderate severe) AND (uterine surgery))"}
{"candidate_id": "LLM01836", "doc_id": "NCT01009359_inc", "case_bucket": "or", "source_criterion": "Able to give fully informed consent in writing Males or females aged >/= 50 years No significant disease or drug use Absence of any sign of dementia/cognitive impairment in neuropsychological examinationsPatients for brain imaging: Patient and designee capable of giving fully informed consent in writing Patient fulfils DSM-IV and NINCDS-ADRA criteria for probable Alzheimers disease", "candidate_expression": "((Able to give fully informed consent in writing) AND (Alzheimers disease probable) AND (DSM-IV criteria fulfils) AND (Males) AND (NINCDS-ADRA criteria fulfils) AND (Patient and designee capable of giving fully informed consent in writing) AND (aged >/= 50 years) AND (cognitive impairment) AND (dementia) AND (disease significant) AND (drug use) AND (females) AND (neuropsychological examinations) AND (sign of cognitive impairment) AND (sign of dementia) AND (significant))"}
{"candidate_id": "LLM01837", "doc_id": "NCT02635893_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease, Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke, Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold such as antipsychotic drugs (chlorpromazine, clozapine) or tricyclic antidepressants. Pregnant females, and Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida or herniated cervical disk. Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease, Any debilitating disease that causes exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke, Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold such as antipsychotic drugs (chlorpromazine, clozapine) or tricyclic antidepressants. Pregnant females, and Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida or herniated cervical disk.", "candidate_expression": "((History) AND (History of) AND (Metal plate in skull) AND (Pregnant) AND (Premorbid) AND (Uncontrolled) AND (altered cognitive status) AND (antipsychotic drugs) AND (cardiovascular disease) AND (chlorpromazine) AND (clozapine) AND (cord compression) AND (debilitating disease) AND (drugs acting primarily on the central nervous system) AND (exercise intolerance) AND (females) AND (head injury) AND (herniated cervical disk) AND (lower the seizure threshold) AND (major depression) AND (medical problems) AND (ongoing) AND (orthopedic disease) AND (prior to the SCI) AND (psychosis) AND (pulmonary disease) AND (seizures) AND (spina bifida) AND (spinal cord) AND (spinal cord disease) AND (spinal stenosis) AND (stroke) AND (syrinx) AND (tricyclic antidepressants))"}
{"candidate_id": "LLM01838", "doc_id": "NCT03026465_inc", "case_bucket": "or", "source_criterion": "Patients older than 18 years Ischemic symptoms or evidence of myocardial ischemia (inducible or spontaneous) in the presence of >50% de novo stenosis located in native coronary vessels", "candidate_expression": "((stenosis >50% de novo) AND (stenosis native coronary vessels) AND (years older than 18) AND ((Ischemic symptoms) OR (myocardial ischemia evidence)) AND ((inducible) OR (spontaneous)))"}
{"candidate_id": "LLM01839", "doc_id": "NCT02882113_exc", "case_bucket": "or", "source_criterion": "Patients who have Tacrolimus trough level resulted as 2 ng/mg at the baseline. Patients who are on steroid therapy due to positive result of acute rejection test before the baseline. Patients who have received a transplant besides liver. Patients who are allergic to IP or macrolide compounds. Patients who are on cyclosporine, bosentan, or potassium sparing diuretic. Patients with genetic diseases such as galactose intolerance, Lapp lactase deficiency, or glucose-galactose malabsorption. Pregnant or lactating women. Patients not willing to adhere to study procedures/treatments.", "candidate_expression": "((2 ng/mg) AND (Patients not willing to adhere to study procedures/treatments) AND (Pregnant or lactating women) AND (Tacrolimus) AND (acute rejection test) AND (allergic) AND (genetic diseases) AND (liver) AND (positive) AND (steroid) AND (transplant) AND ((IP) OR (macrolide)) AND ((bosentan) OR (cyclosporine) OR (potassium sparing diuretic)) AND ((Lapp lactase deficiency) OR (galactose intolerance) OR (glucose-galactose malabsorption)))"}
{"candidate_id": "LLM01840", "doc_id": "NCT03355326_exc", "case_bucket": "or", "source_criterion": "Neurological Congenital malformations and/or those known to impair intestinal motility Additional congenital gastrointestinal abnormalities requiring surgical intervention Congenital Cyanotic heart disease Surgical Closure of abdominal wall defect with prosthetic material (e.g. prosthetic or bio-prosthetic mesh)", "candidate_expression": "((Additional) AND (Congenital) AND (Cyanotic heart disease) AND (Surgical Closure) AND (abdominal wall defect) AND (congenital) AND (gastrointestinal abnormalities) AND (prosthetic material) AND (requiring) AND (surgical intervention) AND ((Neurological Congenital malformations) OR (impair intestinal motility)) AND ((bio-prosthetic mesh) OR (prosthetic mesh)))"}
{"candidate_id": "LLM01841", "doc_id": "NCT02034019_exc", "case_bucket": "other", "source_criterion": "Any intraocular inflammation in the study eye present during the screening slit lamp examination Score greater than \"0\" on the Ocular Pain Assessment in the study eye at Screening Any intraocular inflammation in the study eye present during the screening slit lamp examination", "candidate_expression": "((Ocular Pain Assessment greater than \"0\" at Screening) AND (intraocular inflammation) AND (intraocular inflammation the screening slit lamp examination) AND (slit lamp examination intraocular inflammation during the screening slit lamp examination))"}
{"candidate_id": "LLM01842", "doc_id": "NCT02867618_inc", "case_bucket": "or", "source_criterion": "Phase I: Patients must have histologically confirmed R/R NHL or HL (defined by WHO criteria). Patients with chronic lymphocytic leukemia (CLL) and small lymphocytic lymphoma (SLL) are eligible. In addition, patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL and HL will be eligible if there is no available standard therapy. Phase II: Patients must have histologically confirmed R/R NHL (as defined by WHO criteria). Patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL will be eligible if there is no available standard therapy. Must have received front line chemotherapy. No upper limit for the number of prior therapies Evaluable Disease in the Phase I, and measurable disease in the Phase II Age > 18 years ECOG performance status < 2 Patients must have adequate organ and marrow function Adequate Contraception Ability to understand and the willingness to sign a written informed consent document", "candidate_expression": "((Ability to understand and the willingness to sign a written informed consent document) AND (Adequate) AND (Age > 18 years in the Phase II) AND (Contraception Adequate) AND (DLBCL) AND (Disease measurable in the Phase I) AND (ECOG performance status < 2) AND (NHL) AND (NHL R/R) AND (WHO criteria) AND (adequate) AND (chemotherapy front line) AND (histologically confirmed) AND (marrow function adequate) AND (organ function adequate) AND (therapies at least 2 prior) AND NOT (diffuse large B cell lymphomas (DLBCL)) AND NOT (standard therapy) AND ((chronic lymphocytic leukemia (CLL)) OR (small lymphocytic lymphoma (SLL))) AND ((DLBCL) OR (HL)) AND ((HL) OR (NHL)))"}
{"candidate_id": "LLM01843", "doc_id": "NCT03434951_inc", "case_bucket": "other", "source_criterion": "elective primary total knee arthroplasty ASA I-III written consent", "candidate_expression": "((ASA) AND (I-III) AND (elective) AND (primary) AND (total knee arthroplasty) AND (written consent))"}
{"candidate_id": "LLM01844", "doc_id": "NCT01994382_exc", "case_bucket": "or", "source_criterion": "Richter's syndrome, Burkitt's lymphoma, or Burkitt-like Lymphoma (transformed DLBCL from Follicular NHL are eligible). Prior transplant with stem cell infusion 90 days or active graft-versus-host treatment within 8 weeks of Day 1. Prior therapy with SYK inhibitors. Chronic treatment with strong CYP3A4 inhibitor/ inducer, acid reducing agent, Proton pump inhibitors Known lymphomatous involvement of the CNS. Persistent, unresolved NCI CTCAE v4.0 ≥ Grade 2, previous drug-related toxicity (except alopecia, erectile impotence, hot flashes, libido, neuropathy). Prior monoclonal antibody, radioimmunoconjugate, antibody drug conjugate, phototherapy, radiotherapy, chemotherapy, immunotherapy, immunosuppressive therapy, or any test agent within 3 weeks or for alemtuzumab 8 weeks of Day 1. For CTCL: (TSEBT) within 12 weeks, or initiation of topical steroid, nitrogen mustard, or topical retinoid within 2 weeks. (Stable topical ≥ 4 weeks prior to Day 1 allowed). Known carrier or infection for HIV/Hep B or C. HCV ab+ must be PCR-. HBV ab+ must be HBsAg- or undetectable DNA Active infection requiring systemic treatment, Significant GI disease, previous major gastric/bowel surgery, difficulty swallowing or malabsorption syndrome. Major surgery within 4 weeks Previous malignancies within 2 yrs. unless relapse risk is small (< 5%). Current use of systemic steroids >20 mg QD prednisone (or equivalent) Breastfeeding or pregnant (intention to become) females or participation in other clinical trials", "candidate_expression": "((Breastfeeding) AND (Burkitt's lymphoma) AND (Burkitt-like Lymphoma) AND (CTCL) AND (DLBCL) AND (Follicular NHL) AND (GI disease Significant) AND (HBV ab+ HBsAg-) AND (HCV ab+ PCR-) AND (Hep B infection for) AND (Hep C infection for) AND (Major) AND (NCI CTCAE v4.0 ≥ Grade 2) AND (Proton pump inhibitors) AND (Richter's syndrome) AND (SYK inhibitors) AND (Significant) AND (TSEBT within 12 weeks) AND (acid reducing agent) AND (alemtuzumab 8 weeks of Day 1) AND (alopecia) AND (antibody drug conjugate) AND (bowel surgery) AND (chemotherapy) AND (difficulty swallowing) AND (drug-related toxicity previous) AND (erectile impotence) AND (females) AND (gastric surgery) AND (graft-versus-host treatment active within 8 weeks of Day 1) AND (hot flashes) AND (immunosuppressive therapy within 3 weeks of Day 1) AND (immunotherapy) AND (infection for HIV) AND (infection requiring systemic treatment) AND (libido) AND (lymphomatous involvement of the CNS) AND (major) AND (malabsorption syndrome) AND (malignancies within 2 yrs.) AND (monoclonal antibody) AND (neuropathy) AND (nitrogen mustard) AND (phototherapy) AND (prednisone >20 mg QD) AND (pregnant) AND (radioimmunoconjugate) AND (radiotherapy) AND (stem cell infusion) AND (strong CYP3A4 inducer) AND (strong CYP3A4 inhibitor) AND (surgery Major within 4 weeks) AND (systemic steroids) AND (systemic treatment) AND (therapy Prior) AND (topical retinoid ≥ 4 weeks prior to Day 1) AND (topical steroid initiation) AND (transplant Prior 90 days of Day 1) AND (undetectable DNA) AND (unless relapse risk is small (< 5%)))"}
{"candidate_id": "LLM01845", "doc_id": "NCT02759861_exc", "case_bucket": "or", "source_criterion": "Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active. Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety. Malignancy diagnosed or treated within 5 years (recent localized treatment of squamous or non-invasive basal cell skin cancers is permitted; cervical carcinoma in situ is allowed if appropriately treated prior to screening); subjects under evaluation for a malignancy are not eligible. Infection with hepatitis B virus (HBV) or human immunodeficiency virus (HIV) Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit. Known hypersensitivity to LDV/SOF", "candidate_expression": "((Malignancy) AND (Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active.) AND (Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety.) AND (Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit.) AND (allowed) AND (appropriately) AND (cervical carcinoma in situ) AND (hypersensitivity) AND (localized) AND (permitted) AND (prior to screening) AND (recent) AND (treated) AND (treatment) AND (within 5 years) AND ((hepatitis B virus (HBV)) OR (human immunodeficiency virus (HIV))) AND ((LDV) OR (SOF)) AND ((non-invasive basal cell skin cancer) OR (squamous cell skin cancer)))"}
{"candidate_id": "LLM01846", "doc_id": "NCT03199560_inc", "case_bucket": "or", "source_criterion": "Women above 18 years of age with biopsy proven, clinically stage 1 or 2 breast cancer who will be undergoing partial mastectomy with SLNBx at Memorial Health", "candidate_expression": "((SLNBx) AND (Women) AND (above 18 years) AND (age) AND (at Memorial Health) AND (biopsy) AND (breast cancer) AND (partial mastectomy) AND (will be undergoing) AND ((stage 1) OR (stage 2)))"}
{"candidate_id": "LLM01847", "doc_id": "NCT01312012_exc", "case_bucket": "or", "source_criterion": "major systemic disease Pregnant woman with infection of human immunodeficiency virus or hepatitis C virus Pregnant woman is receiving any drug with antiviral activity or any form of drug therapy for hepatitis B virus Pregnant woman whose ultrasonographic examination reveals congenital anomaly of the fetus Pregnant woman whose amniocentesis reveals any genetic abnormality", "candidate_expression": "((Pregnant) AND (amniocentesis) AND (congenital anomaly of the fetus) AND (drug therapy) AND (drug with antiviral activity) AND (genetic abnormality) AND (hepatitis B virus) AND (hepatitis C virus) AND (human immunodeficiency virus) AND (major systemic disease) AND (ultrasonographic examination) AND (woman))"}
{"candidate_id": "LLM01848", "doc_id": "NCT03320057_exc", "case_bucket": "other", "source_criterion": "Not pregnant Not seeking medication abortion Under the age of 15 Contraindications for medication abortion", "candidate_expression": "((Contraindications) AND (age Under 15) AND (medication abortion) AND (pregnant))"}
{"candidate_id": "LLM01849", "doc_id": "NCT01313676_exc", "case_bucket": "or", "source_criterion": "Pregnancy: Women who are pregnant or lactating. Asthma: Subjects with a current diagnosis of asthma. (Subjects with a prior history of asthma are eligible if they also have a current diagnosis of COPD). alpha 1-antitrypsin deficiency: Subjects with known alpha-1 antitrypsin deficiency as the underlying cause of COPD. Other respiratory disorders: Subjects with active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, pulmonary fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. Lung resection or transplantation: Subjects with lung volume reduction surgery within the 12 months prior to Screening or having had a lung transplant. A moderate/severe COPD exacerbation that has not resolved at least 14 days prior to Visit 1 and at least 30 days following the last dose of oral corticosteroids (if applicable). Current severe heart failure (New York Heart Association class IV). Subjects will also be excluded if they have a known ejection fraction of <30% or if they have an implantable cardioverter defibrillator (ICD). Other diseases/abnormalities: Any life-threatening condition with life expectancy <3 years, other than vascular disease or COPD, that might prevent the subject from completing the study. End stage chronic renal disease: Subjects will be excluded if on renal replacement therapy (hemodialysis or peritoneal). Drug/food allergy: Subjects with a history of hypersensitivity to any of the study medications (e.g. beta-agonists, corticosteroid) or components of the inhalation powder (e.g. lactose, magnesium stearate). In addition, patients with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates the subject's participation will also be excluded. Drug/alcohol abuse: Subjects with a known or suspected history of alcohol or drug abuse within the last 2 years. Oxygen therapy: Subjects receiving treatment with long-term oxygen therapy (LTOT) or nocturnal oxygen therapy required for greater than 12 hours a day. Oxygen prn use (i.e. <=12 hours per day) is not exclusionary. Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures. Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study. Additional medication: Use of the following medications within the following time intervals prior to Visit 1 or during the study (unless otherwise specified): Medication No use within the following time intervals prior to Screening or thereafter at any time during the study (unless otherwise specified) Inhaled Long acting beta-agonists (LABA) 48 hours ICS/LABA combination products 48 hours Inhaled corticosteroids 48 hours Tiotropium 1 week Systemic, Oral, parenteral, intra-articular corticosteroids 30 days (oral and systemic corticosteroids may be used to treat COPD exacerbations during the study) Cytochrome P450 3A4 strong inhibitors including but not limited to antiretrovirals (protease inhibitors) (e.g.Indinavir, Nelfinavir, Ritonavir, Saquinavir); Imidazole and Triazole anti-fungals (e.g. Ketaconazole, Itraconazole); Clarithromycin, Telithromycin, Amiodarone, and Nefazodone 6 weeks Grapefruit is allowed up to Visit 1, then limited to no more than one glass of grapefruit juice (250 mL/ 8 ounces) or one grapefruit per day Any other investigational drug 30 days or 5 half lives whichever is longer.", "candidate_expression": "((Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study.) AND (Amiodarone) AND (Asthma current) AND (COPD) AND (COPD exacerbation resolved) AND (COPD exacerbations) AND (Clarithromycin) AND (Cytochrome P450 3A4 strong inhibitors 6 weeks) AND (Drug abuse) AND (Drug allergy) AND (End stage chronic renal disease) AND (Grapefruit) AND (ICS/LABA combination products 48 hours) AND (Imidazole anti-fungals) AND (Indinavir) AND (Inhaled Long acting beta-agonists (LABA) 48 hours) AND (Inhaled corticosteroids 48 hours) AND (Itraconazole) AND (Ketaconazole) AND (Lung resection) AND (Nefazodone) AND (Nelfinavir) AND (New York Heart Association class IV) AND (No) AND (Other respiratory disorders) AND (Pregnancy: Women who are pregnant or lactating.) AND (Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures.) AND (Ritonavir) AND (Saquinavir) AND (Screening) AND (Telithromycin) AND (Tiotropium 1 week Systemic Oral parenteral) AND (Triazole anti-fungals) AND (active pulmonary diseases) AND (alcohol abuse) AND (alpha 1-antitrypsin deficiency) AND (alpha-1 antitrypsin deficiency) AND (antiretrovirals) AND (any time during the study) AND (asthma current) AND (asthma prior history) AND (beta-agonists) AND (bronchiectasis) AND (components of the inhalation powder) AND (corticosteroid) AND (corticosteroids) AND (corticosteroids 30 days intra-articular oral systemic) AND (drug abuse) AND (ejection fraction <30%) AND (food allergy) AND (having had a lung transplant moderate severe) AND (heart failure severe) AND (hemodialysis peritoneal) AND (hypersensitivity) AND (implantable cardioverter defibrillator (ICD)) AND (in the opinion of the study physician, contraindicates the subject's participation will also be excluded) AND (interstitial lung diseases) AND (investigational drug 30 days 5 half lives) AND (lactose) AND (life-threatening condition life expectancy) AND (long-term oxygen therapy (LTOT)) AND (lung cancer) AND (lung transplant) AND (lung volume reduction surgery) AND (magnesium stearate) AND (milk protein allergy history severe) AND (nocturnal oxygen therapy) AND (protease inhibitors) AND (pulmonary fibrosis) AND (pulmonary hypertension) AND (renal replacement therapy) AND (sarcoidosis) AND (study medications) AND (that might prevent the subject from completing the study) AND (transplantation) AND (treat COPD exacerbations during the study) AND (tuberculosis) AND (vascular disease) AND (with lung volume reduction surgery within the 12 months prior to Screening))"}
{"candidate_id": "LLM01850", "doc_id": "NCT02284737_inc", "case_bucket": "or", "source_criterion": "Provision of informed consent prior to any study specific procedures; Men and women 18 years and older; Group I PAH, defined as a mPAP=25mmHg, PCWP<15mmHg and PVR[The PVR =(mPAP-PCWP)/CO]>3.0 Woods unit.", "candidate_expression": "(((mPAP-PCWP)/CO) AND (18 years and older) AND (<15mmHg) AND (=25mmHg) AND (>3.0 Woods unit) AND (Group I) AND (Men) AND (PAH) AND (PCWP) AND (PVR) AND (mPAP) AND (women) AND (years))"}
```
