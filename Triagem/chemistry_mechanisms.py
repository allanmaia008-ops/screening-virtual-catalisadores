"""Reaction-specific literature context for the Chemistry results panel."""

from __future__ import annotations

import html
import re
import unicodedata


MECHANISMS = {
    "metanacao": {
        "label": ("Metanação de CO₂", "CO₂ methanation"),
        "metals": {"ni"}, "support": "y2o3", "promoter": None,
        "steps": ["CO₂ adsorvido", "formiato superficial (HCOO*)", "hidrogenação sequencial", "CH₄ + H₂O"],
        "steps_en": ["Adsorbed CO₂", "Surface formate (HCOO*)", "Sequential hydrogenation", "CH₄ + H₂O"],
        "finding": "Formiato foi confirmado por DRIFTS in situ em Ni/Y₂O₃; esta interpretação é específica desse sistema.",
        "finding_en": "Formate was confirmed by in situ DRIFTS on Ni/Y₂O₃; this interpretation is specific to that system.",
        "risk": "Avaliar intermediários carbonáceos e estabilidade da fase ativa sob as condições de hidrogenação; a fórmula, por si só, não quantifica esses efeitos.",
        "risk_en": "Assess carbonaceous intermediates and active-phase stability under hydrogenation conditions; the formula alone does not quantify these effects.",
        "citation": "Hasan et al. (2021), PCCP", "doi": "https://doi.org/10.1039/D0CP06257J",
    },
    "rwgs": {
        "label": ("RWGS", "RWGS"),
        "metals": {"au"}, "support": "ceo2", "promoter": None,
        "steps": ["CO₂ + H₂ ativados", "carbonato / formiato*", "rota associativa proposta", "CO + H₂O"],
        "steps_en": ["Activated CO₂ + H₂", "Carbonate / formate*", "Proposed associative route", "CO + H₂O"],
        "finding": "Para Au/CeO₂(111), espectroscopias operando e transiente sustentaram uma rota associativa via carbonato/formiato; a contribuição redox foi considerada menor nesse sistema.",
        "finding_en": "For Au/CeO₂(111), operando and transient spectroscopy supported an associative carbonate/formate route; the redox contribution was considered minor in that system.",
        "risk": "Seletividade e estado redox dependem das condições e da interface metal–suporte; não inferir desempenho ou estabilidade apenas pela composição.",
        "risk_en": "Selectivity and redox state depend on conditions and the metal–support interface; do not infer performance or stability from composition alone.",
        "citation": "Ziemba et al. (2022), Applied Catalysis B", "doi": "https://doi.org/10.1016/j.apcatb.2021.120825",
    },
    "reforma": {
        "label": ("Reforma seca de CH₄", "Dry reforming of CH₄"),
        "metals": {"pt", "ni"}, "support": "ceo2", "promoter": None,
        "steps": ["CH₄ ativado", "CHₓ* / C* superficial", "CO₂ → O* na interface", "C* + O* → CO"],
        "steps_en": ["Activated CH₄", "Surface CHₓ* / C*", "CO₂ → interfacial O*", "C* + O* → CO"],
        "finding": "Em Pt–Ni/CeO₂, DRIFTS-MS associou espécies O* derivadas de CO₂ à oxidação de carbono superficial. Isso não torna resistência ao coque automática em outras composições.",
        "finding_en": "On Pt–Ni/CeO₂, DRIFTS-MS linked CO₂-derived O* species to surface-carbon oxidation. Coke resistance is not automatic for other compositions.",
        "risk": "A reforma seca envolve risco de deposição de carbono e sinterização em alta temperatura. O efeito protetor reportado é específico a Pt–Ni/CeO₂ e às condições estudadas.",
        "risk_en": "Dry reforming involves carbon-deposition and high-temperature sintering risks. The reported protective effect is specific to Pt–Ni/CeO₂ and the studied conditions.",
        "citation": "Chen et al. (2021), Catalysis Science & Technology", "doi": "https://doi.org/10.1039/D1CY00382H",
    },
}


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")))


def mechanism_context(reaction: str, active_metals: list[str], promoter: str, support: str) -> dict | None:
    """Match the current screening composition to a reaction-specific reference."""
    mechanism = MECHANISMS.get(reaction)
    if mechanism is None:
        return None
    metals_match = {_norm(metal) for metal in active_metals if _norm(metal)} == mechanism["metals"]
    support_match = _norm(support) == mechanism["support"]
    promoter_match = _norm(promoter) == _norm(mechanism["promoter"] or "")
    return {**mechanism, "direct_match": metals_match and support_match and promoter_match,
            "metals_match": metals_match, "support_match": support_match, "promoter_match": promoter_match}


def render_mechanism_panel(st, reaction: str, formula: str, active_metals: list[str], promoter: str,
                           support: str, english: bool = False) -> None:
    """Render one literature pathway and composition-aware evidence checks."""
    context = mechanism_context(reaction, active_metals, promoter, support)
    if context is None:
        return

    title = "Literature mechanism for the selected reaction" if english else "Mecanismo da literatura para a reação selecionada"
    direct = context["direct_match"]
    status = (("Direct match to the cited system" if direct else "Related reference; composition differs") if english
              else ("Correspondência direta com o sistema citado" if direct else "Referência relacionada; composição diferente"))
    metal_label, promoter_label, support_label = (("Active metals", "Promoter", "Suggested support") if english
                                                   else ("Metais ativos", "Promotor", "Suporte sugerido"))
    evidence_text = ("Roles are not assigned to this composition without matching literature evidence." if english
                     else "Não se atribuem papéis mecanísticos a esta composição sem evidência correspondente.")
    if context["metals_match"]:
        evidence_text = ("The selected active-metal set matches the reference." if english
                         else "O conjunto de metais ativos selecionado corresponde ao da referência.")
    promoter_note = (("No promoter selected." if english else "Nenhum promotor selecionado.") if not promoter else
                     (f"{promoter} selected; its effect is not established by this reference." if english else
                      f"{promoter} selecionado; seu efeito não é estabelecido por esta referência."))
    support_note = (("Matches the reference support." if english else "Corresponde ao suporte da referência.") if context["support_match"] else
                    ("Differs from the reference support." if english else "Difere do suporte da referência."))
    steps = context["steps_en"] if english else context["steps"]
    pathway = " → ".join(f"<span class='chem-lit-step'>{html.escape(step)}</span>" for step in steps)
    risk_labels = (("Sintering", "Poisoning", "Dispersion", "Reaction-specific risk") if english else
                   ("Sinterização", "Envenenamento", "Dispersão", "Risco específico da reação"))
    risk_texts = (["Compare particle size before and after operation at relevant temperatures.",
                   "Check feed impurities and surface contamination after reaction.",
                   "Nominal composition does not determine dispersion; confirm by suitable characterization.",
                   context["risk_en"]] if english else
                  ["Comparar tamanho de partícula antes/depois nas temperaturas relevantes.",
                   "Verificar impurezas da alimentação e contaminação da superfície após reação.",
                   "Composição nominal não determina dispersão; confirmar por caracterização adequada.",
                   context["risk"]])
    risks = "".join(f"<div><b>{html.escape(label)}</b><p>{html.escape(text)}</p></div>" for label, text in zip(risk_labels, risk_texts))
    composition = (f"<div class='chem-lit-composition'><b>{html.escape(metal_label)}:</b> {html.escape(', '.join(active_metals) or '—')}<br>"
                   f"<b>{html.escape(promoter_label)}:</b> {html.escape(promoter or ('None' if english else 'Nenhum'))} · {html.escape(promoter_note)}<br>"
                   f"<b>{html.escape(support_label)}:</b> {html.escape(support or '—')} · {html.escape(support_note)}</div>")
    finding = context["finding_en"] if english else context["finding"]
    source_label = "Source" if english else "Fonte"
    mechanism_name = context["label"][1 if english else 0]
    st.markdown(
        f"""<style>
        .chem-lit-panel{{margin:18px 0;padding:16px;border:1px solid #D7E3DD;border-radius:10px;background:#fff;color:#14213D}}
        .chem-lit-panel h3{{margin:0 0 10px;color:#153A70}}.chem-lit-composition{{padding:10px;border:1px solid #E3EAE6;border-radius:7px;line-height:1.8}}
        .chem-lit-flow{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:12px 0}}.chem-lit-step{{padding:8px 10px;border-radius:7px;background:#EFF7F2;color:#153A70;font-weight:650}}
        .chem-lit-risks{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:10px}}.chem-lit-risks>div{{padding:10px;border-radius:7px;background:#F8FAF9}}
        .chem-lit-risks p{{margin:5px 0 0;color:#40536A;font-size:.84rem}}.chem-lit-status{{display:inline-block;padding:5px 8px;border-radius:6px;background:{'#EAF2FF' if direct else '#FFF4DE'};color:{'#1756A3' if direct else '#875A10'};font-size:.82rem;font-weight:700}}
        @media(max-width:700px){{.chem-lit-risks{{grid-template-columns:1fr}}}}
        </style><section class='chem-lit-panel'><h3>{html.escape(title)} · {html.escape(mechanism_name)}</h3>
        <p>{html.escape('Screened formula' if english else 'Fórmula triada')}: <b>{html.escape(formula)}</b></p>{composition}
        <p>{html.escape(evidence_text)}</p><h4>{html.escape('Reported pathway (reference system)' if english else 'Rota reportada (sistema de referência)')}</h4>
        <div class='chem-lit-flow'>{pathway}</div><p>{html.escape(finding)}</p>
        <h4>{html.escape('Composition-aware checks' if english else 'Verificações considerando a composição')}</h4><div class='chem-lit-risks'>{risks}</div>
        <p><b>{html.escape('Evidence status' if english else 'Status da evidência')}:</b> <span class='chem-lit-status'>{html.escape(status)}</span></p>
        <p><a href='{context['doi']}' target='_blank' rel='noreferrer'>{html.escape(source_label)}: {html.escape(context['citation'])} · DOI</a></p></section>""",
        unsafe_allow_html=True,
    )
