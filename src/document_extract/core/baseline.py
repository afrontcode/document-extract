import io
import re
import pdfplumber

def extract_text_with_pdfplumber(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def baseline_extract(text: str) -> dict:
    ruc_match = re.search(r"(?:Numero de documento|RUC|R\.U\.C)[^\d]{1,20}((?:10|20)\d{9})", text, re.IGNORECASE)
    if not ruc_match:
        ruc_match = re.search(
            r"(?:n[uú]mero|nro\.?|n[°º])\s*(?:de\s*)?documento\s*:?\s*\n?\s*((?:10|20)\d{9})",
            text,
            re.IGNORECASE
        )

    cliente_match = re.search(r"Nombre\s*:\s*(.+)", text, re.IGNORECASE)
    fecha_match = re.search(r"Fecha de Emisi[oó]n\s*[:\.-]?\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    moneda_match = re.search(r"Moneda\s*[:\.-]?\s*([A-Za-z]+)", text, re.IGNORECASE)
    total_match = re.search(r"(?:TOTAL|Precio de Venta|Importe Total)[^\d]{1,20}([\d,]+\.\d{2})", text, re.IGNORECASE)

    return {
        "cliente_nombre": cliente_match.group(1).strip() if cliente_match else None,
        "ruc_cliente": ruc_match.group(1) if ruc_match else None,
        "fecha_emision": fecha_match.group(1) if fecha_match else None,
        "moneda": moneda_match.group(1).strip() if moneda_match else None,
        "monto_total": float(total_match.group(1).replace(",", "")) if total_match else None,
        "caracteres_leidos": len(text)
    }