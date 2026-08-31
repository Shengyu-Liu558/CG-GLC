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
{"candidate_id": "LLM02076", "doc_id": "NCT01959061_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed colorectal adenocarcinoma Disease limited to the liver Unresectable disease by surgery or other local therapies Age >18 years ECOG performance status 0-2,Child pugh A or B Expected survival = 3 months Adequate hematological, hepatic, and renal function", "candidate_expression": "((Age >18 years) AND (Child pugh) AND (ECOG performance status 0-2) AND (Expected survival = 3 months) AND (Histologically) AND (colorectal adenocarcinoma Histologically confirmed) AND ((A) OR (B)) AND ((hematological function) OR (hepatic function) OR (renal function)) AND ((Disease limited to the liver) OR (Unresectable disease)) AND ((local therapies other) OR (surgery)))"}
{"candidate_id": "LLM02077", "doc_id": "NCT02951832_exc", "case_bucket": "or", "source_criterion": "Having experienced severe allergies, trauma history and/or operation history within 3 months; With a history of mental illness and/or family history of mental illness; Limb disabled; Taking medicine within one month; Suffering major events or having mood swings.", "candidate_expression": "((Limb disabled) AND (major events) AND (medicine within one month) AND ((major events) OR (mood swings)) AND ((operation within 3 months) OR (severe allergies within 3 months) OR (trauma within 3 months)) AND ((mental illness family history) OR (mental illness history)))"}
{"candidate_id": "LLM02078", "doc_id": "NCT02698969_exc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of hepatic or renal disease Clinical diagnosis of chronic or acute alcoholism History of allergy or hypersensitivity to Sugammadex and/or atropine or Neostigmine Current medications with CNS effects History of neurologic disease Diaphragmatic palsy Pregnancy or nursing History of malignant arrhythmias", "candidate_expression": "((CNS effects) AND (Diaphragmatic palsy) AND (alcoholism Clinical diagnosis) AND (malignant arrhythmias History) AND (medications) AND (neurologic disease History) AND ((Neostigmine) OR (Sugammadex) OR (atropine)) AND ((hepatic disease) OR (renal disease)) AND ((Pregnancy) OR (nursing)) AND ((acute) OR (chronic)) AND ((allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM02079", "doc_id": "NCT02562456_exc", "case_bucket": "or", "source_criterion": "severe behavioral issues presence of fistula or abscess near the selected tooth presence of pulp exposure in the selected tooth presence of mobility in the selected tooth", "candidate_expression": "((behavioral issues severe) AND (mobility selected tooth) AND (pulp exposure selected tooth) AND ((abscess) OR (fistula)))"}
{"candidate_id": "LLM02080", "doc_id": "NCT02744976_exc", "case_bucket": "or", "source_criterion": "cardiac or non-cardiac illness with life expectancy of less than two years; failure to advance the IVUS catheter through the culprit lesion; acute coronary syndrome congestive heart failure NYHA III-IV diabetes mellitus chronic kidney disease previous PCI in the target vessel heavily calcified vessels allergy to metformin", "candidate_expression": "((IVUS catheter) AND (NYHA III-IV) AND (PCI previous target vessel target vessel) AND (acute coronary syndrome) AND (advance the IVUS catheter failure culprit lesion) AND (allergy) AND (cardiac illness) AND (chronic kidney disease) AND (congestive heart failure) AND (diabetes mellitus) AND (heavily calcified vessels) AND (life expectancy less than two years) AND (metformin) AND (non-cardiac illness))"}
{"candidate_id": "LLM02081", "doc_id": "NCT02361892_exc", "case_bucket": "or", "source_criterion": "endometrial hyperplasia with atypia, estrogen-progestin therapy in the 2 months before enrollment, autoimmune diseases, chronic, metabolic, systemic and endocrine disorders, including hyperandrogenism, hyperprolactinemia, diabetes mellitus and thyroid disease, hypogonadotropic hypogonadism, majors clinical conditions", "candidate_expression": "((atypia) AND (autoimmune diseases) AND (chronic disorders) AND (diabetes mellitus) AND (endocrine disorders) AND (endometrial hyperplasia) AND (estrogen-progestin therapy) AND (hyperandrogenism) AND (hyperprolactinemia) AND (hypogonadotropic hypogonadism) AND (in the 2 months before enrollment) AND (majors clinical conditions) AND (metabolic disorders) AND (systemic disorders) AND (thyroid disease))"}
{"candidate_id": "LLM02082", "doc_id": "NCT02858804_inc", "case_bucket": "or", "source_criterion": "age=65 years diagnosis with mantle cell lymphoma Ann Arbor stage II,III or IV ECOG=1 or if ECOG=2 but recover after pretreatment.", "candidate_expression": "((=1) AND (=2) AND (=65 years) AND (Ann Arbor stage) AND (ECOG) AND (II) AND (III) AND (IV) AND (after pretreatment) AND (age) AND (mantle cell lymphoma) AND (pretreatment) AND (recover))"}
{"candidate_id": "LLM02083", "doc_id": "NCT03099408_inc", "case_bucket": "or", "source_criterion": "Women be at least 18 years of age Have symptoms of vaginal odor and or/discharge Meet the clinical (Amsel) criteria for BV Willing to participate in research", "candidate_expression": "((BV criteria clinical Amsel criteria) AND (Women) AND (age at least 18 years) AND (participate in research Willing to) AND ((vaginal discharge) OR (vaginal odor)))"}
{"candidate_id": "LLM02084", "doc_id": "NCT01701219_inc", "case_bucket": "or", "source_criterion": "1. Presence of bacteremia due solely to: S. aureus on at least 1 blood culture within 72 hours of beginning study drug (Cohort A) OR MRSA on a baseline blood culture and on at least 1 additional blood culture after at least 72 hours of vancomycin and/or daptomycin treatment (Cohort B). 2. Male or female ≥ 18 years of age. 3. If female of childbearing potential must be willing to practice sexual abstinence or dual methods of contraception during treatment and for at least 30 days after the last dose of study drug. 4. Expectation of survival for at least 2 months.", "candidate_expression": "((Expectation) AND (MRSA) AND (S. aureus) AND (after at least 72 hours of vancomycin and/or daptomycin treatment) AND (age) AND (at least 1) AND (at least 1 additional) AND (bacteremia) AND (baseline) AND (beginning study drug) AND (blood culture) AND (childbearing potential) AND (daptomycin) AND (dual) AND (during treatment) AND (female) AND (for at least 2 months) AND (for at least 30 days after the last dose of study drug) AND (survival) AND (the last dose of study drug) AND (vancomycin) AND (vancomycin and/or daptomycin treatment) AND (willing) AND (within 72 hours of beginning study drug) AND (≥ 18 years) AND ((daptomycin treatment) OR (vancomycin treatment)) AND ((Male) OR (female)) AND ((methods of contraception) OR (practice sexual abstinence)))"}
{"candidate_id": "LLM02085", "doc_id": "NCT02831166_exc", "case_bucket": "or", "source_criterion": "Less than 18 years of age; Pregnancy; Chronic use of vitamin K antagonists or direct thrombin inhibitors, or oral Xa-factor antagonists; Hypersensitivity to antiplatelet and/or anticoagulant drugs; Active bleeding or high bleeding risk (severe liver failure, active peptic ulcer, creatinine clearance < 30 mL/min, platelets count < 100.000 mm3); Uncontrolled systemic hypertension; Cardiogenic shock; Previous myocardial revascularization surgery with = 1 internal mammary or radial artery graft; Documented chronic peripheral arterial disease preventing the use of the femoral technique; Severe concomitant disease with life expectancy below 12 months; Participation in drug or devices investigative clinical trials in the last 30 days; Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.", "candidate_expression": "((Cardiogenic shock) AND (Hypersensitivity) AND (Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.) AND (Pregnancy) AND (age Less than 18 years) AND (anticoagulant drugs) AND (antiplatelet drugs) AND (bleeding Active) AND (creatinine clearance < 30 mL/min) AND (direct thrombin inhibitors) AND (disease Severe concomitant life expectancy) AND (high bleeding risk) AND (internal mammary graft) AND (liver failure severe) AND (myocardial revascularization surgery Previous) AND (oral Xa-factor antagonists) AND (peptic ulcer active) AND (peripheral arterial disease chronic) AND (platelets count < 100.000 mm3) AND (radial artery graft) AND (systemic hypertension Uncontrolled) AND (vitamin K antagonists) AND NOT (femoral technique))"}
{"candidate_id": "LLM02086", "doc_id": "NCT03338855_exc", "case_bucket": "or", "source_criterion": "Involvement in the planning and conduct of the study (applies to both AstraZeneca staff and staff at third party vendor or at the investigational sites). Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator. History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study. Clinical diagnosis of Type 1 diabetes, maturity onset diabetes of the young, secondary diabetes or diabetes insipidus. Unstable/rapidly progressing renal disease or estimated Glomerular Filtration Rate < 60 mL/min (Cockcroft-Gault formula). Clinically significant out of range values of serum levels of either alanine aminotransferase (ALT), aspartate aminotransferase (AST) or alkaline phosphatase (ALP) in the Investigator's opinion. Contraindications to dapagliflozin according to the local label. Use of antidiabetic drugs other than metformin within 3 months prior to screening. Weight gain or loss > 5 kg in the last 3 months, ongoing weight-loss diet (hypocaloric diet) or use of weight loss agents. History of drug abuse or alcohol abuse in the past 12 months. Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk. Plasma donation within one month of screening or any blood donation/blood loss > 500 mL within 3 months prior to screening or during the study. Anemia defined as Hemoglobin (Hb) < 115 g/L (7.1 mM) in women and < 120 g/L (7.5 mM) in men. Use of anti-coagulant treatment such as heparin, warfarin, platelet inhibitors, thrombin and factor X inhibitors. Use of medication such as oral glucocorticoids, anti-estrogens or other medications that are known to markedly influence insulin sensitivity. Use of loop diuretics. Regular smoking and other regular nicotine use. Central nervous system aneurysm clip Implanted neural stimulator Implanted cardiac pacemaker of defibrillator Cochlear implant Metal containing corpora aliena in the eye or brain. Patients, who do not want to be informed about unexpected medical findings, or do not wish that their physician be informed about coincidental findings, cannot participate in the study.", "candidate_expression": "((Anemia) AND (Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk.) AND (Central nervous system aneurysm clip) AND (Cochlear implant) AND (Contraindications) AND (Hemoglobin (Hb) 7.1 mM 7.5 mM) AND (History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study) AND (Implanted neural stimulator) AND (Plasma donation within one month of screening) AND (Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator.) AND (anti-coagulant treatment) AND (antidiabetic drugs within 3 months prior to screening) AND (cardiovascular event) AND (dapagliflozin) AND (disease clinically significant) AND (disorder recent < 3 months) AND (hypocaloric diet) AND (loop diuretics) AND NOT (metformin) AND ((Type 1 diabetes) OR (diabetes insipidus) OR (maturity onset diabetes of the young) OR (secondary diabetes)) AND ((Unstable) OR (rapidly progressing)) AND ((estimated Glomerular Filtration Rate < 60 mL/min Cockcroft-Gault formula) OR (renal disease)) AND ((alanine aminotransferase (ALT)) OR (alkaline phosphatase (ALP)) OR (aspartate aminotransferase (AST))) AND ((Weight gain) OR (Weight loss)) AND ((weight loss agents) OR (weight-loss diet ongoing)) AND ((alcohol abuse) OR (drug abuse)) AND ((blood donation) OR (blood loss > 500 mL)) AND ((during the study) OR (within 3 months prior to screening)) AND ((men < 120 g/L) OR (women < 115 g/L)) AND ((factor X inhibitors) OR (heparin) OR (platelet inhibitors) OR (thrombin) OR (warfarin)) AND ((anti-estrogens) OR (medications other) OR (oral glucocorticoids)) AND ((nicotine regular) OR (smoking Regular)) AND ((cardiac pacemaker) OR (defibrillator)) AND ((corpora aliena in the brain Metal containing) OR (corpora aliena in the eye Metal containing)))"}
{"candidate_id": "LLM02087", "doc_id": "NCT00455663_inc", "case_bucket": "or", "source_criterion": "Diagnosis of schizophrenia or schizoaffective disorder If entering the study as an inpatient, hospitalization was recent Currently receiving treatment with an atypical antipsychotic and continuation on the medication has been recommended Assumes primary responsibility for taking medication Currently living in a stable environment", "candidate_expression": "((atypical antipsychotic) AND (continuation on the medication recommended) AND (hospitalization recent) AND (inpatient) AND (living in a stable environment) AND (treatment Currently) AND ((schizoaffective disorder) OR (schizophrenia)))"}
{"candidate_id": "LLM02088", "doc_id": "NCT02415257_inc", "case_bucket": "other", "source_criterion": "Vestibular schwannoma advised to surgical treatment No measurable remaining vestibular function", "candidate_expression": "((No) AND (Vestibular schwannoma) AND (advised) AND (remaining vestibular function) AND (surgical treatment))"}
{"candidate_id": "LLM02089", "doc_id": "NCT03537924_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((Allergy) AND (active smoking during the last 10 years) AND (cigarettes per day >20) AND (pack-years >20) AND (tolerance relevant being) AND (treatment requiring) AND ((altitude exposure) OR (hypoxia)) AND ((heavy smoking) OR (regular use of alcohol)) AND ((acetazolamide) OR (sulfonamides other)) AND ((cardiovascular disease) OR (disease other) OR (respiratory disease)))"}
{"candidate_id": "LLM02090", "doc_id": "NCT02668016_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older Previously taken one or more statins Withdrawn from statins because of perceived side effects Developed side effects within 2 weeks of initiation Clinical indication for statins for primary or secondary prevention of cardiovascular disease or dyslipidaemia, on either no medication or non-statin lipid lowering therapy (e.g, ezetimibe)", "candidate_expression": "((18 years or older) AND (Aged) AND (indication) AND (initiation) AND (one or more) AND (side effects) AND (statins) AND (within 2 weeks of initiation) AND ((primary) OR (secondary)) AND ((dyslipidaemia) OR (prevention of cardiovascular disease)))"}
{"candidate_id": "LLM02091", "doc_id": "NCT01824537_exc", "case_bucket": "or", "source_criterion": "Volunteers must not have been vaccinated against HPV-Gardasil-9 (both partners) Any history of cervical, penile, oral or anal cancers Being pregnant or plan on immediately becoming pregnant", "candidate_expression": "((Any history) AND (HPV-Gardasil-9) AND NOT (vaccinated have been) AND ((pregnant) OR (pregnant plan on immediately becoming)) AND ((anal cancers) OR (cancers cervical) OR (oral cancers) OR (penile cancers)))"}
{"candidate_id": "LLM02092", "doc_id": "NCT02573909_inc", "case_bucket": "other", "source_criterion": "Planned gynecological lower abdomen surgery with epidural pain treatment Informed consent obtained", "candidate_expression": "((Planned) AND (epidural pain treatment) AND (gynecological lower abdomen surgery))"}
{"candidate_id": "LLM02093", "doc_id": "NCT03352869_inc", "case_bucket": "or", "source_criterion": "Overweight and obese PCOS patients with newly diagnosed IGR; PCOS diagnosis based on 2003 Rotterdam criteria Overweight / obesity diagnostic criteria according to WHO-WPR Impaired glucose regulation diagnostic criteria according to 1998 WHO diagnostic criteria.", "candidate_expression": "((1998 WHO diagnostic criteria) AND (2003 Rotterdam criteria) AND (IGR) AND (Impaired glucose regulation) AND (Overweight) AND (PCOS) AND (WHO-WPR) AND (newly diagnosed) AND (obese) AND (obesity))"}
{"candidate_id": "LLM02094", "doc_id": "NCT00391690_inc", "case_bucket": "or", "source_criterion": "Patients with histologically confirmed diagnosis of prostate cancer who have not yet developed bone metastases Prostate cancer patients with a rise in PSA under hormone therapy. PSA criteria: Patients who have undergone prostatectomy: any rise in PSA or Patients without prostatectomy: 2 consecutive rises in PSA levels relative to a previous reference value, separated by one month. The first measurement must occur one month after the reference value and must be above the reference value. The second confirmatory measurement taken one month after the first measurement must be greater than the first measurement. Previous chemotherapy or radiotherapy must have been performed ≥ 8 weeks prior to study entry. Eastern Cooperative Oncology Group (ECOG) score of 0, 1 or 2 (patients that spend less than 50% of time in bed during the day) Adequate liver function - serum total bilirubin concentration less than 1.5 x upper limit of normal value Age: ≥ 18 years Patient has given written informed consent prior to any study-specific procedures. Patients with psychiatric or addictive disorders which prevent them from giving their informed consent must not enter the study.", "candidate_expression": "((Age ≥ 18 years) AND (Eastern Cooperative Oncology Group (ECOG) score 0, 1 or 2) AND (PSA levels rises) AND (PSA rise) AND (Prostate cancer) AND (addictive disorders) AND (bone metastases) AND (chemotherapy) AND (histologically confirmed) AND (hormone therapy) AND (liver function Adequate) AND (measurement one month after the first measurement greater than the first measurement second) AND (measurement one month after the reference value above the reference value first) AND (prostate cancer) AND (prostatectomy) AND (prostatectomy 2) AND (psychiatric disorders) AND (radiotherapy) AND (serum total bilirubin concentration less than 1.5 x upper limit of normal value) AND (spend time in bed during the day less than 50%) AND (without))"}
{"candidate_id": "LLM02095", "doc_id": "NCT01424020_exc", "case_bucket": "or", "source_criterion": "Unable to participate for administrative reasons Psychiatric troubles Pain at rest or critical limb ischemia Unable to walk (ex: wheelchair subjects)", "candidate_expression": "((Psychiatric troubles) AND (Unable to participate) AND (Unable to walk) AND (administrative reasons) AND (wheelchair subjects) AND ((Pain at rest) OR (critical limb ischemia)))"}
{"candidate_id": "LLM02096", "doc_id": "NCT02656394_exc", "case_bucket": "or", "source_criterion": "1. Comorbidity with other severe or chronic eye conditions that in the judgment of the investigator will interfere with study assessments, such as corneal opacities and scars, dystrophies, epithelial scarring, infections, blood clots, etc. 2. Best corrected visual acuity (BCVA) at baseline <20/200. 3. Has a condition or history that, in the opinion of the investigator, may interfere significantly with the subject's participation in the study. 4. A woman who is pregnant, nursing an infant, or planning a pregnancy. 5. Has a known adverse reaction and/or sensitivity to the study drug or its components. 6. Routine use (more than twice a week) of a chlorinated swimming pool. 7. Unwilling or unable to cease using the following medications during the study period: Topical ocular cyclosporine (e.g. Restasis®), anti-histamines, antipsychotics, or eye gels. 8. Currently enrolled in an investigational drug or device study or have used an investigational drug or device within 30 days prior to Visit 1.", "candidate_expression": "((Best corrected visual acuity (BCVA) at baseline <20/200) AND (Restasis®) AND (Topical ocular cyclosporine) AND (Unwilling or unable) AND (adverse reaction to the study drug or its components more than twice a week) AND (anti-histamines) AND (antipsychotics) AND (blood clots) AND (chlorinated swimming pool Routine use) AND (corneal opacities) AND (corneal scars) AND (dystrophies) AND (epithelial scarring) AND (eye conditions will interfere with study assessments) AND (eye gels) AND (in the judgment of the investigator) AND (in the opinion of the investigator) AND (infections) AND (investigational device) AND (investigational drug) AND (may interfere significantly) AND (nursing) AND (pregnancy) AND (pregnant) AND (sensitivity to the study drug or its components) AND (woman))"}
{"candidate_id": "LLM02097", "doc_id": "NCT03539718_inc", "case_bucket": "or", "source_criterion": "Patients on regular hemodialysis 3sessions/wk. Recent catheter insertion at beginning of the study. Both males and females. Age group = 18 ys.", "candidate_expression": "((Age group = 18 ys) AND (catheter insertion Recent at beginning of the study) AND (regular hemodialysis 3sessions/wk) AND ((females) OR (males)))"}
{"candidate_id": "LLM02098", "doc_id": "NCT03513874_inc", "case_bucket": "or", "source_criterion": "Type 1 diabetes according to ADA criterias <5 years. Age= 18 years and less than 70 years. Non-obese: defined as BMI less than 28 kg/m2 Positive for at least one of the anti-islet autoantibodies: GADA, IA2A, ZnT8A Fasting or postprandial plasma C-peptide more than 100 pmol/L Written informed consent from the patient or family representative.", "candidate_expression": "((<5 years) AND (= 18 years and less than 70 years) AND (ADA criterias) AND (Age) AND (BMI) AND (Non) AND (Type 1 diabetes) AND (Written informed consent from the patient or family representative.) AND (anti-islet autoantibodies) AND (at least one) AND (less than 28 kg/m2) AND (more than 100 pmol/L) AND (obese) AND ((GADA) OR (IA2A) OR (ZnT8A)) AND ((Fasting plasma C-peptide) OR (postprandial plasma C-peptide)))"}
{"candidate_id": "LLM02099", "doc_id": "NCT03228654_inc", "case_bucket": "or", "source_criterion": "uterine size <12 weeks. presence of benign cause for the hysterectomy e.g. fibroid uterus, perimenopausal beeding not responding to medical treatment or complex endometrial hyperplasia without atypia. Absence of significant scarring in the pelvis from previous surgeries.", "candidate_expression": "((<12 weeks) AND (Absence) AND (atypia) AND (benign cause) AND (complex endometrial hyperplasia) AND (fibroid uterus) AND (from previous surgeries) AND (hysterectomy) AND (medical treatment) AND (not) AND (pelvis) AND (perimenopausal beeding) AND (previous) AND (responding to medical treatment) AND (significant scarring) AND (surgeries) AND (uterine size) AND (without))"}
{"candidate_id": "LLM02100", "doc_id": "NCT01963754_exc", "case_bucket": "or", "source_criterion": "If smoking and/or other drug addiction is present If local anesthetic allergy is present Patient subjected to chemical or radiotherapy if Hepatic disease is present If immunodepression is present If Pregnancy is present If Diabetes is present If Heart disease is present", "candidate_expression": "((Diabetes) AND (Heart disease) AND (Hepatic disease) AND (Pregnancy) AND (allergy) AND (immunodepression) AND (local anesthetic) AND ((drug addiction) OR (smoking)) AND ((chemical) OR (radiotherapy)))"}
```
