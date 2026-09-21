#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Minimal Google Coral PCIe/M.2 Edge TPU inference example for Fedora.

The model, labels and sample image can be obtained from google-coral/test_data:
  mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite
  inat_bird_labels.txt
  parrot.jpg

The explicit teardown at the end is intentional.  With current LiteRT/Python
combinations, relying on interpreter shutdown ordering may trigger a
segmentation fault after otherwise successful inference.
"""

from __future__ import annotations

import gc
import time
from pathlib import Path

import numpy as np
from PIL import Image
from ai_edge_litert.interpreter import Interpreter, load_delegate


MODEL = Path("mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite")
LABELS = Path("inat_bird_labels.txt")
IMAGE = Path("parrot.jpg")
LIBEDGETPU = "/usr/lib64/libedgetpu.so.1"


def load_labels(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    delegate = None
    interpreter = None

    try:
        delegate = load_delegate(
            LIBEDGETPU,
            {"device": "pci:0"},
        )

        interpreter = Interpreter(
            model_path=str(MODEL),
            experimental_delegates=[delegate],
        )
        interpreter.allocate_tensors()

        input_info = interpreter.get_input_details()[0]
        output_info = interpreter.get_output_details()[0]

        print("INPUT:")
        print(input_info)
        print()
        print("OUTPUT:")
        print(output_info)

        height = int(input_info["shape"][1])
        width = int(input_info["shape"][2])

        image = Image.open(IMAGE).convert("RGB").resize((width, height))
        input_data = np.expand_dims(np.asarray(image, dtype=np.uint8), axis=0)
        interpreter.set_tensor(input_info["index"], input_data)

        print()
        print("Inferências:")
        for run in range(1, 6):
            start = time.perf_counter()
            interpreter.invoke()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            print(f"{run}: {elapsed_ms:.3f} ms")

        output = interpreter.get_tensor(output_info["index"])[0]

        scale, zero_point = output_info["quantization"]
        if scale:
            scores = scale * (output.astype(np.float32) - zero_point)
        else:
            scores = output.astype(np.float32)

        labels = load_labels(LABELS)
        top = np.argsort(scores)[::-1][:5]

        print()
        print("Resultados:")
        for index in top:
            label = labels[index] if index < len(labels) else f"class {index}"
            print(f"{index:4d} {scores[index]:.5f} {label}")

        return 0

    finally:
        # Destroy the Interpreter before the delegate.  This avoids depending
        # on Python interpreter-shutdown ordering for native LiteRT objects.
        if interpreter is not None:
            del interpreter
            gc.collect()

        if delegate is not None:
            del delegate
            gc.collect()


if __name__ == "__main__":
    raise SystemExit(main())
