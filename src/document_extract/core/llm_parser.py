import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import time
from google.genai.errors import ServerError

# Carga variables de entorno
load_dotenv()

class InvoiceData(BaseModel):
    emisor_nombre: Optional[str] = Field(default=None, description="Nombre de la empresa que emite la factura")
    emisor_ruc: Optional[str] = Field(default=None, description="RUC de la empresa emisora")
    cliente_nombre: Optional[str] = Field(default=None, description="Nombre o razón social del cliente")
    cliente_ruc: Optional[str] = Field(default=None, description="RUC del cliente")
    fecha_emision: Optional[str] = Field(default=None, description="Fecha de emisión DD/MM/YYYY")
    moneda: Optional[str] = Field(default=None, description="Moneda (ej. SOLES, USD)")
    monto_total: Optional[float] = Field(default=None, description="Importe total a pagar")
    descripcion_servicio: Optional[str] = Field(default=None, description="Concepto o descripción principal facturada")


def load_prompt(version: str = "v1_invoice.txt") -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / version
    return prompt_path.read_text(encoding="utf-8")


def extract_with_llm(text: str, model_name: str = "gemini-1.5-flash", prompt_file: str = "v1_invoice.txt") -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    system_instruction = load_prompt(prompt_file)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"Texto de la factura:\n\n{text}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=InvoiceData,
                    temperature=0.0,
                )
            )
            return json.loads(response.text)
        except ServerError as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))  # Espera 2s, luego 4s...
                continue
            raise e

    return json.loads(response.text)