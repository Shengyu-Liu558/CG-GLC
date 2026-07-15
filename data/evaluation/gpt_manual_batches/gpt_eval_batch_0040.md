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
{"candidate_id": "LLM00976", "doc_id": "NCT02689024_inc", "case_bucket": "other", "source_criterion": "adult patients aged = 55 years with a radiographically confirmed hip fracture", "candidate_expression": "((adult) AND (aged = 55 years) AND (hip fracture) AND (radiographically))"}
{"candidate_id": "LLM00977", "doc_id": "NCT02934269_exc", "case_bucket": "or", "source_criterion": "Exposure/treatment to an investigational (new chemical entity) or marketed drug or biologic within 30 days preceding the first dose administration, or five half-lives of that investigational drug or biologic, if known (whichever is longer). Donation blood or serum within 8 weeks before the first dose administration to a blood bank or blood donation center. History of alcohol or drug abuse (as defined by the current version of the DSM) within 2 years before the first dose administration, or positive alcohol or drug screen. Vaccination within 30 days prior to the first dose administration or has plans to receive a vaccination during the course of the study (including the follow phone call on Day 105).", "candidate_expression": "((Donation blood) AND (Donation serum) AND (History) AND (Vaccination) AND (alcohol abuse) AND (alcohol screen) AND (current version of the DSM) AND (drug abuse) AND (drug screen) AND (during the course) AND (first dose administration) AND (plans) AND (positive) AND (study) AND (the first dose administration) AND (vaccination) AND (within 2 years before) AND (within 30 days prior) AND (within 8 weeks before))"}
{"candidate_id": "LLM00978", "doc_id": "NCT02035904_inc", "case_bucket": "or", "source_criterion": "F; age 18 to 70 American Society of Anesthesiologists (ASA) I e II; breast cancer ( DIN 2 e 3, o LIN 2 e 3 sec. Tavassoli) scheduled for nipple-sparing mastectomy, simple mastectomy, skin-sparing mastectomy, skin-reducing mastectomy c, lymphnode biopsy and axillary dissection; immediate sub-pectoral prosthetic reconstruction; signed informed consent.", "candidate_expression": "((18 to 70) AND (2 e 3) AND (2 e 3 sec) AND (American Society of Anesthesiologists (ASA)) AND (F) AND (I e II) AND (age) AND (immediate) AND (scheduled for) AND (sub-pectoral prosthetic reconstruction) AND ((axillary dissection) OR (breast cancer) OR (lymphnode biopsy) OR (nipple-sparing mastectomy) OR (simple mastectomy) OR (skin-reducing mastectomy) OR (skin-sparing mastectomy)) AND ((DIN) OR (LIN)))"}
{"candidate_id": "LLM00979", "doc_id": "NCT03247413_exc", "case_bucket": "or", "source_criterion": "patient not previously scheduled for radiofrequency ablation of the cervical, thoracic, or lumbar facets, or sacroiliac joints on anticoagulation have a pacemaker age less than 18 years old non-English speaking", "candidate_expression": "((age less than 18 years old) AND (anticoagulation) AND (anticoagulation sacroiliac joints) AND (pacemaker) AND NOT (English speaking) AND NOT (radiofrequency ablation previously scheduled for cervical facets thoracic facets lumbar facets))"}
{"candidate_id": "LLM00980", "doc_id": "NCT03164096_exc", "case_bucket": "or", "source_criterion": "Patients with coagulopathy or under anti-coagulation therapy. Gastrointestinal disease, motion sickness. diabetes mellitus. Patients with preeclampsia,", "candidate_expression": "((Gastrointestinal disease) AND (diabetes mellitus) AND (motion sickness) AND (preeclampsia) AND ((anti-coagulation therapy) OR (coagulopathy)))"}
{"candidate_id": "LLM00981", "doc_id": "NCT02804126_inc", "case_bucket": "other", "source_criterion": "obtained consent singleton pregnancy subarachnoid anaesthesia", "candidate_expression": "((pregnancy singleton) AND (subarachnoid anaesthesia))"}
{"candidate_id": "LLM00982", "doc_id": "NCT03208998_inc", "case_bucket": "or", "source_criterion": "HBsAg and HBeAg positive for more than 6 months, HBV DNA detectable with ALT level abnormal lasted for three months and at least time190 IU/L or liver puncture biopsy demonstrated apparent inflammation, never treated before enrolled.", "candidate_expression": "((ALT level abnormal 190 IU/L) AND (HBV DNA detectable) AND (HBeAg positive) AND (HBsAg positive) AND (enrolled) AND (inflammation) AND (liver puncture biopsy) AND NOT (treated before enrolled))"}
{"candidate_id": "LLM00983", "doc_id": "NCT03208127_exc", "case_bucket": "or", "source_criterion": "Pregnant or nursing (lactating) women HIV positivity Need for dual organ transplant Any contra-indication to liver transplantation per center protocol", "candidate_expression": "((HIV positivity) AND (Pregnant) AND (contra-indication) AND (dual organ transplant Need for) AND (lactating) AND (liver transplantation) AND (nursing) AND (women))"}
{"candidate_id": "LLM00984", "doc_id": "NCT03154931_inc", "case_bucket": "other", "source_criterion": "Clinical Administered PTSD Scale 5 Monthly version Criteria A and >30 points", "candidate_expression": "(Clinical Administered PTSD Scale Criteria A >30 points)"}
{"candidate_id": "LLM00985", "doc_id": "NCT03513757_inc", "case_bucket": "other", "source_criterion": "All children scheduled for outpatient MRI scans with expected duration of scan between 30 minutes and 75 minutes.", "candidate_expression": "((MRI scans) AND (between 30 minutes and 75 minutes) AND (expected duration of scan) AND (outpatient))"}
{"candidate_id": "LLM00986", "doc_id": "NCT02375295_inc", "case_bucket": "or", "source_criterion": "Male or Female. No age restriction. Diagnosed with an infection related stone. Medically fit for definitive surgical management of stone. Life expectancy greater than one year. Stone free after definitive surgical therapy defined as fragments less than 3mm.", "candidate_expression": "((Life expectancy greater than one year) AND (definitive surgical management Medically fit for) AND (definitive surgical therapy fragments less than 3mm) AND (stone) AND (stone infection related) AND NOT (Stone) AND ((Female) OR (Male)))"}
{"candidate_id": "LLM00987", "doc_id": "NCT02219880_inc", "case_bucket": "or", "source_criterion": "Aged between 18-70 years Meets the Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria for generalised anxiety disorder (GAD) based on structured interview (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]. Note that while the MINI-Plus 6 uses the DSM-IV criteria, the same criteria are used in the DSM-V). Presents with anxiety (Hamilton Anxiety Rating Scale = 18) at the time of study entry Fluent in written and spoken English Provides a signed copy of the consent form Primary diagnosis other than GAD Presentation of moderate to severe depressive symptoms (Montgomery-Asberg Rating Scale: MADRS = 18 at time of study entry or = 24 at any time during study) Presentation of suicidal ideation (= 3 on MADRS suicidal thoughts domain at time of study entry or at any time during study) Current diagnosis of bipolar disorder or schizophrenia on structured interview (MINI Plus) Current substance/alcohol use disorder on structured interview (MINI Plus) Page 21 of 39 Commercial-in-Confidence Currently taking an antidepressant, mood stabiliser, antipsychotic, anticonvulsant, warfarin or thyroxin, or current regular use (more than 2 days per week) of a benzodiazepine or opioid-based analgesic Current use of a psychotropic nutraceutical (e.g. St John's wort) Previous intolerance to kava Three or more failed trials of pharmacotherapy for the current GAD episode Recently commenced psychotherapy (within four weeks of study entry) Known or suspected clinically unstable systemic medical disorder Diagnosed hepato-biliary disease/inflammation Elevated liver enzymes at baseline blood test Pregnancy or breastfeeding, or trying to conceive Not using medically approved contraception (including abstinence) if female and of childbearing age Unable to participate in all scheduled visits, treatment plan, or other trial procedures according to the protocol (except for the optional genetic component)", "candidate_expression": "((= 18) AND (= 3) AND (Aged) AND (Current) AND (Currently) AND (Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria) AND (Elevated) AND (GAD) AND (GAD episode) AND (Hamilton Anxiety Rating Scale) AND (MADRS) AND (MADRS suicidal thoughts domain) AND (MINI Plus) AND (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]) AND (Montgomery-Asberg Rating Scale) AND (Not) AND (Previous) AND (Primary diagnosis) AND (Recently) AND (St John's wort) AND (Three or more) AND (Unable to participate) AND (abstinence) AND (age) AND (anxiety) AND (at any time during study) AND (at the time of study entry) AND (at time of study entry) AND (baseline) AND (between 18-70 years) AND (blood test) AND (childbearing) AND (childbearing age) AND (clinically unstable) AND (contraception) AND (current) AND (depressive symptoms) AND (except for) AND (failed) AND (female) AND (generalised anxiety disorder) AND (genetic component) AND (intolerance) AND (kava) AND (liver enzymes) AND (medical disorder) AND (medically approved) AND (moderate to severe) AND (more than 2 days per week) AND (other than) AND (psychotherapy) AND (psychotropic nutraceutical) AND (regular) AND (structured interview) AND (suicidal ideation) AND (systemic) AND (time of study entry) AND (trials of pharmacotherapy) AND (use) AND (within four weeks of study entry) AND ((scheduled visits) OR (treatment plan) OR (trial procedures)) AND ((= 18) OR (= 24)) AND ((at any time during study) OR (at time of study entry)) AND ((bipolar disorder) OR (schizophrenia)) AND ((alcohol use disorder) OR (substance use disorder)) AND ((taking) OR (use)) AND ((anticonvulsant) OR (antidepressant) OR (antipsychotic) OR (mood stabiliser) OR (thyroxin) OR (warfarin)) AND ((benzodiazepine) OR (opioid-based analgesic)) AND ((Known) OR (suspected)) AND ((hepato-biliary disease) OR (hepato-biliary inflammation)) AND ((Pregnancy) OR (breastfeeding) OR (trying to conceive)))"}
{"candidate_id": "LLM00988", "doc_id": "NCT03196843_exc", "case_bucket": "or", "source_criterion": "Patients with a history of any other malignancy. Concomitant treatment with any other anticancer therapy. Patient have contraindication to chemotherapy(eg.uncontrolled coronarism and heart failure; History of myocardial infarction within the past 6 months, Chronic obstructive pulmonary, uncontrolled epileptic attack and other disease that investigator consider it unsuitable for the chemotherapy)", "candidate_expression": "((Concomitant) AND (History) AND (anticancer therapy) AND (any other) AND (chemotherapy) AND (contraindication) AND (history) AND (malignancy) AND (other) AND (treatment) AND (uncontrolled) AND (unsuitable for the chemotherapy) AND (within the past 6 months) AND ((coronarism) OR (heart failure)) AND ((Chronic obstructive pulmonary) OR (disease) OR (epileptic attack) OR (myocardial infarction)))"}
{"candidate_id": "LLM00989", "doc_id": "NCT01774019_inc", "case_bucket": "or", "source_criterion": "Age 18 or older Willing and able to comply with the study procedures and provide written informed consent to participate in the study Diagnosis of probable pancreatic cancer, distal common bile duct (CBD) cholangiocarcinoma and other periampullary cancers (histology not required) Biliary obstructive symptoms or signs Bilirubin level at/above 100 umol per liter (5.8 mg/dL) Distal biliary obstruction consistent with pancreatic cancer, distal CBD cholangiocarcinoma or other periampullary malignancy Location of distal biliary obstruction is such that it would allow the proximal end of a stent to be positioned at least 2cm from the hilum Patients deemed as resectable by pancreatic protocol CT or MRI Surgical candidate per pancreatobiliary surgeon after multi-disciplinary discussion Surgery intent within 4 weeks Endoscopic and surgical treatment to be provided by same team", "candidate_expression": "((18 or older) AND (Age) AND (Bilirubin level) AND (Distal biliary obstruction) AND (Surgery) AND (Surgical candidate) AND (at least 2cm from the hilum) AND (at/above 100 umol per liter) AND (at/above 5.8 mg/dL) AND (deemed as resectable) AND (distal biliary obstruction) AND (intent) AND (other) AND (per pancreatobiliary surgeon) AND (probable) AND (stent) AND (within 4 weeks) AND (would allow) AND ((Biliary obstructive signs) OR (Biliary obstructive symptoms)) AND ((distal CBD cholangiocarcinoma) OR (pancreatic cancer) OR (periampullary malignancy)) AND ((pancreatic protocol CT) OR (pancreatic protocol MRI)) AND ((Endoscopic treatment) OR (surgical treatment)) AND ((distal common bile duct (CBD) cholangiocarcinoma) OR (pancreatic cancer) OR (periampullary cancers)))"}
{"candidate_id": "LLM00990", "doc_id": "NCT03430284_exc", "case_bucket": "or", "source_criterion": "type 1 diabetes,specific types of diabetes,gestational diabetes or pregestational diabetes; acute cardiovascular or cerebrovascular accidents within past 3 months; severe hepatic or renal dysfunction; malignant tumor; allergic history or contraindication for any drugs in trials; taking part in other clinical trials; obviously poor compliance.", "candidate_expression": "((acute) AND (any) AND (drugs in trials) AND (history) AND (malignant tumor) AND (obviously) AND (poor compliance) AND (severe) AND (specific types) AND (taking part in other clinical trials) AND (within past 3 months) AND ((hepatic dysfunction) OR (renal dysfunction)) AND ((allergic) OR (contraindication)) AND ((diabetes) OR (gestational diabetes) OR (pregestational diabetes) OR (type 1 diabetes)) AND ((accidents cardiovascular) OR (cerebrovascular accidents)))"}
{"candidate_id": "LLM00991", "doc_id": "NCT02946918_exc", "case_bucket": "or", "source_criterion": "AJCC Stage III or greater Undifferentiated, Anaplastic or Medullary Thyroid Cancer Planned postoperative TSH goal other than 0.1-0.5 mU/L History of gastrointestinal malabsorption or gastric bypass surgery Pregnancy Use of medications that alter the absorption or metabolism of levothyroxine Prior use of levothyroxine", "candidate_expression": "((AJCC Stage III or greater) AND (Anaplastic Thyroid Cancer) AND (Medullary Thyroid Cancer) AND (Pregnancy) AND (TSH postoperative 0.1-0.5 mU/L) AND (Undifferentiated Thyroid Cancer) AND (absorption of levothyroxine) AND (gastric bypass surgery) AND (gastrointestinal malabsorption) AND (levothyroxine) AND (levothyroxine Prior) AND (medications) AND (metabolism of levothyroxine))"}
{"candidate_id": "LLM00992", "doc_id": "NCT02715518_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00993", "doc_id": "NCT03129555_inc", "case_bucket": "or", "source_criterion": "A diagnosis of VTE in outpatient clinic or as discharge diagnosis after hospitalization. A claimed prescription of a NOAC from a Danish pharmacy within 14 days of discharge or outpatient clinic visit.", "candidate_expression": "((Danish pharmacy) AND (NOAC) AND (VTE) AND (after hospitalization) AND (claimed) AND (discharge) AND (discharge diagnosis) AND (discharge or outpatient clinic visit) AND (hospitalization) AND (outpatient clinic) AND (outpatient clinic visit) AND (prescription) AND (within 14 days of discharge or outpatient clinic visit))"}
{"candidate_id": "LLM00994", "doc_id": "NCT01665417_inc", "case_bucket": "or", "source_criterion": "Pathologic confirmation of lung adenocarcinoma with measurable disease, defined as at least one lesion that can be accurately measured in at least one dimension (longest diameter to be recorded on CT); Patients must have previously untreated locally advanced or metastatic NSCLC; Patients must have lung cancer with a documented EGFR activating mutation (exon 19 deletion, L858R).", "candidate_expression": "((L858R) AND (NSCLC) AND (Pathologic) AND (at least one) AND (can be accurately measured in at least one dimension) AND (confirmation) AND (exon 19 deletion) AND (lesion) AND (locally advanced) AND (lung adenocarcinoma) AND (lung cancer) AND (metastatic) AND (untreated) AND (with EGFR activating mutation) AND (with measurable disease))"}
{"candidate_id": "LLM00995", "doc_id": "NCT02884401_inc", "case_bucket": "or", "source_criterion": "Participants must present a diagnosis of osteoporosis based on DXA measurement of the bone mineral density at the femur neck and/or total hip and/or lumbar spine (T value 2.5 SD or more below the young female adult mean) within the past 24 months. Not in treatment with anti-resorptive agents (like bisphosphonates and denosumab) for more than 4 consecutive years, in order to reduce the risk of medication-related osteonecrosis of the jaws (Lo et al., 2010). = 50 years old. In self-reported menopause, defined as the permanent cessation of ovulation, for at least one year (Soules et al., 2001). Edentulous area involving a maximum of two teeth (wisdom teeth and second molars are excluded) and presenting at least one neighbouring tooth (e.g. gap in the area of a second premolar and first molar, with first premolar in place). Residual alveolar width = 4 mm (Milinkovic and Cordaro, 2014), residual alveolar height >8 mm, enough inter-arch space for a crown (at least 5 mm) and a minimum distance of 7 mm from the adjacent teeth (Shah and Lum, 2008). The width and height will be confirmed after x-ray examination in Visit 2. Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth). Willingness to replace the missing tooth/teeth with dental implants Registration with a GDP", "candidate_expression": "((DXA) AND (Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth)) AND (Residual alveolar width = 4 mm) AND (T value 2.5 SD or more below the young female adult mean lumbar spine) AND (Willingness to replace the missing tooth/teeth with dental implants) AND (bisphosphonates) AND (bone mineral density femur neck total hip) AND (cessation of ovulation permanent) AND (denosumab) AND (menopause at least one year) AND (old = 50 years) AND (osteoporosis past 24 months) AND (residual alveolar height >8 mm) AND NOT (anti-resorptive agents more than 4 consecutive years,))"}
{"candidate_id": "LLM00996", "doc_id": "NCT02944929_exc", "case_bucket": "other", "source_criterion": "Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate. Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator. Un-controlled progressive pathology. Osteoarticular lesion which contraindicates part of the rehabilitation involved in the study. Patients with other interventions planned prior to the end of the study period (orthosis, surgery etc.). Surgery to the treated limb less than 6 months previously. Pregnant woman.", "candidate_expression": "((Osteoarticular lesion) AND (Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate) AND (Pregnant woman) AND (Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator) AND (Surgery treated limb less than 6 months))"}
{"candidate_id": "LLM00997", "doc_id": "NCT02490839_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((PPIs) AND (antibiotics) AND (any kind) AND (bismuth salts) AND (bleeding) AND (concomitant) AND (during the course of the ulcer) AND (gastric surgery) AND (history) AND (hypersensitivity) AND (illness) AND (in the previous month) AND (malignant tumor) AND (nursing) AND (pregnant) AND (previous) AND (serious) AND (test drugs) AND (the ulcer) AND (ulcer) AND (woman))"}
{"candidate_id": "LLM00998", "doc_id": "NCT02609048_exc", "case_bucket": "or", "source_criterion": "1. A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment) 2. AST or ALT > 3 × ULN 3. Total bilirubin > 2 × ULN 4. Auto-immune hepatitis 5. Primary sclerosing cholangitis 6. Known history of alpha-1-Antitrypsin deficiency 7. Known history of chronic viral hepatitis 8. Creatine kinase above ULN 9. Serum creatinine above ULN 10. For females, pregnancy or breast-feeding 11. Use of colchicine, methotrexate, azathioprine, or systemic steroids in the two months preceding screening 12. Current use of fibrates, including fenofibrates, or simvastatin 13. Use of an experimental treatment for PBC 14. Use of experimental or unapproved immunosuppressant 15. Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator", "candidate_expression": "((A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment)) AND (Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator) AND (Auto-immune hepatitis) AND (Creatine kinase above ULN) AND (Primary sclerosing cholangitis) AND (Serum creatinine above ULN) AND (Total bilirubin > 2 × ULN) AND (alpha-1-Antitrypsin deficiency history) AND (experimental treatment for PBC) AND (females) AND (immunosuppressant) AND (in the investigator's opinion) AND (medical condition) AND (viral hepatitis history chronic) AND ((PBC) OR (other than)) AND ((ALT > 3 × ULN) OR (AST > 3 × ULN)) AND ((breast-feeding) OR (pregnancy)) AND ((azathioprine) OR (colchicine) OR (methotrexate) OR (systemic steroids)) AND ((fenofibrates) OR (fibrates) OR (simvastatin)) AND ((experimental) OR (unapproved)))"}
{"candidate_id": "LLM00999", "doc_id": "NCT01866800_exc", "case_bucket": "or", "source_criterion": "History of acute coronary syndrome in the past 30 days. History of congesting heart failure with left ventricular ejection fraction <30% or exacerbation in the past 30 days. Current dialysis treatment. Known furosemide hypersensitivity. Contraindications to placement of a Foley catheter in the bladder.", "candidate_expression": "((Contraindications) AND (acute coronary syndrome in the past 30 days) AND (congesting heart failure) AND (dialysis treatment Current) AND (exacerbation in the past 30 days) AND (furosemide) AND (hypersensitivity) AND (left ventricular ejection fraction <30%) AND (placement of a Foley catheter bladder))"}
{"candidate_id": "LLM01000", "doc_id": "NCT02952378_inc", "case_bucket": "scope", "source_criterion": "For healthy individuals: Healthy, without allergies and with the age of 18 years or above. For patients: Burn injury exceeding 6-8 Total Burned Surface Area %", "candidate_expression": "((18 years or above) AND (Burn injury) AND (Healthy) AND (Total Burned Surface Area) AND (age) AND (allergies) AND (exceeding 6-8 %) AND (healthy) AND (patients) AND (without))"}
```
