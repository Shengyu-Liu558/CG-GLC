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
{"candidate_id": "LLM01651", "doc_id": "NCT03168178_inc", "case_bucket": "other", "source_criterion": "Pregnant women between 34-42 weeks gestation Singleton fetus Admitted for labor management & develops a fever of 100.4 F or greater", "candidate_expression": "((Pregnant) AND (Singleton fetus) AND (fever 100.4 F or greater) AND (gestation between 34-42 weeks) AND (labor management Admitted for) AND (women))"}
{"candidate_id": "LLM01652", "doc_id": "NCT02689024_inc", "case_bucket": "other", "source_criterion": "adult patients aged = 55 years with a radiographically confirmed hip fracture", "candidate_expression": "((adult) AND (aged = 55 years) AND (hip fracture) AND (radiographically))"}
{"candidate_id": "LLM01653", "doc_id": "NCT03080493_exc", "case_bucket": "or", "source_criterion": "Current use of gabapentin or pregabalin Allergy to gabapentin, acetaminophen, codeine, or ibuprofen Self reported renal disease (severe impaired renal function) Self reported current or chronic narcotic use (typical daily use) Women with any issue that, in the opinion of the investigator, would interfere with study participation or generating accurate study data", "candidate_expression": "((Allergy) AND (impaired renal function severe) AND (narcotic use Self reported daily use) AND (renal disease Self reported) AND ((gabapentin) OR (pregabalin)) AND ((chronic) OR (current)) AND ((acetaminophen) OR (codeine) OR (gabapentin) OR (ibuprofen)))"}
{"candidate_id": "LLM01654", "doc_id": "NCT02797548_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome within 1 month Heart failure NYHA III to IV Contraindication to Aspirin On anticoagulant therapy Emergent surgery Cardiac surgery High bleeding risk surgeries, e.g., Intra-cranial surgery, Intra-spinal surgery, Retinal surgery Pregnancy or breast-feeding Life expectancy less than 1year", "candidate_expression": "((Acute coronary syndrome within 1 month) AND (Aspirin) AND (Cardiac surgery) AND (Contraindication) AND (Emergent surgery) AND (Heart failure) AND (High bleeding risk surgeries) AND (Life expectancy less than 1year) AND (NYHA III to IV) AND (anticoagulant therapy) AND ((Intra-cranial surgery) OR (Intra-spinal surgery) OR (Retinal surgery)) AND ((Pregnancy) OR (breast-feeding)))"}
{"candidate_id": "LLM01655", "doc_id": "NCT00862446_exc", "case_bucket": "other", "source_criterion": "Enrollment in another trial Lack of consent", "candidate_expression": "((Enrollment in another trial) AND (Lack of consent))"}
{"candidate_id": "LLM01656", "doc_id": "NCT02106598_exc", "case_bucket": "or", "source_criterion": "Known pregnancy or breast-feeding. Medical illness unrelated to the tumor which in the opinion of the attending physician and principal investigator will preclude administration of the agent. This includes patients with uncontrolled infection, chronic renal insufficiency, myocardial infarction within the past 6 months, unstable angina, cardiac arrhythmias other than chronic atrial fibrillation and chronic active or persistent hepatitis, or New York Heart Association Classification III or IV heart disease.", "candidate_expression": "((Medical illness unrelated to the tumor) AND (New York Heart Association Classification III or IV) AND (breast-feeding) AND (cardiac arrhythmias) AND (chronic active hepatitis) AND (chronic renal insufficiency) AND (heart disease) AND (myocardial infarction within the past 6 months) AND (persistent hepatitis) AND (pregnancy) AND (uncontrolled infection) AND (unstable angina) AND (which in the opinion of the attending physician and principal investigator will preclude administration of the agent) AND NOT (chronic atrial fibrillation))"}
{"candidate_id": "LLM01657", "doc_id": "NCT02926989_exc", "case_bucket": "other", "source_criterion": "An initial plasma sodium concentration of lower than 130 mmol/L An initial plasma sodium concentration of higher than 150 mmol/L An initial plasma potassium concentration of lower than 3.0 mmol/L Need for 10% glucose solution Diabetes Diabetes insipidus Diabetic ketoacidosis Renal disease that needs dialysis Protocol-determined chemotherapy hydration Severe liver disease Inborn errors of metabolism that need protocol-determined fluid therapy", "candidate_expression": "((10% glucose solution) AND (Diabetes) AND (Diabetes insipidus) AND (Diabetic ketoacidosis) AND (Inborn errors of metabolism) AND (Need for) AND (Protocol-determined) AND (Renal disease) AND (Severe) AND (chemotherapy hydration) AND (dialysis) AND (fluid therapy) AND (higher than 150 mmol/L) AND (initial) AND (liver disease) AND (lower than 130 mmol/L) AND (lower than 3.0 mmol/L) AND (need) AND (needs) AND (plasma potassium concentration) AND (plasma sodium concentration) AND (protocol-determined))"}
{"candidate_id": "LLM01658", "doc_id": "NCT03056287_exc", "case_bucket": "or", "source_criterion": "1. Unable to ambulate at least 150 feet prior to stroke, or experienced intermittent claudication while walking; 2. history of congestive heart failure, unstable cardiac arrhythmias, hypertrophic cardiomyopathy, severe aortic stenosis, angina or dyspnea at rest or during ADL's; 3. History of oxygen dependence; 4. Preexisting neurological disorders, dementia or previous stroke; 5. History of major head trauma; 6. Legal blindness or severe visual impairment; 7. history of psychosis or other Axis I disorder that is primary; 8. Life expectancy <1 yr.; 9. Severe arthritis or other problems that limit passive range of motion; 10. History of DVT or pulmonary embolism within 6 months; 11. Uncontrolled diabetes with recent weight loss, diabetic coma, or frequent insulin reactions; 12. Severe hypertension with systolic >200 mmHg and diastolic >110 mmHg at rest; 13. attempt of suicide in the last 2 years or at suicidal risk assessed by SCID interview; 14. Previous or current enrollment in a clinical trial to enhance motor recovery; 15) currently exercising ≥ 2 times per week (≥20 minutes); 16) Presence of non-MR compatible implants, pregnancy or severe claustrophobia.", "candidate_expression": "((<1 yr) AND (>110 mmHg) AND (>200 mmHg) AND (History) AND (Life expectancy) AND (Preexisting) AND (SCID interview) AND (Severe hypertension) AND (Uncontrolled) AND (diastolic) AND (frequent) AND (history) AND (in the last 2 years) AND (major head trauma) AND (oxygen dependence) AND (previous) AND (primary) AND (prior) AND (severe) AND (stroke) AND (systolic) AND (while walking) AND (within 6 months) AND ((Unable to ambulate at least 150 feet) OR (intermittent claudication)) AND ((angina) OR (congestive heart failure) OR (dyspnea at rest) OR (dyspnea during ADL's) OR (hypertrophic cardiomyopathy) OR (severe aortic stenosis) OR (unstable cardiac arrhythmias)) AND ((dementia) OR (neurological disorders) OR (stroke)) AND ((Legal blindness) OR (severe visual impairment)) AND ((Axis I disorder) OR (psychosis)) AND ((Severe arthritis) OR (problems that limit passive range of motion)) AND ((DVT) OR (pulmonary embolism)) AND ((diabetes) OR (diabetic coma) OR (insulin reactions) OR (weight loss)) AND ((at suicidal risk) OR (attempt of suicide)) AND ((claustrophobia) OR (non-MR compatible implants) OR (pregnancy)))"}
{"candidate_id": "LLM01659", "doc_id": "NCT02015494_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered drug or vaccine product within 30 days preceding the administration of the study vaccine or planned use within the first six weeks of the study period Has received any licensed or other investigational influenza vaccine within 3 months prior to enrollment in this study or expected receipt of any influenza vaccination before the Day 21 blood collection History of excessive alcohol use, drug abuse or significant psychiatric illness Tobacco use within 3 months of enrollment and throughout first 6 months of the study Has a chronic illness (e.g., liver or kidney disease), receiving a concomitant therapy or have any other condition that could interfere with the subject's participation in the study or in the interpretation of the study results Clinically significant abnormal liver function tests at screening Positive serology for HBsAg, HCV or HIV antibodies Pregnant or lactating female Having cancer or have received treatment for cancer within three years (persons with a history of cancer who are disease-free without treatment for three years or more are eligible), excluding minor skin cancers, which are allowed unless located at the vaccination site Persons with impaired immune responsiveness (of any cause), including diabetes mellitus and autoimmune disorders Persons presently receiving or having a recent history of receiving (within the past six months) any medication or therapeutic modality that affects the immune system such as allergy shots, immune globulin, interferon, immunomodulators, radiation therapy, cytotoxic drugs or drugs known to be frequently associated with significant major organ toxicity, or systemic corticosteroids (oral or injectable). Inhaled and topical corticosteroids are allowed. Persons with a history of severe allergic reaction after previous vaccinations or hypersensitivity to any seasonal influenza vaccine component Persons with a history of Guillain-Barré Syndrome Receipt of blood or blood products 8 weeks prior to vaccination or planned administration during the three week study period following vaccination Donation of blood or blood products within 8 weeks prior to vaccination or during the three week study period following An oral temperature >100.4° or acute disease within 72 hours prior to vaccination, defined as the presence of a moderate or severe illness (as determined by the investigator through medical history and physical examination; for example, those requiring an absence from work) with or without fever. Body Mass Index >29.9 Any disorder of coagulation A clinical diagnosis of influenza within the previous 12 months Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study", "candidate_expression": "((Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study) AND (Body Mass Index >29.9) AND (Clinically significant) AND (Donation of blood) AND (Donation of blood products within 8 weeks prior to vaccination during the three week study period) AND (Guillain-Barré Syndrome) AND (HBsAg antibodies) AND (HCV antibodies) AND (HIV antibodies) AND (Pregnant) AND (Receipt of blood) AND (Receipt of blood products 8 weeks prior to vaccination) AND (Tobacco use within 3 months of enrollment throughout first 6 months of the study) AND (acute disease) AND (allergic reaction history severe after previous vaccinations) AND (allergy shots) AND (any influenza vaccination expected receipt before the Day 21) AND (any medication) AND (any other condition could interfere with the subject's participation in the study) AND (autoimmune disorders) AND (cancer) AND (cancer history) AND (chronic illness) AND (cytotoxic drugs) AND (diabetes mellitus) AND (disease-free) AND (disorder of coagulation) AND (drug abuse) AND (drug investigational non-registered) AND (drugs known to be frequently associated with significant major organ toxicity known to be frequently associated with significant major organ toxicity) AND (excessive alcohol use) AND (female) AND (hypersensitivity to any seasonal influenza vaccine component) AND (immune globulin) AND (immunomodulators) AND (impaired immune responsiveness) AND (influenza vaccine within 3 months prior to enrollment in this study licensed other investigational) AND (influenza within the previous 12 months) AND (interferon) AND (kidney disease) AND (lactating) AND (liver disease) AND (liver function tests Clinically significant abnormal at screening) AND (moderate illness) AND (oral temperature >100.4°) AND (planned administration during the three week study period following vaccination) AND (psychiatric illness significant) AND (radiation therapy) AND (seasonal influenza vaccine component) AND (severe illness) AND (systemic corticosteroids oral injectable) AND (therapeutic modality) AND (therapy concomitant) AND (treatment for cancer) AND (vaccine product within 30 days preceding the administration of the study vaccine) AND (within the first six weeks of the study period planned use the study period) AND NOT (treatment for three years or more))"}
{"candidate_id": "LLM01660", "doc_id": "NCT03471117_exc", "case_bucket": "or", "source_criterion": "Allergy to Glitazones Myocardial infarction Heart failure Angina History of kidney stones Liver disease (abnormal liver enzymes) Anemia (hemoglobin <8 g/dl) Cancer with current treatment Previous organ transplantation Immunosuppressant therapy Human immunodeficiency virus infection Pregnancy or lactating Current tobacco use Dilantin and oral contraceptive usage due to potential drug interaction with glitazones Self-identified history of hypoglycemia", "candidate_expression": "((<8 g/dl) AND (Allergy) AND (Anemia) AND (Angina) AND (Cancer) AND (Current) AND (Glitazones) AND (Heart failure) AND (History) AND (Human immunodeficiency virus infection) AND (Immunosuppressant therapy) AND (Liver disease) AND (Myocardial infarction) AND (Previous) AND (Self-identified) AND (abnormal) AND (current) AND (drug interaction) AND (glitazones) AND (hemoglobin) AND (history) AND (hypoglycemia) AND (kidney stones) AND (liver enzymes) AND (organ transplantation) AND (potential) AND (tobacco use) AND (treatment) AND ((Pregnancy) OR (lactating)) AND ((Dilantin) OR (oral contraceptive)))"}
{"candidate_id": "LLM01661", "doc_id": "NCT02340169_exc", "case_bucket": "or", "source_criterion": "Has other dermatological conditions that may interfere with clinical assessments Allergy or sensitivity to corticosteroids or any drug hypersensitivity or intolerance that would compromise patient safety or study results History of an adverse reaction to Cortrosyn™ or similar test reagents Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation", "candidate_expression": "((Allergy) AND (Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation) AND (Cortrosyn) AND (Has other dermatological conditions that may interfere with clinical assessments) AND (adverse reaction) AND (corticosteroids) AND (drug hypersensitivity) AND (drug intolerance) AND (hat would compromise patient safety or study results) AND (sensitivity) AND (similar) AND (similar test reagents) AND (test reagents))"}
{"candidate_id": "LLM01662", "doc_id": "NCT00404495_inc", "case_bucket": "other", "source_criterion": "Cohort 1: Recurrent or refractory medulloblastoma in which current standard treatment approaches have failed; biopsy is not required for recurrent disease. Cohort 2: Newly-diagnosed high-grade glioma (World Health Organization [WHO] grade 3 or 4) Life expectancy ≥ 3 months", "candidate_expression": "((3 or 4) AND (Life expectancy) AND (Recurrent medulloblastoma) AND (World Health Organization [WHO] grade) AND (failed) AND (high-grade glioma) AND (not required) AND (refractory medulloblastoma) AND (standard treatment) AND (≥ 3 months))"}
{"candidate_id": "LLM01663", "doc_id": "NCT03344887_exc", "case_bucket": "other", "source_criterion": "Patients that do not have a valid Ontario Health Insurance Plan (OHIP) number at time of first transfusion Patients that require emergent release of a RBC transfusion and in whom emergency randomization could not be completed Patients with complex antibody profile in which it is impossible to match RBC units", "candidate_expression": "((RBC transfusion require emergent release) AND (complex antibody profile) AND (impossible to match RBC units) AND (transfusion first) AND NOT (have a valid Ontario Health Insurance Plan (OHIP) number at time of first transfusion) AND NOT (emergency randomization))"}
{"candidate_id": "LLM01664", "doc_id": "NCT03253796_exc", "case_bucket": "or", "source_criterion": "Has bilateral sacroiliitis Grade 2 or unilateral sacroiliitis Grade 3 or Grade 4 Is a nursing or pregnant female, or intends to become pregnant within 6 months after receiving trial medication Intends to donate eggs (female participants) or sperm (male participants) while receiving trial medication or within 6 months after trial medication Has any clinically significant condition or situation that would interfere with the trial evaluations or participation in the trial Has ever received any cytotoxic drugs, including chlorambucil, cyclophosphamide, nitrogen mustard, or other alkylating agents • Disease-modifying anti-rheumatic drugs (30 days off drug) • Live vaccinations (3 months off drug) • Investigational medications (30 days or 5 half-lives off drug, whichever is longer) • Bacille Calmette-Guerin (BCG) vaccination (12 months off drug) Has any systemic inflammatory condition, including psoriatic arthritis, active Lyme disease, systemic lupus erythematosus, infectious arthritis, vasculitis, parvovirus infection, rheumatoid arthritis, active uveitis, or active IBD Has a history of latent or active granulomatous infection prior to Screening Had a nontuberculous mycobacterial infection or opportunistic infection within 6 months prior to Screening Has a history of an infected joint prosthesis, or has received antibiotics for a suspected infection of a joint prosthesis, if that prosthesis has not been removed or replaced Had a serious infection, has been hospitalized for an infection, or has been treated with IV antibiotics for an infection within 2 months prior to Baseline Had a history of, or ongoing, chronic or recurrent infectious disease Is known to be infected with human immunodeficiency virus (HIV) or seropositive for hepatitis C virus (HCV) Has had a chest x-ray within 2 months prior to Screening that shows an abnormality suggestive of a current active infection or malignancy Has a history of lymphoproliferative disease Has had a malignancy within 5 years before screening (exceptions are squamous and basal cell carcinomas of the skin and carcinoma in situ of cervix that has been surgically cured) Has a history of known demyelinating diseases such as multiple sclerosis or optic neuritis Has a history of or concurrent congestive heart failure of any grade Has a transplanted organ (with the exception of a corneal transplant performed >= 3 months prior to baseline) Has current signs or symptoms of significant medical illness which could interfere with the trial, or require treatment that might interfere with the trial Is a user of recreational or illicit drugs or has or had a substance abuse (drug or alcohol) problem within the previous 2 years", "candidate_expression": "((Bacille Calmette-Guerin (BCG) vaccination 12 months off drug) AND (Disease-modifying anti-rheumatic drugs 30 days off drug) AND (Has any clinically significant condition or situation that would interfere with the trial evaluations or participation in the trial) AND (Investigational medications) AND (Is a user of recreational or illicit drugs or has or had a substance abuse (drug or alcohol) problem within the previous 2 years) AND (Live vaccinations 3 months off drug) AND (abnormality) AND (antibiotics) AND (chest x-ray within 2 months prior to Screening) AND (congestive heart failure) AND (cytotoxic drugs) AND (demyelinating diseases history) AND (donate eggs) AND (donate sperm) AND (female) AND (granulomatous infection prior to Screening) AND (infection) AND (infectious disease) AND (inflammatory condition) AND (joint prosthesis) AND (lymphoproliferative disease) AND (malignancy within 5 years before screening) AND (medical illness significant) AND (pregnant intends to become within 6 months after receiving trial medication) AND (surgically) AND (transplanted organ) AND NOT (corneal transplant >= 3 months prior to baseline) AND ((basal cell carcinomas of the skin) OR (carcinoma in situ cervix surgically cured) OR (squamous carcinomas of the skin)) AND ((multiple sclerosis) OR (optic neuritis)) AND ((concurrent) OR (history)) AND ((interfere with the trial) OR (treatment require interfere with the trial)) AND ((female) OR (male)) AND ((while receiving trial medication trial medication) OR (within 6 months after trial medication trial medication)) AND ((sacroiliitis bilateral Grade 2) OR (sacroiliitis unilateral)) AND ((alkylating agents) OR (chlorambucil) OR (cyclophosphamide) OR (nitrogen mustard)) AND ((30 days off drug) OR (5 half-lives off drug)) AND ((Lyme disease active) OR (active IBD) OR (active uveitis) OR (infectious arthritis) OR (parvovirus infection) OR (psoriatic arthritis) OR (rheumatoid arthritis) OR (systemic lupus erythematosus) OR (vasculitis)) AND ((active) OR (latent)) AND ((Grade 3) OR (Grade 4)) AND ((nontuberculous mycobacterial infection) OR (opportunistic infection)) AND ((infected history) OR (infection suspected)) AND ((IV antibiotics within 2 months prior to Baseline) OR (hospitalized) OR (serious infection)) AND ((chronic) OR (recurrent)) AND ((history) OR (ongoing)) AND ((human immunodeficiency virus (HIV)) OR (seropositive for hepatitis C virus (HCV))) AND ((nursing) OR (pregnant)) AND ((infection) OR (malignancy)))"}
{"candidate_id": "LLM01665", "doc_id": "NCT01175044_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo revision total knee arthroplasty", "candidate_expression": "(revision total knee arthroplasty)"}
{"candidate_id": "LLM01666", "doc_id": "NCT02798237_exc", "case_bucket": "or", "source_criterion": "cognitive impairment (Mini-Mental Status Examination score: illiterate 13 points; elementary and middle school 18 points; and high-school 26 points; or inability to respond to verbal command); inability to walk independently for at least 10 minutes, with or without walking devices; pain or other disorders precluding their participation.", "candidate_expression": "((13 points) AND (18 points) AND (26 points) AND (Mini-Mental Status Examination score) AND (at least 10 minutes) AND (cognitive impairment) AND (inability to walk independently) AND (pain or other disorders precluding their participation) AND (precluding their participation) AND (walking devices) AND ((other disorders) OR (pain)) AND ((elementary) OR (middle school)) AND ((high-school) OR (illiterate) OR (inability to respond to verbal command)))"}
{"candidate_id": "LLM01667", "doc_id": "NCT02056288_inc", "case_bucket": "other", "source_criterion": "Supracondylar fracture Age 2-17 years American Society of Anesthesiologists Status 1 -3 Scheduled for closed reduction with percutaneous pinning under general anesthesia", "candidate_expression": "((1 -3) AND (2-17 years) AND (Age) AND (American Society of Anesthesiologists Status) AND (Scheduled for) AND (Supracondylar fracture) AND (closed reduction with percutaneous pinning) AND (general anesthesia))"}
{"candidate_id": "LLM01668", "doc_id": "NCT03164304_inc", "case_bucket": "other", "source_criterion": "Pregnant women admitted to Women health hospital with a diagnosis of severe pre-eclampsia", "candidate_expression": "((Pregnant) AND (Women health hospital) AND (admitted to) AND (pre-eclampsia severe) AND (women))"}
{"candidate_id": "LLM01669", "doc_id": "NCT02707874_inc", "case_bucket": "other", "source_criterion": "Inpatients having major foot and ankle surgery that will benefit from continuous popliteal sciatic nerve block with an indwelling catheter American Society Anesthesiologists (ASA) physical status I-III 18-85 years of age, inclusive 40-120 kg, inclusive 150 cm of height or greater", "candidate_expression": "((150 cm or greater) AND (18-85 years) AND (40-120) AND (ASA) AND (American Society Anesthesiologists physical status) AND (I-III) AND (Inpatients) AND (age) AND (continuous) AND (height) AND (indwelling catheter) AND (kg) AND (major foot and ankle surgery) AND (popliteal sciatic nerve block))"}
{"candidate_id": "LLM01670", "doc_id": "NCT03491059_exc", "case_bucket": "or", "source_criterion": "not a regular user of e-cigarettes pregnant or lactating (only excluded from imaging study) prisoner incapable of giving informed consent unable to lie flat on the scanner for extended periods of time unstable medical condition like heart disease, uncontrolled hypertension, thyroid disease, diabetes, renal or liver impairment, or glaucoma prostatic hypertrophy, stroke, or ulcer in past year psychiatric conditions such as schizophrenia, adult ADHD, or bipolar disorder current or regular use of psychiatric medications such as tranquilizers, antipsychotics, and/or antidepressants use of medications that are inducers of CYP2A6 (a nicotine metabolizing enzyme) such as rifampicin, dexamethasone, phenobarbital, and other anti-convulsant drugs unable to communicate in English current use of smokeless tobacco, tobacco cigarettes (5 and fewer a day) occasional use of pipes is permitted if subject abstains for the week prior to the study older than 80 years", "candidate_expression": "((adult ADHD) AND (anti-convulsant drugs) AND (antidepressants) AND (antipsychotics) AND (bipolar disorder) AND (dexamethasone) AND (diabetes) AND (e-cigarettes) AND (glaucoma) AND (heart disease) AND (hypertension uncontrolled) AND (incapable of giving informed consent) AND (liver impairment) AND (medical condition unstable) AND (medications inducers of CYP2A6) AND (nicotine metabolizing enzyme) AND (phenobarbital) AND (pregnant or lactating (only excluded from imaging study)) AND (prisoner) AND (prostatic hypertrophy) AND (psychiatric conditions) AND (psychiatric medications) AND (renal impairment) AND (rifampicin) AND (schizophrenia) AND (smokeless tobacco) AND (stroke) AND (thyroid disease) AND (tobacco cigarettes) AND (tranquilizers) AND (ulcer) AND (unable to lie flat on the scanner for extended periods of time) AND (years older than 80) AND NOT (regular user))"}
{"candidate_id": "LLM01671", "doc_id": "NCT02504203_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01672", "doc_id": "NCT02656394_inc", "case_bucket": "or", "source_criterion": "1. Male or female of any race, at least 18 years of age at Visit 1 Screening. 2. Has provided verbal and written informed consent. 3. Be able and willing to follow instructions, including participation in all study assessments and visits. 4. Currently being treated for glaucoma using at least two medications, and be willing to continue on the same regime. 5. Suffers from at least two of the symptoms in the GLIA™ Glaucoma Medication Ocular Side Effect Symptoms Questionnaire at a severity of 2 (moderate) or more. 6. If a woman of childbearing potential, have a negative urine pregnancy test at Visit 1 and be using an adequate method of birth control throughout the study period.", "candidate_expression": "((Be able and willing to follow instructions, including participation in all study assessments and visits.) AND (Currently) AND (GLIA™ Glaucoma Medication Ocular Side Effect Symptoms Questionnaire) AND (Has provided verbal and written informed consent.) AND (Male) AND (Visit 1) AND (Visit 1 Screening) AND (adequate) AND (age) AND (at Visit 1) AND (at Visit 1 Screening) AND (at least 18 years) AND (at least two) AND (childbearing potential) AND (female) AND (glaucoma) AND (medications) AND (method of birth control) AND (moderate) AND (negative) AND (severity of 2 or more) AND (study period) AND (symptoms) AND (throughout the study period) AND (treated) AND (urine pregnancy test) AND (woman))"}
{"candidate_id": "LLM01673", "doc_id": "NCT02964416_exc", "case_bucket": "or", "source_criterion": "Patients with a history of allergy or hypersensitivity to tramadol. History of epilepsy or convulsions due to any reason. Chronic usage of analgesic drugs. Patients using monoamine oxidase inhibitors. Patients with clinical signs of raised ICP. Obesity (women with a body mass index >35 kg/m2 or men with a body mass index >42 kg/m2) Language barrier. Patients taking B-blockers or Ca channel blockers. Patients above 65 years of age ( Physiology difference)", "candidate_expression": "((>35 kg/m2) AND (>42 kg/m2) AND (B-blockers) AND (Ca channel blockers) AND (ICP) AND (Language barrier) AND (Obesity) AND (above 65 years) AND (age) AND (allergy) AND (analgesic drugs) AND (body mass index) AND (convulsions) AND (epilepsy) AND (hypersensitivity) AND (men) AND (monoamine oxidase inhibitors) AND (raised) AND (tramadol) AND (women))"}
{"candidate_id": "LLM01674", "doc_id": "NCT03047538_exc", "case_bucket": "or", "source_criterion": "hypersensitivity to perindopril or to other ACE inhibitors, amlodipine, atorvastatin, dihydropyridines or to or statins angioneurotic edema in medical history (hereditary / idiopathic or associated with prior treatment with ACE inhibitors) severe hypotension, shock, including cardiogenic shock hemodynamically unstable heart failure Active liver disease or unexplained persistent elevations of serum transaminases more than three times normal Women of childbearing age without reliable contraception pregnancy breastfeeding Patients with contraindications listed in the currently valid SP", "candidate_expression": "((ACE inhibitors) AND (Women) AND (angioneurotic edema) AND (breastfeeding) AND (childbearing age) AND (contraindications) AND (elevations) AND (heart failure) AND (hemodynamically unstable) AND (hypersensitivity) AND (listed in the currently valid SP) AND (more than three times normal) AND (other) AND (persistent) AND (pregnancy) AND (prior) AND (severe) AND (treatment) AND (unexplained) AND (without) AND ((associated) OR (hereditary) OR (idiopathic)) AND ((cardiogenic shock) OR (hypotension) OR (shock)) AND ((liver disease) OR (serum transaminases)) AND ((ACE inhibitors) OR (amlodipine) OR (atorvastatin) OR (dihydropyridines) OR (perindopril) OR (statins)) AND ((contraception) OR (reliable)))"}
{"candidate_id": "LLM01675", "doc_id": "NCT02393287_exc", "case_bucket": "other", "source_criterion": "1. Presence of other neoplasia 2. Man", "candidate_expression": "((Man) AND (neoplasia) AND (other))"}
```
