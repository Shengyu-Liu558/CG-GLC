$ErrorActionPreference = "Stop"

python src/criteria_boolean/prepare_llm_eval_dataset.py --full-dataset
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
python src/criteria_boolean/generate_human_eval_sample.py --methods cgglc --sample-size 50 --skip-existing
python src/criteria_boolean/generate_human_eval_sample.py --methods flat or_direct constraint --reference-csv results/human_eval/cgglc_human_eval_1.csv --skip-existing
