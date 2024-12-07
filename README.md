# Procedural Grade School Math

Generate grade school math word problems procedurally using python scripts.

## Motivation

1. A recent paper by Apple pointed out even though most LLMs score very high on the GSM8k benchmark, some LLMs score badly by simply changing the numbers or names in the problems. This indicates overtraining on the GSM8K dataset.
2. Most larger LLMs were not affected, and most small LLMs have adjusted and no longer have the same vulnerabilities. However, the training data used to improve performance are proprietary, there is not many open source GSM datasets.
3. A tremendous number of problems can be potentially procedurally generated. While repetitive to humans, the variation in names, numbers, items, fact ordering etc might be able to improve training data.
4. LLMs can be tested on unique procedurally generated problems, similar to ARC.
5. Variations in problems can be finely controlled. Eg, we can easily generate problems with double or 10x the complexity.

## Analysis of GSM problems
[Analysis](Analysis.md)
