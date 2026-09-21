import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import anthropic
from pydantic import BaseModel, Field

load_dotenv()

class InvoiceData(BaseModel):
    emisor_nombre: Optional[str] = Field(default=None, description="Nombre de la empresa que emite la factura")
    emisor_ruc: Optional[str] = Field(default=None, description="RUC de la empresa emisora")
    cliente_nombre: Optional[str] = Field(default=None, description="Nombre o razón social del cliente")
    cliente_ruc: Optional[str] = Field(default=None, description="RUC del cliente")
    fecha_emision: Optional[str] = Field(default=None, description="Fecha de emisión DD/MM/YYYY")
    moneda: Optional[str] = Field(default=None, description="Moneda (ej. SOLES, USD)")
    monto_total: Optional[float] = Field(default=None, description="Importe total a pagar")
    descripcion_servicio: Optional[str] = Field(default=None, description="Concepto principal facturado")


def load_prompt(version: str = "v1_invoice.txt") -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / version
    return prompt_path.read_text(encoding="utf-8")


def extract_with_anthropic(
    text: str, 
    model_name: str = "claude-haiku-4-5-20251001",
    prompt_file: str = "v1_invoice.txt"
) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    system_instruction = load_prompt(prompt_file)

    # Convertimos el esquema de Pydantic en una herramienta forzada
    tool_definition = {
        "name": "record_invoice_data",
        "description": "Guarda los datos estructurados extraídos de una factura",
        "input_schema": InvoiceData.model_json_schema()
    }

    response = client.messages.create(
        model=model_name,
        max_tokens=1024,
        system=system_instruction,
        tools=[tool_definition],
        tool_choice={"type": "tool", "name": "record_invoice_data"},  # Fuerza a usar esta herramienta
        messages=[
            {"role": "user", "content": f"Texto de la factura:\n\n{text}"}
        ]
    )
    
    extracted_data = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "record_invoice_data":
            extracted_data = block.input
            break

    if not extracted_data:
        raise ValueError("No se pudo extraer la información estructurada con Anthropic.")

    # Información de tokens y costos
    usage_info = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
    }

    return {
        "data": extracted_data,
        "usage": usage_info
    }