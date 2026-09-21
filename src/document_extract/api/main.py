import time
from fastapi import FastAPI, UploadFile, File, Query
from document_extract.core.baseline import extract_text_with_pdfplumber, baseline_extract
from document_extract.core.llm_parser import extract_with_llm
from document_extract.core.anthropic_parse import extract_with_anthropic

app = FastAPI(
    title="Extractor Inteligente de Documentos",
    description="API para extraer datos estructurados de PDFs"
)

@app.get("/")
def home():
    return {"mensaje": "API activa"}

@app.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    method: str = Query("llm", enum=["baseline", "llm", "anthropic" , "both"])
):
    start_total = time.perf_counter()
    file_bytes = await file.read()
    raw_text = extract_text_with_pdfplumber(file_bytes)
    
    response = {
        "filename": file.filename,
        "caracteres_detectados": len(raw_text),
    }

    if method == "baseline":
        t0 = time.perf_counter()
        response["datos"] = baseline_extract(raw_text)
        response["latencia_segundos"] = round(time.perf_counter() - t0, 4)
        response["metodo"] = "baseline_regex"

    elif method == "llm":
        t0 = time.perf_counter()
        response["datos"] = extract_with_llm(raw_text)
        response["latencia_segundos"] = round(time.perf_counter() - t0, 4)
        response["metodo"] = "gemini-1.5-flash"

    elif method == "anthropic":
        t0 = time.perf_counter()
        result = extract_with_anthropic(raw_text)
        latencia = round(time.perf_counter() - t0, 4)

        response["metodo"] = "claude-3-5-haiku"
        response["latencia_segundos"] = latencia
        response["datos"] = result["data"]
        response["tokens"] = result["usage"]

    elif method == "both":
        t0 = time.perf_counter()
        res_base = baseline_extract(raw_text)
        t_base = round(time.perf_counter() - t0, 4)

        t1 = time.perf_counter()
        res_llm = extract_with_llm(raw_text)
        t_llm = round(time.perf_counter() - t1, 4)

        response["metodo"] = "comparacion"
        response["baseline"] = {"datos": res_base, "latencia_segundos": t_base}
        response["llm"] = {"datos": res_llm, "latencia_segundos": t_llm}

    response["tiempo_total_segundos"] = round(time.perf_counter() - start_total, 4)
    return response