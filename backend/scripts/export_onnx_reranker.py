"""Export cross-encoder model to ONNX format and quantize to INT8.

One-time script. Run on a machine with internet access:
    python scripts/export_onnx_reranker.py

Produces: models/reranker-int8/ directory with:
    - model.onnx (INT8 quantized)
    - tokenizer files
"""

import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Export cross-encoder to ONNX + INT8")
    parser.add_argument(
        "--model", default="cross-encoder/ms-marco-MiniLM-L-12-v2",
        help="HuggingFace model name",
    )
    parser.add_argument(
        "--output", default="models/reranker-int8",
        help="Output directory",
    )
    args = parser.parse_args()

    # Step 1: Export to ONNX using optimum
    print(f"[1/3] Exporting {args.model} to ONNX...")
    try:
        from optimum.onnxruntime import ORTModelForSequenceClassification
    except ImportError:
        print("ERROR: Install optimum first: pip install optimum[onnxruntime]")
        sys.exit(1)

    fp32_dir = args.output + "-fp32"
    model = ORTModelForSequenceClassification.from_pretrained(
        args.model, export=True
    )
    model.save_pretrained(fp32_dir)

    # Also save tokenizer
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.save_pretrained(fp32_dir)
    tokenizer.save_pretrained(args.output)
    print(f"   FP32 ONNX saved to {fp32_dir}/")

    # Step 2: Quantize to INT8
    print(f"[2/3] Quantizing to INT8...")
    from optimum.onnxruntime import ORTQuantizer
    from optimum.onnxruntime.configuration import AutoQuantizationConfig

    quantizer = ORTQuantizer.from_pretrained(fp32_dir)
    qconfig = AutoQuantizationConfig.avx2(is_static=False)
    quantizer.quantize(save_dir=args.output, quantization_config=qconfig)
    print(f"   INT8 ONNX saved to {args.output}/")

    # Step 3: Verify
    print("[3/3] Verifying...")
    import onnxruntime as ort
    onnx_path = os.path.join(args.output, "model_quantized.onnx")
    if not os.path.exists(onnx_path):
        # Try alternative name
        onnx_path = os.path.join(args.output, "model.onnx")
    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    input_names = [inp.name for inp in session.get_inputs()]
    output_names = [out.name for out in session.get_outputs()]
    print(f"   Inputs: {input_names}")
    print(f"   Outputs: {output_names}")

    # Dummy inference
    import numpy as np
    dummy = {
        "input_ids": np.array([[101, 2023, 2003, 1037, 3231, 102, 2023, 2003, 1037, 3231, 102]], dtype=np.int64),
        "attention_mask": np.array([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]], dtype=np.int64),
    }
    if "token_type_ids" in input_names:
        dummy["token_type_ids"] = np.array([[0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1]], dtype=np.int64)
    result = session.run(output_names, dummy)
    print(f"   Dummy output shape: {result[0].shape}, value: {result[0]}")

    # Report sizes
    fp32_size = os.path.getsize(os.path.join(fp32_dir, "model.onnx")) / 1024 / 1024
    int8_size = os.path.getsize(onnx_path) / 1024 / 1024
    print(f"\n   FP32 model: {fp32_size:.1f} MB")
    print(f"   INT8 model: {int8_size:.1f} MB")
    print(f"   Compression: {fp32_size/int8_size:.1f}x")
    print("\nDone! Deploy the models/ directory to VPS.")


if __name__ == "__main__":
    main()
