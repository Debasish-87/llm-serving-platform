#!/usr/bin/env python3
"""
Quantize the serving model to 4-bit AWQ.

Produces the model referenced by benchmarks/configs/vllm-awq.env
(Qwen/Qwen2.5-0.5B-Instruct-AWQ) from the FP16 baseline model.

Usage:
    pip install autoawq transformers accelerate
    python benchmarks/scripts/quantize_model.py \
        --model Qwen/Qwen2.5-0.5B-Instruct \
        --output ./models/Qwen2.5-0.5B-Instruct-AWQ

Notes:
    - Calibration uses a small slice of a public instruction-tuning dataset
      by default. Swap CALIBRATION_DATASET for a domain-relevant sample if
      quantizing a model for a specific real workload — calibration data
      shapes which weights survive quantization with the least quality loss.
    - This does not evaluate output quality after quantization. Pair this
      script with a small held-out prompt set and compare outputs manually
      (or via a metric such as perplexity) before trusting the AWQ variant
      for anything beyond this benchmark.
"""

import argparse

CALIBRATION_DATASET = "mit-han-lab/pile-val-backup"
CALIBRATION_SAMPLES = 128


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="HF model id or local path to quantize")
    parser.add_argument("--output", required=True, help="Directory to write the quantized model to")
    parser.add_argument("--bits", type=int, default=4, choices=[4, 8])
    parser.add_argument("--group-size", type=int, default=128)
    args = parser.parse_args()

    # Imported lazily so `--help` works without the (heavy) dependency installed.
    from awq import AutoAWQForCausalLM
    from transformers import AutoTokenizer

    print(f"Loading {args.model} ...")
    model = AutoAWQForCausalLM.from_pretrained(args.model, safetensors=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)

    quant_config = {
        "zero_point": True,
        "q_group_size": args.group_size,
        "w_bit": args.bits,
        "version": "GEMM",
    }

    print(
        f"Quantizing to {args.bits}-bit AWQ using "
        f"{CALIBRATION_SAMPLES} samples from {CALIBRATION_DATASET} ..."
    )
    model.quantize(
        tokenizer,
        quant_config=quant_config,
        calib_data=CALIBRATION_DATASET,
        n_samples=CALIBRATION_SAMPLES,
    )

    model.save_quantized(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"Quantized model written to {args.output}")
    print(
        "Next: push this to your model registry / mount path, update "
        "MODEL in benchmarks/configs/vllm-awq.env, and deploy."
    )


if __name__ == "__main__":
    main()
