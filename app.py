from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(page_title="BidWise | Equalização Tributária", layout="wide")

UF_OPTIONS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

INTERNAL_ICMS = {
    "AC": 19.0, "AL": 19.0, "AM": 20.0, "AP": 18.0, "BA": 20.5, "CE": 20.0, "DF": 20.0,
    "ES": 17.0, "GO": 19.0, "MA": 22.0, "MG": 18.0, "MS": 17.0, "MT": 17.0, "PA": 19.0,
    "PB": 20.0, "PE": 20.5, "PI": 21.0, "PR": 19.5, "RJ": 20.0, "RN": 20.0, "RO": 19.5,
    "RR": 20.0, "RS": 17.0, "SC": 17.0, "SE": 19.0, "SP": 18.0, "TO": 20.0,
}

FCP_DEFAULT = {uf: 2.0 for uf in UF_OPTIONS}


@dataclass
class Context:
    item_type: str
    supplier_regime: str
    supplier_profile: str
    origin: str
    destination: str
    nature: str
    ncm: str


@dataclass
class TaxLine:
    name: str
    amount: float
    recoverable: float
    non_recoverable: float
    note: str


def inject_brand_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bw-brand: #4A90A4; --bw-accent: #6F8797; --bw-accent-hover: #5F7686;
            --bw-text-primary: #1C2D3A; --bw-text-secondary: #3F4F5F; --bw-text-muted: #6B7E8A;
            --bw-surface-subtle: rgba(74, 144, 164, 0.08); --bw-border-subtle: rgba(196, 213, 223, 0.90);
            --bw-panel: #F7FAFC;
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(74, 144, 164, 0.08), transparent 28%),
                linear-gradient(180deg, #F9FBFD 0%, #F4F8FB 100%);
            color: var(--bw-text-primary);
        }
        .block-container { padding-top: 2rem; padding-bottom: 2.2rem; }
        .hero-card, .section-card, .kpi-card, .tax-card {
            border: 1px solid var(--bw-border-subtle); border-radius: 18px; background: rgba(255,255,255,0.90);
        }
        .hero-card {
            background: linear-gradient(135deg, rgba(74,144,164,0.10), rgba(255,255,255,0.92));
            padding: 1.4rem 1.5rem 1.2rem 1.5rem; margin-bottom: 1rem;
        }
        .hero-title { font-size: 2rem; font-weight: 700; line-height: 1.1; color: var(--bw-text-primary); margin-bottom: 0.25rem; }
        .hero-subtitle, .tax-note { color: var(--bw-text-secondary); }
        .kpi-card { padding: 1rem 1rem 0.85rem 1rem; min-height: 138px; background: var(--bw-panel); }
        .kpi-label { font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--bw-text-muted); margin-bottom: 0.45rem; }
        .kpi-value { font-size: 1.7rem; font-weight: 700; color: var(--bw-text-primary); margin-bottom: 0.35rem; }
        .tax-card { padding: 1rem; height: 100%; }
        .tax-title { font-weight: 700; color: var(--bw-text-primary); margin-bottom: 0.65rem; }
        .tax-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.55rem; }
        .tax-pill { background: var(--bw-surface-subtle); border: 1px solid var(--bw-border-subtle); border-radius: 12px; padding: 0.55rem 0.7rem; }
        .tax-pill-label { font-size: 0.78rem; color: var(--bw-text-muted); }
        .tax-pill-value { font-weight: 600; color: var(--bw-text-primary); }
        .info-strip { background: #E8EFF6; color: #24425A; border: 1px solid #C7D6E2; border-radius: 14px; padding: 0.8rem 0.95rem; margin-bottom: 1rem; }
        div[data-testid="stDataEditor"] { border: 1px solid var(--bw-border-subtle); border-radius: 14px; overflow: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def money(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


def interstate_icms(origin: str, destination: str) -> float:
    if origin == destination:
        return INTERNAL_ICMS.get(destination, 18.0)
    if origin in {"Internacional", "ZFM"}:
        return INTERNAL_ICMS.get(destination, 18.0)
    if destination in {"ES", "MG", "RJ", "RS", "SC", "SP", "PR"}:
        return 12.0
    return 7.0


def default_rates(ctx: Context) -> Dict[str, float]:
    imported = ctx.origin == "Internacional"
    zfm = ctx.origin == "ZFM"
    material = ctx.item_type == "Material"
    service = ctx.item_type == "Serviço"
    supplier_industry = ctx.supplier_profile in {"Indústria", "Importador"}
    same_state = ctx.origin == ctx.destination and ctx.origin not in {"Internacional", "ZFM"}
    icms_internal = INTERNAL_ICMS.get(ctx.destination, 18.0)
    icms_rate = interstate_icms(ctx.origin, ctx.destination)
    difal_rate = 0.0
    if material and not same_state and not imported and ctx.nature in {"Uso / consumo", "Ativo imobilizado"}:
        difal_rate = max(icms_internal - icms_rate, 0.0)
    rates = {
        "Preço base da proposta": 1000.0, "Preço bruto da proposta": None, "Custo líquido equalizado": None,
        "Frete (R$)": 0.0, "Seguro (R$)": 0.0, "Outras despesas (R$)": 0.0, "Desconto (R$)": 0.0,
        "Base aduaneira (R$)": None, "MVA-ST (%)": 40.0 if material else 0.0,
        "ICMS (%)": icms_rate if material else 0.0, "IPI (%)": 5.0 if material and supplier_industry and not zfm else 0.0,
        "PIS (%)": 1.65 if material and not imported and not zfm else 0.0, "COFINS (%)": 7.60 if material and not imported and not zfm else 0.0,
        "ICMS-ST (%)": 0.0, "DIFAL (%)": difal_rate if material else 0.0, "FCP (%)": FCP_DEFAULT.get(ctx.destination, 2.0) if material and not same_state else 0.0,
        "ISS (%)": 5.0 if service else 0.0, "II (%)": 14.0 if imported and material else 0.0,
        "PIS-Importação (%)": 2.10 if imported and material else 0.0, "COFINS-Importação (%)": 9.65 if imported and material else 0.0,
        "Despesas aduaneiras (R$)": 250.0 if imported else 0.0,
    }
    if service:
        rates.update({"PIS (%)": 1.65, "COFINS (%)": 7.60, "ICMS (%)": 0.0, "IPI (%)": 0.0, "ICMS-ST (%)": 0.0, "DIFAL (%)": 0.0, "FCP (%)": 0.0, "MVA-ST (%)": 0.0})
    if ctx.supplier_regime == "Simples Nacional":
        rates["PIS (%)"] = 0.0
        rates["COFINS (%)"] = 0.0
    if zfm:
        rates["IPI (%)"] = 0.0
        rates["PIS (%)"] = 0.0
        rates["COFINS (%)"] = 0.0
    return rates


def build_editor_df(rows: List[Tuple[str, Optional[float], str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Parâmetro", "Valor", "Unidade"])


def coerce_map(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    result: Dict[str, Optional[float]] = {}
    for _, row in df.iterrows():
        value = row["Valor"]
        result[row["Parâmetro"]] = None if pd.isna(value) else float(value)
    return result


def merge_editor_state(store_key: str, defaults: pd.DataFrame) -> pd.DataFrame:
    state_key = f"{store_key}_defaults"
    if store_key not in st.session_state:
        st.session_state[store_key] = defaults.copy()
        st.session_state[state_key] = defaults.copy()
        return defaults
    previous = st.session_state[store_key]
    previous_defaults = st.session_state.get(state_key, defaults)
    previous_values = {row["Parâmetro"]: row["Valor"] for _, row in previous.iterrows()}
    previous_default_values = {row["Parâmetro"]: row["Valor"] for _, row in previous_defaults.iterrows()}
    merged = defaults.copy()
    for index, row in merged.iterrows():
        param = row["Parâmetro"]
        if param not in previous_values:
            continue
        old_default = previous_default_values.get(param)
        old_value = previous_values.get(param)
        if pd.isna(old_value) and pd.isna(old_default):
            merged.at[index, "Valor"] = old_value
        elif old_value != old_default:
            merged.at[index, "Valor"] = old_value
    st.session_state[store_key] = merged
    st.session_state[state_key] = defaults.copy()
    return merged


def credit_flags(ctx: Context) -> Dict[str, bool]:
    material = ctx.item_type == "Material"
    imported = ctx.origin == "Internacional"
    service = ctx.item_type == "Serviço"
    supplier_industry = ctx.supplier_profile in {"Indústria", "Importador"}
    pis_cofins_credit = ctx.supplier_regime != "Simples Nacional"
    icms_credit = material and ctx.supplier_regime != "Simples Nacional"
    ipi_credit = material and supplier_industry
    if ctx.nature == "Uso / consumo":
        pis_cofins_credit = False
        icms_credit = False
        ipi_credit = False
    if service:
        icms_credit = False
        ipi_credit = False
    if imported:
        icms_credit = material
        ipi_credit = material
    return {
        "ICMS": icms_credit,
        "IPI": ipi_credit,
        "PIS": pis_cofins_credit,
        "COFINS": pis_cofins_credit,
        "PIS-Importação": pis_cofins_credit and imported,
        "COFINS-Importação": pis_cofins_credit and imported,
    }


def difal_applicable(ctx: Context) -> bool:
    return (
        ctx.item_type == "Material"
        and ctx.origin not in {"Internacional", "ZFM"}
        and ctx.origin != ctx.destination
        and ctx.nature in {"Uso / consumo", "Ativo imobilizado"}
    )


def compute_taxes(ctx: Context, values: Dict[str, Optional[float]]) -> Dict[str, object]:
    base_input = values.get("Preço base da proposta")
    gross_input = values.get("Preço bruto da proposta")
    liquid_input = values.get("Custo líquido equalizado")
    imported = ctx.origin == "Internacional"
    material = ctx.item_type == "Material"
    service = ctx.item_type == "Serviço"
    freight = values.get("Frete (R$)") or 0.0
    insurance = values.get("Seguro (R$)") or 0.0
    other_expenses = values.get("Outras despesas (R$)") or 0.0
    discount = values.get("Desconto (R$)") or 0.0
    customs_base_override = values.get("Base aduaneira (R$)")
    mva_st = (values.get("MVA-ST (%)") or 0.0) / 100.0
    icms = (values.get("ICMS (%)") or 0.0) / 100.0
    ipi = (values.get("IPI (%)") or 0.0) / 100.0
    pis = (values.get("PIS (%)") or 0.0) / 100.0
    cofins = (values.get("COFINS (%)") or 0.0) / 100.0
    icms_st = (values.get("ICMS-ST (%)") or 0.0) / 100.0
    difal = (values.get("DIFAL (%)") or 0.0) / 100.0
    fcp = (values.get("FCP (%)") or 0.0) / 100.0
    iss = (values.get("ISS (%)") or 0.0) / 100.0
    ii = (values.get("II (%)") or 0.0) / 100.0
    pis_import = (values.get("PIS-Importação (%)") or 0.0) / 100.0
    cofins_import = (values.get("COFINS-Importação (%)") or 0.0) / 100.0
    customs_expenses = values.get("Despesas aduaneiras (R$)") or 0.0
    allowed_diffal = difal_applicable(ctx)
    credits = credit_flags(ctx)
    difal_effective = difal if allowed_diffal else 0.0
    fcp_effective = fcp if allowed_diffal else 0.0

    def calculate_from_base(base_value: float) -> Dict[str, float]:
        operation_value = max(base_value + freight + insurance + other_expenses - discount, 0.0)
        customs_base = customs_base_override if customs_base_override is not None else operation_value
        icms_own_base = operation_value
        icms_own_amount = icms_own_base * icms if material else 0.0
        ii_amount = customs_base * ii if imported and material else 0.0
        ipi_base = operation_value + ii_amount
        ipi_amount = ipi_base * ipi if material else 0.0
        pis_amount = operation_value * pis if (material or service) and not imported else 0.0
        cofins_amount = operation_value * cofins if (material or service) and not imported else 0.0
        pis_import_base = customs_base + ii_amount + customs_expenses
        pis_import_amount = pis_import_base * pis_import if imported and material else 0.0
        cofins_import_amount = pis_import_base * cofins_import if imported and material else 0.0
        icms_st_manual = operation_value * icms_st if material else 0.0
        st_base = operation_value * (1.0 + mva_st) if material else 0.0
        st_due = max((st_base * icms) - icms_own_amount, 0.0) if material else 0.0
        icms_st_amount = max(icms_st_manual, st_due)
        difal_base = operation_value
        difal_amount = difal_base * difal_effective if material else 0.0
        fcp_amount = difal_base * fcp_effective if material else 0.0
        iss_amount = operation_value * iss if service else 0.0

        gross = operation_value + customs_expenses + ii_amount + ipi_amount + pis_import_amount + cofins_import_amount + icms_st_amount + difal_amount + fcp_amount + iss_amount
        recoverable_total = (
            (icms_own_amount if credits["ICMS"] else 0.0)
            + (ipi_amount if credits["IPI"] else 0.0)
            + (pis_amount if credits["PIS"] else 0.0)
            + (cofins_amount if credits["COFINS"] else 0.0)
            + (pis_import_amount if credits["PIS-Importação"] else 0.0)
            + (cofins_import_amount if credits["COFINS-Importação"] else 0.0)
        )
        liquid = gross - recoverable_total
        return {
            "operation_value": operation_value,
            "customs_base": customs_base,
            "icms_own_amount": icms_own_amount,
            "ii_amount": ii_amount,
            "ipi_amount": ipi_amount,
            "pis_amount": pis_amount,
            "cofins_amount": cofins_amount,
            "pis_import_amount": pis_import_amount,
            "cofins_import_amount": cofins_import_amount,
            "icms_st_amount": icms_st_amount,
            "st_due": st_due,
            "difal_amount": difal_amount,
            "fcp_amount": fcp_amount,
            "iss_amount": iss_amount,
            "gross": gross,
            "liquid": liquid,
        }

    inferred_bases: List[float] = []
    if base_input is not None:
        inferred_bases.append(base_input)
    if gross_input is not None:
        probe_base = max((gross_input - freight - insurance - other_expenses + discount), 0.0)
        for _ in range(6):
            probe_result = calculate_from_base(probe_base)
            delta = gross_input - probe_result["gross"]
            if abs(delta) < 0.01:
                break
            probe_base = max(probe_base + (delta * 0.85), 0.0)
        inferred_bases.append(probe_base)
    if liquid_input is not None:
        probe_base = max((liquid_input - freight - insurance - other_expenses + discount), 0.0)
        for _ in range(6):
            probe_result = calculate_from_base(probe_base)
            delta = liquid_input - probe_result["liquid"]
            if abs(delta) < 0.01:
                break
            probe_base = max(probe_base + (delta * 0.85), 0.0)
        inferred_bases.append(probe_base)

    warnings: List[str] = []
    if not inferred_bases:
        warnings.append("Preencha pelo menos um dos campos de preço para iniciar a equalização.")
        return {"base": None, "gross": None, "liquid": None, "lines": [], "warnings": warnings, "summary": {}}

    base = sum(inferred_bases) / len(inferred_bases)
    spread = max(inferred_bases) - min(inferred_bases)
    if len(inferred_bases) > 1 and spread > 0.05:
        warnings.append("Os preços informados não fecham exatamente entre si. A calculadora assumiu uma média implícita.")

    result_map = calculate_from_base(base)
    operation_value = result_map["operation_value"]
    ii_amount = result_map["ii_amount"]
    icms_amount = result_map["icms_own_amount"]
    ipi_amount = result_map["ipi_amount"]
    pis_amount = result_map["pis_amount"]
    cofins_amount = result_map["cofins_amount"]
    icms_st_amount = result_map["icms_st_amount"]
    difal_amount = result_map["difal_amount"]
    fcp_amount = result_map["fcp_amount"]
    iss_amount = result_map["iss_amount"]
    pis_import_amount = result_map["pis_import_amount"]
    cofins_import_amount = result_map["cofins_import_amount"]

    lines: List[TaxLine] = []
    if material:
        lines.extend([
            TaxLine("ICMS", icms_amount, icms_amount if credits["ICMS"] else 0.0, icms_amount if not credits["ICMS"] else 0.0, "Calculado sobre o valor da operação (produto + frete + despesas - desconto)."),
            TaxLine("IPI", ipi_amount, ipi_amount if credits["IPI"] else 0.0, ipi_amount if not credits["IPI"] else 0.0, "Base simplificada do IPI considera valor da operação e II quando importado."),
            TaxLine("ICMS-ST", icms_st_amount, 0.0, icms_st_amount, "A calculadora usa o maior entre ST manual e ST estimado por MVA."),
            TaxLine("DIFAL", difal_amount, 0.0, difal_amount, "Aplicado apenas em operação interestadual de uso/consumo ou ativo imobilizado."),
            TaxLine("FCP", fcp_amount, 0.0, fcp_amount, "FCP segue a mesma elegibilidade do DIFAL no modelo."),
        ])
        if imported:
            lines.extend([
                TaxLine("II", ii_amount, 0.0, ii_amount, "Tratado como custo não recuperável da importação."),
                TaxLine("PIS-Importação", pis_import_amount, pis_import_amount if credits["PIS-Importação"] else 0.0, pis_import_amount if not credits["PIS-Importação"] else 0.0, "Crédito geral do Lucro Real quando elegível."),
                TaxLine("COFINS-Importação", cofins_import_amount, cofins_import_amount if credits["COFINS-Importação"] else 0.0, cofins_import_amount if not credits["COFINS-Importação"] else 0.0, "Crédito geral do Lucro Real quando elegível."),
            ])
        else:
            lines.extend([
                TaxLine("PIS", pis_amount, pis_amount if credits["PIS"] else 0.0, pis_amount if not credits["PIS"] else 0.0, "Crédito simplificado do regime não cumulativo."),
                TaxLine("COFINS", cofins_amount, cofins_amount if credits["COFINS"] else 0.0, cofins_amount if not credits["COFINS"] else 0.0, "Crédito simplificado do regime não cumulativo."),
            ])
    elif service:
        lines.extend([
            TaxLine("ISS", iss_amount, 0.0, iss_amount, "Tratado como custo por fora no comparativo do serviço."),
            TaxLine("PIS", pis_amount, pis_amount if credits["PIS"] else 0.0, pis_amount if not credits["PIS"] else 0.0, "Crédito geral simplificado para serviço tomado."),
            TaxLine("COFINS", cofins_amount, cofins_amount if credits["COFINS"] else 0.0, cofins_amount if not credits["COFINS"] else 0.0, "Crédito geral simplificado para serviço tomado."),
        ])
    total_recoverable = sum(line.recoverable for line in lines)
    total_non_recoverable = sum(line.non_recoverable for line in lines)
    gross = result_map["gross"]
    liquid = result_map["liquid"]
    if ctx.supplier_regime == "Simples Nacional":
        warnings.append("Fornecedor no Simples Nacional reduz ou elimina créditos no MVP. Valide o cenário real antes da decisão final.")
    if ctx.nature == "Uso / consumo":
        warnings.append("Natureza 'Uso / consumo' bloqueia créditos relevantes no MVP para evitar superestimar benefício fiscal.")
    if ctx.origin == "Internacional":
        warnings.append("Importação usa bases gerais simplificadas. Custos aduaneiros reais podem exigir ajuste adicional.")
    if ctx.origin == "ZFM":
        warnings.append("ZFM foi modelada com regra geral simplificada. O benefício efetivo pode variar por produto e destinatário.")
    if material and not ctx.ncm.strip():
        warnings.append("NCM é opcional neste MVP, mas recomendado para calibrar IPI, ST e benefícios com mais segurança.")
    if discount > (base + freight + insurance + other_expenses):
        warnings.append("Desconto maior do que o valor da operação gera base tributável zerada no modelo.")
    if material and not allowed_diffal and (difal > 0 or fcp > 0):
        warnings.append("DIFAL/FCP informados, mas a operação atual não se enquadra na regra simplificada aplicada.")

    return {
        "base": base,
        "gross": gross,
        "liquid": liquid,
        "lines": lines,
        "warnings": warnings,
        "summary": {
            "recoverable": total_recoverable,
            "non_recoverable": total_non_recoverable,
            "gross_delta": gross - base,
            "operation_value": operation_value,
        },
    }


def render_kpis(result: Dict[str, object]) -> None:
    kpi_cols = st.columns(4)
    items = [
        ("Preço base", money(result["base"]), "Referência econômica sem equalização."),
        ("Preço bruto", money(result["gross"]), "Valor da proposta com tributos por fora e custos adicionais."),
        ("Custo líquido", money(result["liquid"]), "Preço equalizado após créditos recuperáveis."),
        ("Tributos não recuperáveis", money(result["summary"].get("non_recoverable")), "Impacto direto no custo da compra."),
    ]
    for col, (label, value, note) in zip(kpi_cols, items):
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="tax-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tax_cards(lines: List[TaxLine]) -> None:
    if not lines:
        return
    for start in range(0, len(lines), 3):
        cols = st.columns(3)
        for col, line in zip(cols, lines[start : start + 3]):
            col.markdown(
                f"""
                <div class="tax-card">
                    <div class="tax-title">{line.name}</div>
                    <div class="tax-grid">
                        <div class="tax-pill">
                            <div class="tax-pill-label">Valor do tributo</div>
                            <div class="tax-pill-value">{money(line.amount)}</div>
                        </div>
                        <div class="tax-pill">
                            <div class="tax-pill-label">Crédito recuperável</div>
                            <div class="tax-pill-value">{money(line.recoverable)}</div>
                        </div>
                        <div class="tax-pill">
                            <div class="tax-pill-label">Parcela não recuperável</div>
                            <div class="tax-pill-value">{money(line.non_recoverable)}</div>
                        </div>
                        <div class="tax-pill">
                            <div class="tax-pill-label">Impacto no custo líquido</div>
                            <div class="tax-pill-value">{money(line.non_recoverable)}</div>
                        </div>
                    </div>
                    <div class="tax-note" style="margin-top: 0.7rem;">{line.note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def explanation_tab(ctx: Context, values: Dict[str, Optional[float]]) -> None:
    st.markdown("### Lógica tributária do MVP")
    st.markdown(
        """
        Esta página usa regras gerais para equalização de propostas no Brasil, com foco em **comprador no Lucro Real**.
        O objetivo é comparar o preço apresentado pelo fornecedor com o custo líquido efetivo para a empresa compradora.
        """
    )
    bullets = [
        f"**ICMS:** calculado pela UF de origem e destino. Operação {ctx.origin} → {ctx.destination}.",
        "**Valor da operação:** usa preço base + frete + seguro + outras despesas - desconto como base principal dos tributos.",
        "**IPI:** tratado como tributo por fora no comparativo de material, com crédito em cenários gerais elegíveis.",
        "**PIS/COFINS:** entram como crédito simplificado no regime não cumulativo, exceto quando a natureza bloqueia o crédito ou o fornecedor está no Simples.",
        "**ICMS-ST:** usa maior valor entre alíquota manual e estimativa por MVA para reduzir subestimação de custo.",
        "**DIFAL e FCP:** aplicados no modelo apenas quando há operação interestadual para uso/consumo ou ativo imobilizado.",
        "**Importação:** quando marcada, a tela habilita II, PIS-Importação, COFINS-Importação e despesas aduaneiras.",
        "**ZFM:** usa defaults conservadores e mostra alerta porque o benefício depende do enquadramento real da operação.",
    ]
    for bullet in bullets:
        st.markdown(f"- {bullet}")
    st.markdown("### Como cada tributo entra no cálculo")
    detail_rows = [
        ["ICMS", "Valor embutido no preço base. Se elegível, reduz o custo líquido como crédito."],
        ["IPI", "Adicionado por fora na proposta e, quando recuperável, abatido do custo líquido."],
        ["PIS / COFINS", "No modelo doméstico, incidem no valor da operação e entram na equalização via crédito recuperável."],
        ["ISS", "Para serviço, tratado como custo por fora no preço bruto."],
        ["ICMS-ST", "Calculado pelo maior entre ST manual e ST estimado por MVA, sempre como custo não recuperável no MVP."],
        ["DIFAL / FCP", "Aplicados apenas no cenário simplificado de interestadual com natureza de uso/consumo ou ativo."],
        ["II", "Custo não recuperável da importação."],
        ["PIS-Importação / COFINS-Importação", "Base simplificada: base aduaneira + II + despesas aduaneiras; podem gerar crédito no Lucro Real."],
        ["Despesas aduaneiras", "Entram no preço bruto e no custo líquido; quando informado, podem compor também a base de importação."],
    ]
    st.table(pd.DataFrame(detail_rows, columns=["Tributo", "Tratamento no MVP"]))
    st.markdown("### Premissas relevantes deste cenário")
    assumptions = [
        f"Natureza selecionada: **{ctx.nature}**.",
        f"Regime do fornecedor: **{ctx.supplier_regime}**.",
        f"Perfil do fornecedor: **{ctx.supplier_profile}**.",
        f"NCM informado: **{ctx.ncm or 'não informado'}**.",
        f"ICMS configurado: **{pct(values.get('ICMS (%)') or 0.0)}**.",
        f"IPI configurado: **{pct(values.get('IPI (%)') or 0.0)}**.",
    ]
    for assumption in assumptions:
        st.markdown(f"- {assumption}")
    st.info("Este MVP foi desenhado para apoio à equalização comercial. Antes de usar em fechamento contratual ou compliance fiscal, vale validar as bases com a área tributária.")


def main() -> None:
    inject_brand_css()
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">BidWise Tax Equalizer</div>
            <p class="hero-subtitle">
                Compare preço com impostos e custo líquido equalizado em compras de material ou contratação de serviços,
                usando regras gerais da legislação brasileira para um comprador no Lucro Real.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown("### Parâmetros da operação")
        item_type = st.selectbox("Material ou serviço", ["Material", "Serviço"])
        supplier_regime = st.selectbox("Regime do fornecedor", ["Lucro Real", "Lucro Presumido", "Simples Nacional"])
        supplier_profiles = ["Indústria", "Atacadista / distribuidor", "Varejista", "Importador"] if item_type == "Material" else ["Prestador de serviço", "Consultoria", "Tecnologia", "Terceirização"]
        supplier_profile = st.selectbox("Perfil do fornecedor", supplier_profiles)
        origin_options = ["Internacional", "ZFM"] + UF_OPTIONS if item_type == "Material" else UF_OPTIONS
        origin_default = origin_options.index("SP") if "SP" in origin_options else 0
        origin = st.selectbox("Origem", origin_options, index=origin_default)
        destination = st.selectbox("Destino", UF_OPTIONS, index=UF_OPTIONS.index("SP"))
        nature_options = ["Industrialização", "Ativo imobilizado", "Uso / consumo"] if item_type == "Material" else ["Tomada do serviço"]
        nature = st.selectbox("Natureza", nature_options)
        ncm = st.text_input("NCM (opcional, recomendado)", placeholder="Ex.: 8479.89.99") if item_type == "Material" else ""
        st.markdown(
            """
            <div class="info-strip">
                Comprador fixo no <strong>Lucro Real</strong>. O MVP prioriza regras gerais para apoiar equalização de propostas,
                com foco em velocidade de análise e transparência das premissas.
            </div>
            """,
            unsafe_allow_html=True,
        )
    ctx = Context(item_type, supplier_regime, supplier_profile, origin, destination, nature, ncm)
    defaults = default_rates(ctx)
    price_rows = [
        ("Preço base da proposta", defaults["Preço base da proposta"], "R$"),
        ("Preço bruto da proposta", defaults["Preço bruto da proposta"], "R$"),
        ("Custo líquido equalizado", defaults["Custo líquido equalizado"], "R$"),
        ("Frete (R$)", defaults["Frete (R$)"], "R$"),
        ("Seguro (R$)", defaults["Seguro (R$)"], "R$"),
        ("Outras despesas (R$)", defaults["Outras despesas (R$)"], "R$"),
        ("Desconto (R$)", defaults["Desconto (R$)"], "R$"),
    ]
    rate_rows = [
        ("ICMS (%)", defaults["ICMS (%)"], "%"),
        ("IPI (%)", defaults["IPI (%)"], "%"),
        ("PIS (%)", defaults["PIS (%)"], "%"),
        ("COFINS (%)", defaults["COFINS (%)"], "%"),
        ("MVA-ST (%)", defaults["MVA-ST (%)"], "%"),
        ("ICMS-ST (%)", defaults["ICMS-ST (%)"], "%"),
        ("DIFAL (%)", defaults["DIFAL (%)"], "%"),
        ("FCP (%)", defaults["FCP (%)"], "%"),
        ("ISS (%)", defaults["ISS (%)"], "%"),
    ]
    if origin == "Internacional":
        rate_rows.extend([
            ("II (%)", defaults["II (%)"], "%"),
            ("PIS-Importação (%)", defaults["PIS-Importação (%)"], "%"),
            ("COFINS-Importação (%)", defaults["COFINS-Importação (%)"], "%"),
            ("Despesas aduaneiras (R$)", defaults["Despesas aduaneiras (R$)"], "R$"),
            ("Base aduaneira (R$)", defaults["Base aduaneira (R$)"], "R$"),
        ])
    price_df = merge_editor_state("price_editor_store", build_editor_df(price_rows))
    rate_df = merge_editor_state("rate_editor_store", build_editor_df(rate_rows))
    tab_calc, tab_expl = st.tabs(["Calculadora", "Explicação dos tributos"])
    with tab_calc:
        left, right = st.columns([1.15, 0.85], gap="large")
        with left:
            st.markdown("### Entrada de dados")
            st.caption("Você pode começar por qualquer um dos preços. Quando houver mais de um valor preenchido, a calculadora testa a consistência e ajusta o cenário.")
            edited_prices = st.data_editor(
                price_df, key="price_editor_widget", use_container_width=True, hide_index=True,
                column_config={"Parâmetro": st.column_config.TextColumn(disabled=True), "Valor": st.column_config.NumberColumn(format="%.2f"), "Unidade": st.column_config.TextColumn(disabled=True)},
            )
            st.session_state["price_editor_store"] = edited_prices.copy()
            st.markdown("### Alíquotas e parâmetros")
            edited_rates = st.data_editor(
                rate_df, key="rate_editor_widget", use_container_width=True, hide_index=True,
                column_config={"Parâmetro": st.column_config.TextColumn(disabled=True), "Valor": st.column_config.NumberColumn(format="%.2f"), "Unidade": st.column_config.TextColumn(disabled=True)},
            )
            st.session_state["rate_editor_store"] = edited_rates.copy()
        merged_values = coerce_map(edited_prices)
        merged_values.update(coerce_map(edited_rates))
        result = compute_taxes(ctx, merged_values)
        with right:
            st.markdown("### Saída equalizada")
            if result["base"] is None:
                st.warning("Aguardando pelo menos um preço para iniciar os cálculos.")
            else:
                render_kpis(result)
                output_rows = [
                    ("Preço base da proposta", result["base"], "R$"),
                    ("Valor da operação", result["summary"].get("operation_value"), "R$"),
                    ("Preço bruto da proposta", result["gross"], "R$"),
                    ("Custo líquido equalizado", result["liquid"], "R$"),
                    ("Tributos recuperáveis", result["summary"].get("recoverable"), "R$"),
                    ("Tributos não recuperáveis", result["summary"].get("non_recoverable"), "R$"),
                    ("Diferença bruto vs líquido", result["gross"] - result["liquid"], "R$"),
                ]
                st.dataframe(build_editor_df(output_rows), use_container_width=True, hide_index=True)
            for warning in result["warnings"]:
                st.warning(warning)
        st.markdown("### Tributos detalhados")
        render_tax_cards(result["lines"])
    with tab_expl:
        explanation_tab(ctx, merged_values)


if __name__ == "__main__":
    main()
