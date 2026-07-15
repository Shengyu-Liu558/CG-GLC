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
{"candidate_id": "LLM05476", "doc_id": "NCT03156855_inc", "case_bucket": "or", "source_criterion": "children and teenagers aged less than 20 years, history of gastrectomy, gastric malignancy, including adenocarcinoma and lymphoma, previous allergic reaction to antibiotics (bismuth, amoxicillin, metronidazole, clarithromycin, tetracycline) and PPI (esomeprazole), contraindication to treatment drugs, pregnant or lactating women, severe concurrent disease, concomitant use of clopidogrel, or (9) Unwilling to accept random assignment of subjects", "candidate_expression": "((PPI) AND (Unwilling to accept random assignment of subjects) AND (adenocarcinoma) AND (aged) AND (allergic reaction) AND (amoxicillin) AND (antibiotics) AND (bismuth) AND (children) AND (clarithromycin) AND (clopidogrel) AND (concomitant) AND (concurrent) AND (contraindication) AND (disease) AND (esomeprazole) AND (gastrectomy) AND (gastric malignancy) AND (history) AND (lactating) AND (less than 20 years) AND (lymphoma) AND (metronidazole) AND (pregnant) AND (previous) AND (severe) AND (teenagers) AND (tetracycline) AND (treatment drugs) AND (women))"}
{"candidate_id": "LLM05477", "doc_id": "NCT03226080_exc", "case_bucket": "or", "source_criterion": "Inability to consent/refusal Allergy to any of the study medications Multiple traumatic injuries Contraindication to neuraxial or general anesthesia Pregnancy", "candidate_expression": "((Allergy) AND (Contraindication) AND (Inability to consent) AND (Multiple traumatic injuries) AND (Pregnancy) AND (general anesthesia) AND (neuraxial anesthesia) AND (refusal) AND (study medications))"}
{"candidate_id": "LLM05478", "doc_id": "NCT02782702_inc", "case_bucket": "or", "source_criterion": "Confirmed diagnosis (clinical and histological features) of Hailey Hailey or Darier diseases. Moderate to very severe lesions located in large folds Patient aged 18 ans or more Patient with health coverage Patient who have signed the consent form Patient proficient into filling out the questionnaires.", "candidate_expression": "((Patient proficient into filling out the questionnaires.) AND (Patient who have signed the consent form) AND (aged 18 ans or more) AND (health coverage) AND (histological) AND (lesions very severe) AND (very severe) AND ((Darier disease) OR (Hailey Hailey disease)))"}
{"candidate_id": "LLM05479", "doc_id": "NCT03288428_inc", "case_bucket": "or", "source_criterion": "elective Laparoscopic myomectomy patients 24hr post-operative patient controlled analgesia analgesia no mild or severe liver or renal disfunction", "candidate_expression": "((24hr post-operative) AND (Laparoscopic) AND (elective) AND (liver disfunction) AND (mild) AND (myomectomy) AND (no) AND (patient controlled analgesia) AND (renal disfunction) AND (severe))"}
{"candidate_id": "LLM05480", "doc_id": "NCT02301039_inc", "case_bucket": "or", "source_criterion": "Age ≥ 18 years (Age ≥ 12 years for patients with bone sarcomas). Histologically confirmed diagnosis of unresectable, recurrent, and/or metastatic high grade soft-tissue or bone sarcoma of one of the following subtypes: soft tissue sarcomas (leiomyosarcoma, poorly differentiated/de-differentiated liposarcoma, high grade pleomorphic undifferentiated sarcoma/MFH and synovial sarcoma), and bone sarcomas (Ewing sarcoma, osteosarcoma, and chondrosarcoma [de-differentiated or mesenchymal]). ECOG Performance Status of 0 or 1. At least one site of measurable disease on CT/MRI scans as defined by RECIST 1.1. Baseline imaging must be performed within 30 days of dosing. At least one site of accessible disease for pre- and post-treatment core biopsies for at least 20 patients per arm on the expansion cohorts. Patients may have received 1-3 prior systemic therapies in the metastatic setting. Adequate organ function within 14 days of dosing Must be willing to provide and have available archival tissue for PD-L1 testing. Written, voluntary informed consent. Fertile men and women of childbearing potential must agree to use an effective method of birth control from providing signed consent and for 120 days after last study drug administration. Women of childbearing potential include pre-menopausal women and women within the first 2 years of the onset of menopause. Women of childbearing potential must have a negative pregnancy test ≤ 72 hours prior to Day 1 of study. Effective methods of birth control include: surgically sterile, barrier device (condom, diaphragm), contraceptive coil, intrauterine device (IUD), and abstinence. Life expectancy of >12 weeks. Patients with central nervous system disease are eligible for enrollment if they have received prior radiotherapy or surgery to sites of CNS metastatic disease and are without evidence of clinical progression for at least 4 weeks prior to screening, have no evidence of new or enlarging brain metastases, and are off steroids for at least 7 days before first dose of pembrolizumab.", "candidate_expression": "((Adequate organ function within 14 days of dosing) AND (Age ≥ 12 years) AND (CNS metastatic disease) AND (ECOG Performance Status 0 or 1) AND (Histologically confirmed) AND (Life expectancy >12 weeks) AND (Women) AND (Written, voluntary informed consent.) AND (birth control) AND (birth control from providing signed consent for 120 days after last study drug administration) AND (central nervous system disease) AND (childbearing potential) AND (imaging Baseline within 30 days of dosing) AND (leiomyosarcoma) AND (liposarcoma high grade pleomorphic undifferentiated) AND (measurable disease) AND (pembrolizumab) AND (pre-menopausal) AND (pregnancy test negative ≤ 72 hours prior to Day 1) AND (synovial sarcoma) AND (systemic therapies 1-3 prior metastatic setting) AND (women) AND (women within the first 2 years of the onset of menopause) AND NOT (clinical progression for at least 4 weeks prior to screening) AND NOT (brain metastases) AND NOT (steroids for at least 7 days before first dose of pembrolizumab) AND ((Age ≥ 18 years) OR (bone sarcomas)) AND ((radiotherapy) OR (surgery)) AND ((enlarging) OR (new)) AND ((bone sarcoma) OR (soft-tissue sarcoma)) AND ((de-differentiated) OR (poorly differentiated)) AND ((MFH) OR (sarcoma)) AND ((bone sarcomas) OR (soft tissue sarcomas)) AND ((Ewing sarcoma) OR (chondrosarcoma) OR (osteosarcoma)) AND ((de-differentiated) OR (mesenchymal)) AND ((CT scans) OR (MRI scans)) AND ((men) OR (women)) AND ((high grade) OR (metastatic) OR (recurrent) OR (unresectable)) AND ((condom) OR (diaphragm)) AND ((abstinence) OR (barrier device) OR (contraceptive coil) OR (intrauterine device (IUD)) OR (surgically sterile)))"}
{"candidate_id": "LLM05481", "doc_id": "NCT02627521_exc", "case_bucket": "or", "source_criterion": "Anticoagulation therapy Prior CABG. Active bleeding or at high risk of bleeding Severe liver or renal disease. Hypersensitivity to ticagrelor History of intracranial hemorrhage", "candidate_expression": "((Active) AND (Anticoagulation therapy) AND (CABG) AND (History) AND (Hypersensitivity) AND (Prior) AND (Severe) AND (at high risk) AND (intracranial hemorrhage) AND (ticagrelor) AND ((bleeding)) AND ((disease liver) OR (renal disease)))"}
{"candidate_id": "LLM05482", "doc_id": "NCT02152696_exc", "case_bucket": "or", "source_criterion": "Hemodynamically unstable in need of acute treatment Most recent hCG > 5000 mIU/mL Patient obtaining care in relation to a recently completed pregnancy (delivery, spontaneous or elective abortion) Diagnosis of gestational trophoblastic disease Subject unwilling or unable to comply with study procedures Known hypersensitivity to MTX Presence of clinical contraindications for treatment with MTX Prior medical or surgical management of this gestation Subject unwilling to accept a blood transfusion", "candidate_expression": "((Hemodynamically unstable) AND (MTX) AND (Subject unwilling to accept a blood transfusion) AND (gestation) AND (gestational trophoblastic disease) AND (hCG Most recent > 5000 mIU/mL) AND (hypersensitivity to MTX) AND ((medical management) OR (surgical management)))"}
{"candidate_id": "LLM05483", "doc_id": "NCT03506477_inc", "case_bucket": "or", "source_criterion": "Provide written, signed and dated informed consent prior to initiating any study-related activities. Male or female >18 years of age at the time of screening Fitzpatrick Skin phototype IV-VI, non-white race/ethnicity, including but not limited to - --African Americans, Asians, Pacific Islanders and Hispanics. Clinical diagnosis of chronic plaque-type psoriasis of the body Plaque psoriasis with =2% Body Surface Area (BSA) involvement (may include scalp involvement), PASI Score = 2, IGA mod 2011 score of 2 or greater (based on scale of 0-4) Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d Must be in general good health as judged by the Investigator, based on medical history and physical examination.", "candidate_expression": "((African Americans) AND (Asians) AND (Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d) AND (Fitzpatrick Skin phototype IV-VI) AND (Hispanics) AND (IGA mod 2011 score 2 or greater scale of 0-4) AND (Male) AND (PASI Score = 2) AND (Pacific Islanders) AND (Plaque psoriasis) AND (Provide written, signed and dated informed consent prior to initiating any study-related activities.) AND (age >18 years of age) AND (female) AND (involvement =2% Body Surface Area (BSA)) AND (non-white race/ethnicity) AND (psoriasis of the body chronic plaque-type))"}
{"candidate_id": "LLM05484", "doc_id": "NCT03297021_exc", "case_bucket": "or", "source_criterion": "Patients with allergies or contraindications to study medications", "candidate_expression": "((allergies) AND (contraindications) AND (study medications))"}
{"candidate_id": "LLM05485", "doc_id": "NCT01888965_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential, who are biologically able to conceive, not employing two forms of highly effective contraception or who are pregnant. Women who are breast-feeding Fertile males unwilling to use contraception Patients with brain metastases or any history of brain metastases Patients who have undergone major surgery (e.g., intra-thoracic, -abdominal, or -pelvic) </= 4 weeks prior to starting study treatment or who have not recovered from such therapy Patients with a history of pulmonary embolism, or untreated deep vein thrombosis within the past 6 months Impairment of gastrointestinal (GI) function or GI disease that may significantly alter the absorption of dovitinib The subject has had another active malignancy within the past 5 years except for cervical cancer in situ, in situ carcinoma of the bladder or non-melanoma carcinoma of the skin. Patients who have received the last administration of an anticancer therapy including chemotherapy, immunotherapy, hormonal therapy and monoclonal antibodies </= 2 weeks prior to starting the study drug, or who have not recovered from the side effects of such therapy Cirrhosis, chronic active hepatitis or chronic persistent hepatitis Patients who are currently receiving prasugrel No concurrent use of isoniazid, labetolol, trovafloxacin, tolcapone, and felbamate No concurrent use of other investigational drugs or antineoplastic therapies. Patients with impaired cardiac function or clinically significant cardiac diseases.", "candidate_expression": "((</= 2 weeks prior to starting the study drug) AND (</= 4 weeks prior to starting study treatment) AND (Cirrhosis) AND (Fertile) AND (Fertile males unwilling to use contraception) AND (GI disease) AND (Impairment of gastrointestinal (GI) function) AND (No) AND (Women) AND (active malignancy) AND (anticancer therapy) AND (antineoplastic therapies) AND (biologically able to conceive) AND (brain metastases) AND (breast-feeding) AND (cardiac diseases) AND (cervical cancer in situ) AND (chemotherapy) AND (child-bearing potential) AND (chronic active hepatitis) AND (chronic persistent hepatitis) AND (clinically significant) AND (deep vein thrombosis) AND (except) AND (felbamate) AND (highly effective contraception) AND (history) AND (hormonal therapy) AND (immunotherapy) AND (impaired cardiac function) AND (in situ carcinoma of the bladder) AND (intra -abdominal) AND (intra -pelvic) AND (intra-thoracic) AND (isoniazid) AND (labetolol) AND (major surgery) AND (males) AND (may significantly alter the absorption of dovitinib) AND (monoclonal antibodies) AND (non-melanoma carcinoma of the skin) AND (not) AND (other investigational drugs) AND (prasugrel) AND (pregnant) AND (pulmonary embolism) AND (recovered from such therapy) AND (recovered from the side effects of such therapy) AND (starting study treatment) AND (starting the study drug) AND (tolcapone) AND (trovafloxacin) AND (two) AND (untreated) AND (unwilling to use contraception) AND (within the past 5 years) AND (within the past 6 months))"}
{"candidate_id": "LLM05486", "doc_id": "NCT03511521_inc", "case_bucket": "or", "source_criterion": "Patients receiving once daily dosing of methylprednisolone or prednisone in a dose of 10 mg/day or greater Hyperglycemic (Glucose level > 126 mg/dL) Diabetic and nondiabetic patients Expected duration of hospital stay and time on steroids >= 3 days Patient of appropriate caregiver able to give Informed Consent", "candidate_expression": "((10 mg/day or greater) AND (> 126 mg/dL) AND (>= 3 days) AND (Diabetic) AND (Expected duration of hospital stay) AND (Glucose level) AND (Hyperglycemic) AND (Patient of appropriate caregiver able to give Informed Consent) AND (methylprednisolone) AND (nondiabetic) AND (once daily) AND (prednisone) AND (time on steroids))"}
{"candidate_id": "LLM05487", "doc_id": "NCT02443623_inc", "case_bucket": "other", "source_criterion": "Signed written informed consent. Age 18 to 65. Normal and healthy (immune competent) as determined by medical history, physical exam, vital signs and clinical laboratory tests during the screening period. If all lab results for quantitative IgA immunoglobulin level are lower than 15% below normal range, the subject may not proceed further in the screening process. Subject must meet all required subject suitability criteria that pertain to normal source plasma donors. Negative HIV serology during screening period. Subject must have been previously immunized for smallpox, at =3 years prior to commencement of screening assessments, and vaccination history must be confirmed by oral or written history and the presence of a visible pathognomonic smallpox vaccination scar. Female subjects of childbearing potential must agree to use highly effective birth control methods.", "candidate_expression": "((18 to 65) AND (3 years prior to commencement of screening assessments) AND (Age) AND (Female) AND (HIV serology) AND (Negative) AND (Normal) AND (Signed written informed consent) AND (birth control methods) AND (childbearing potential) AND (clinical laboratory tests) AND (commencement of screening assessments) AND (during screening period) AND (during the screening period) AND (healthy) AND (immunized) AND (lower than 15% below normal range) AND (medical history) AND (physical exam) AND (quantitative IgA immunoglobulin level) AND (screening period) AND (smallpox) AND (vital signs))"}
{"candidate_id": "LLM05488", "doc_id": "NCT01809041_exc", "case_bucket": "or", "source_criterion": "Patients are not expected to be alive for longer than 3 months. Mini-mental State Examination (MMSE) [18] score = 23. history of dementia, psychiatric illness or any diseases of central nervous system. current use of sedatives or antidepressant. alcoholism and drug dependence. patients previously included in this study (for patients who have second intra-abdominal surgery during the study period). difficult to follow up or patients with poor compliance. uncontrolled hypertension (> 180/100 mmHg)", "candidate_expression": "((= 23) AND (> 180/100 mmHg) AND (Mini-mental State Examination (MMSE)) AND (current) AND (dementia) AND (diseases of central nervous system) AND (expected to be alive) AND (longer than 3 months) AND (not) AND (psychiatric illness) AND (uncontrolled hypertension) AND ((antidepressant) OR (sedatives)) AND ((alcoholism) OR (drug dependence)))"}
{"candidate_id": "LLM05489", "doc_id": "NCT02620904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05490", "doc_id": "NCT03253796_inc", "case_bucket": "or", "source_criterion": "Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication Has chronic back pain of =3 months duration by history Has physician-diagnosed active nr-axSpA with disease duration <= 5 years • Inflammatory back pain • Arthritis (physician-diagnosed) • Enthesitis (heel) physician-diagnosed (spontaneous pain or tenderness at examination of the site of the insertion of the Achilles tendon or plantar fascia) • Dactylitis (physician-diagnosed) • Psoriasis (physician-diagnosed) • History of physician-diagnosed inflammatory bowel disease (IBD) • History of uveitis confirmed by an ophthalmologist • Good response to nonsteroidal anti-inflammatory drugs (NSAID) • Family history of SpA (presence of ankylosing spondylitis, psoriasis, acute uveitis, reactive arthritis, or IBD) • Elevated CRP • Human leukocyte antigen B27 (HLA-B27)+ gene Has a HLA-B27+ gene and 2 or more of the SpA characteristics listed above Has elevated CRP at Screening or evidence of active inflammation in the sacroiliac joints on MRI Has an ASDAS >= 2.1 at Screening Shows high disease activity at Screening and Baseline of both a Total Back Pain score of =4 and a Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score of >= 4 Has an acceptable history of NSAID use Has no history of untreated latent or active tuberculosis (TB) prior to Screening Has had no recent close contact with a person with active TB or, if there has been such contact, will undergo additional evaluations and receive appropriate treatment for latent TB", "candidate_expression": "(((HLA-B27)+) AND (2 or more) AND (<= 5 years) AND (=3 months) AND (=3 months duration) AND (=4) AND (>= 2.1) AND (>= 4) AND (ASDAS) AND (Arthritis) AND (Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score) AND (CRP) AND (Dactylitis) AND (Elevated) AND (Enthesitis) AND (Family history) AND (Good response) AND (HLA-B27+) AND (History) AND (Inflammatory back pain) AND (Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication) AND (MRI) AND (NSAID) AND (Psoriasis) AND (Screening) AND (SpA) AND (Total Back Pain score) AND (acceptable) AND (active) AND (at Screening) AND (at Screening and Baseline) AND (chronic back pain) AND (close contact) AND (disease duration) AND (disease duration <= 5 years) AND (duration) AND (elevated) AND (gene Human leukocyte antigen B27) AND (heel) AND (high disease activity) AND (history) AND (inflammatory bowel disease (IBD)) AND (no) AND (nonsteroidal anti-inflammatory drugs (NSAID)) AND (nr-axSpA) AND (person with active TB) AND (prior to Screening) AND (recent) AND (sacroiliac joints) AND (tuberculosis (TB)) AND (untreated) AND (uveitis) AND ((pain) OR (tenderness)) AND ((plantar fascia) OR (site of the insertion of the Achilles tendon)) AND ((IBD) OR (acute uveitis) OR (ankylosing spondylitis) OR (psoriasis) OR (reactive arthritis)) AND ((CRP) OR (inflammation)) AND ((active) OR (latent)))"}
{"candidate_id": "LLM05491", "doc_id": "NCT02425774_exc", "case_bucket": "or", "source_criterion": "adjuvant radiotherapy evident intra-abdominal inflammation (diagnosed by imaging and/or laboratory results, including an abscess or cholecystitis) chronic pancreatitis pancreatic polypeptide producing endocrine tumor American Society of Anesthesiologists physical-health status classification (ASA-PS)>3 Poorly regulated diabetes (>200 mg/dl (=11 mmol/l))", "candidate_expression": "((>200 mg/dl (=11 mmol/l)) AND (>3) AND (American Society of Anesthesiologists physical-health status classification (ASA-PS)) AND (Poorly regulated) AND (abscess) AND (adjuvant radiotherapy) AND (cholecystitis) AND (chronic) AND (chronic pancreatitis) AND (diabetes) AND (imaging) AND (intra-abdominal inflammation) AND (laboratory) AND (pancreatic polypeptide producing endocrine tumor) AND (pancreatitis))"}
{"candidate_id": "LLM05492", "doc_id": "NCT00061308_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential that do not practice adequate contraception. Pregnant or lactating. Received more than one primary chemotherapy regimen. Concomitant or previous malignancies with the exception of adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, incidental carcinoid, or other cancer from which the patient has been disease free for 5 years. Active uncontrolled infection requiring antibiotics. Concurrent severe medical problems unrelated to the malignancy which would limit full compliance with the study. Received radiation to more than 10% of bone. Prior treatment with topotecan or gemcitabine. Hypersensitivity to camptothecin or nucleoside analogues. Use of an investigational agent within 30 days.", "candidate_expression": "((Active uncontrolled) AND (Concomitant) AND (Concurrent) AND (Hypersensitivity) AND (Pregnant) AND (Prior) AND (Women) AND (adequate contraception) AND (adequately treated) AND (antibiotics) AND (basal cell skin cancer) AND (bone) AND (camptothecin) AND (child-bearing potential) AND (do not) AND (for 5 years) AND (gemcitabine) AND (has been disease free) AND (in situ cervical cancer) AND (incidental carcinoid) AND (infection) AND (investigational agent) AND (lactating) AND (limit full compliance with the study) AND (malignancies) AND (malignancy) AND (medical problems) AND (more than 10%) AND (more than one) AND (nucleoside analogues) AND (other cancer) AND (previous) AND (primary chemotherapy regimen) AND (radiation) AND (severe) AND (squamous cell skin cancer) AND (the exception of) AND (topotecan) AND (treatment) AND (unrelated to the malignancy) AND (within 30 days))"}
{"candidate_id": "LLM05493", "doc_id": "NCT02205502_exc", "case_bucket": "or", "source_criterion": "contraindication to ketamine and lidocaine patients involved to other studies more or equal to American Society of Anesthesiologist (ASA) class III not alert", "candidate_expression": "((American Society of Anesthesiologist (ASA) class III more or equal to) AND (contraindication) AND (not alert) AND (patients involved to other studies) AND ((ketamine) OR (lidocaine)))"}
{"candidate_id": "LLM05494", "doc_id": "NCT02375295_inc", "case_bucket": "or", "source_criterion": "Male or Female. No age restriction. Diagnosed with an infection related stone. Medically fit for definitive surgical management of stone. Life expectancy greater than one year. Stone free after definitive surgical therapy defined as fragments less than 3mm.", "candidate_expression": "((Life expectancy) AND (Medically fit for) AND (Stone) AND (after definitive surgical therapy) AND (definitive surgical management) AND (definitive surgical therapy) AND (fragments less than 3mm) AND (free) AND (greater than one year) AND (infection related) AND (stone) AND ((Female) OR (Male)))"}
{"candidate_id": "LLM05495", "doc_id": "NCT03096613_exc", "case_bucket": "or", "source_criterion": "Acute heart failure or acute exacerbation of chronic heart failure within the past 2 weeks. Scheduled cardiac resynchronization therapy or heart transplantation. History of malignant tumor or life expectancy under 12 months. Already on medications that may affect thyroid function (L-T4, carbimazole, propylthiouracil, amiodarone, lithium). Pregnancy and lactation period. Participation in another clinical trial within the past 30 days. Contraindication or intolerance to evidence-based therapy for CHF, such as beta-blocker, angiotensin-converting enzyme inhibitor or angiotensin receptor blocker. Known hypersensitivity to the trial treatment(s) or diluents (when applicable), including placebo or other comparator drug(s). Untreated adrenal insufficiency. Untreated pituitary insufficiency. Untreated thyrotoxicosis. Treatment with levothyroxine must not be initiated in patients with acute myocardial infarction, acute myocarditis, or acute pancarditis. Severe renal dysfunction (eGFR=30 ml/min/1.73m2). Significant hepatic impairment (Serum GPT > 120 U/L). Any disorder which, in the opinion of the investigator, might jeopardise subject's safety or compliance with the protocol.", "candidate_expression": "((=30 ml/min/1.73m2) AND (> 120 U/L) AND (Acute heart failure) AND (Any disorder which, in the opinion of the investigator, might jeopardise subject's safety or compliance with the protocol.) AND (CHF) AND (Contraindication) AND (L-T4) AND (Pregnancy) AND (Serum GPT) AND (Severe) AND (Significant) AND (Treatment) AND (Untreated) AND (acute) AND (acute myocardial infarction) AND (acute myocarditis) AND (acute pancarditis) AND (adrenal insufficiency) AND (affect) AND (amiodarone) AND (angiotensin receptor blocker) AND (angiotensin-converting enzyme inhibitor) AND (beta-blocker) AND (carbimazole) AND (cardiac resynchronization therapy) AND (chronic heart failure) AND (comparator drug(s)) AND (eGFR) AND (evidence-based therapy) AND (exacerbation) AND (heart transplantation) AND (hepatic impairment) AND (hypersensitivity) AND (intolerance) AND (lactation period) AND (levothyroxine) AND (life expectancy) AND (lithium) AND (malignant tumor) AND (medications) AND (not be initiated) AND (other) AND (pituitary insufficiency) AND (placebo) AND (propylthiouracil) AND (renal dysfunction) AND (thyroid function) AND (thyrotoxicosis) AND (trial diluents) AND (trial treatment(s)) AND (under 12 months) AND (within the past 2 weeks))"}
{"candidate_id": "LLM05496", "doc_id": "NCT03100513_inc", "case_bucket": "other", "source_criterion": "Adult Patients with Overt Hepatic Encephalopathy.", "candidate_expression": "((Adult) AND (Overt Hepatic Encephalopathy))"}
{"candidate_id": "LLM05497", "doc_id": "NCT02748330_inc", "case_bucket": "or", "source_criterion": "Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures. Aged 18 years or older, male or female. History of stable angina pectoris with angiographic evidence of CAD (diameter stenosis = 50%) in major, i.e., left main, left anterior descending, left circumflex, and right coronary arteries. History of previous myocardial infarction (MI) History of coronary revascularization, i.e., percutaneous coronary intervention (PCI) or coronary artery bypass graft (CABG), not including the elective PCI during the index hospitalization Documented history of type 2 diabetes mellitus. Post-procedural residual diameter stenosis of the treated lesions < 20% in patients with stent implantation or < 50% in those with balloon angioplasty Post-procedural thrombolysis in myocardial infarction (TIMI) grade 3 flow in treated vessels Negative cardiac troponin test before the index elective PCI. Taking Clopidogrel 75 mg daily dose for at least 7 days or taking Clopidogrel 75 mg daily dose for less than 7 days but with 300 to 600 mg Clopidogrel loading dose before PCI. Taking acetylsalicylic acid (ASA) 100 mg daily treatment for at least 7 days or taking ASA 100 mg daily dose for less than 7 days but with 300 mg ASA loading dose before PCI. have a negative urine or blood pregnancy test at enrolment and prior to randomization; currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion.", "candidate_expression": "((ASA) AND (ASA 100 mg daily for less than 7 days) AND (ASA 300 mg before PCI) AND (Aged 18 years or older) AND (CABG) AND (CAD angiographic evidence diameter stenosis major coronary arteries left main coronary arteries left anterior descending coronary arteries left circumflex coronary arteries) AND (Clopidogrel 300 to 600 mg before PCI) AND (Clopidogrel 75 mg daily for at least 7 days) AND (Clopidogrel 75 mg daily for less than 7 days) AND (MI) AND (PCI) AND (Post-procedural thrombolysis treated vessels) AND (Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures) AND (TIMI) AND (acetylsalicylic acid 100 mg daily for at least 7 days) AND (balloon angioplasty) AND (cardiac troponin test Negative before the index elective PCI.) AND (coronary artery bypass graft) AND (coronary revascularization during the index hospitalization) AND (currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion) AND (female) AND (have a negative urine or blood pregnancy test at enrolment and prior to randomization;) AND (lesions Post-procedural residual diameter stenosis treated) AND (male) AND (myocardial infarction) AND (myocardial infarction grade 3) AND (myocardial infarction right coronary arteries) AND (percutaneous coronary intervention) AND (stable angina pectoris) AND (stent implantation) AND (type 2 diabetes mellitus) AND NOT (PCI elective))"}
{"candidate_id": "LLM05498", "doc_id": "NCT03631355_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a high tibial osteotomy (HTO) Patients undergoing tibial tubercle osteotomy (TTO) with or without medial patello-femoral ligament (MPFL) reconstruction", "candidate_expression": "((high tibial osteotomy (HTO)) AND (medial patello-femoral ligament (MPFL) reconstruction) AND (tibial tubercle osteotomy (TTO)) AND (undergoing))"}
{"candidate_id": "LLM05499", "doc_id": "NCT00279552_inc", "case_bucket": "other", "source_criterion": "Patients suspected to have vitamin B12 deficiency defined as a plasma vitamin B12 below the reference interval (<200 pmol/L).", "candidate_expression": "((<200 pmol/L) AND (below the reference interval) AND (plasma vitamin B12) AND (suspected) AND (vitamin B12 deficiency))"}
{"candidate_id": "LLM05500", "doc_id": "NCT02692651_inc", "case_bucket": "other", "source_criterion": "Patients 18 years of age or older with >3 unformed stools/24 hours with positive stool test for C. difficile. Patients receiving = 1 high or medium risk antibiotic for treatment of an infection other than CDI, for an anticipated duration of = 5 days from the time of enrollment.", "candidate_expression": "((24 hours) AND (>3) AND (C. difficile) AND (age) AND (or older 18 years) AND (positive) AND (stool test) AND (unformed stools))"}
```
