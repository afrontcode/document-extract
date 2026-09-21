import json
import os
import time
from pathlib import Path
from document_extract.core.baseline import extract_text_with_pdfplumber, baseline_extract
from document_extract.core.anthropic_parse import extract_with_anthropic

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PDF_DIR = DATA_DIR / "raw_pdfs"
GT_DIR = DATA_DIR / "ground_truth"

FIELDS_TO_EVALUATE = [
    "cliente_nombre",
    "cliente_ruc",
    "fecha_emision",
    "moneda",
    "monto_total",
]

def normalize_val(val):
    """Normaliza cadenas y números para comparaciones justas."""
    if val is None:
        return ""
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val).strip().upper()

def run_evaluation():
    pdf_files = sorted([f for f in PDF_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"])
    if not pdf_files:
        print(f"No se encontraron PDFs en {PDF_DIR}")
        return

    results = {
        "baseline": {field: 0 for field in FIELDS_TO_EVALUATE},
        "anthropic": {field: 0 for field in FIELDS_TO_EVALUATE}
    }
    
    total_docs = 0
    total_tokens = {"input": 0, "output": 0}
    latencies = {"baseline": [], "anthropic": []}

    for pdf_path in pdf_files:
        gt_path = GT_DIR / f"{pdf_path.stem}.json"
        if not gt_path.exists():
            print(f"[Saltando] Sin ground truth: {gt_path.name}")
            continue

        total_docs += 1
        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        raw_text = extract_text_with_pdfplumber(pdf_bytes)

        # 1. Evaluar Baseline
        t0 = time.perf_counter()
        base_out = baseline_extract(raw_text)
        latencies["baseline"].append(time.perf_counter() - t0)

        # 2. Evaluar Anthropic
        t1 = time.perf_counter()
        llm_res = extract_with_anthropic(raw_text)
        latencies["anthropic"].append(time.perf_counter() - t1)
        
        llm_out = llm_res["data"]
        total_tokens["input"] += llm_res["usage"]["input_tokens"]
        total_tokens["output"] += llm_res["usage"]["output_tokens"]

        # Comparar aciertos campo por campo
        # Comparar aciertos campo por campo (Lógica corregida para JSON anidado)
        for field in FIELDS_TO_EVALUATE:
            gt_datos = ground_truth.get("datos", ground_truth)
            gt_key = "ruc_cliente" if field == "cliente_ruc" else field
            gt_val = normalize_val(gt_datos.get(gt_key))
            
            # Imprimir para depuración si lo necesitas (opcional)
            # print(f"[{field}] Esperado: '{gt_val}' | Base: '{base_val}' | LLM: '{llm_val}'")
            
            base_val = normalize_val(base_out.get(field) or base_out.get("ruc_cliente" if field == "cliente_ruc" else None))
            if gt_val and base_val == gt_val:
                results["baseline"][field] += 1

            llm_val = normalize_val(llm_out.get(field))
            if gt_val and llm_val == gt_val:
                results["anthropic"][field] += 1

    if total_docs == 0:
        print("No hay pares coincidentes de PDF y Ground Truth.")
        return

    # Imprimir reporte
    print("\n" + "=" * 60)
    print(f"REPORTE DE EVALUACIÓN ({total_docs} documentos evaluados)")
    print("=" * 60)
    print(f"{'Campo':<25} | {'Regex Baseline':<15} | {'Anthropic (LLM)':<15}")
    print("-" * 60)

    for field in FIELDS_TO_EVALUATE:
        acc_base = (results["baseline"][field] / total_docs) * 100
        acc_llm = (results["anthropic"][field] / total_docs) * 100
        print(f"{field:<25} | {acc_base:>6.1f}%          | {acc_llm:>6.1f}%")

    avg_lat_base = (sum(latencies["baseline"]) / total_docs) * 1000
    avg_lat_llm = sum(latencies["anthropic"]) / total_docs

    print("-" * 60)
    print(f"Latencia promedio: Regex = {avg_lat_base:.2f} ms | LLM = {avg_lat_llm:.2f} s")
    print(f"Tokens totales consumidos: {total_tokens['input']} input / {total_tokens['output']} output")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()