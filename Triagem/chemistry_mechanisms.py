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


def _support_options(support: str) -> list[str]:
    """Split a support recommendation into alternatives, not a fictitious mixture."""
    return [part.strip() for part in re.split(r"\s*,\s*|\s+ou\s+|\s+or\s+", str(support or ""), flags=re.IGNORECASE) if part.strip()]


def mechanism_context(reaction: str, active_metals: list[str], promoter: str, support: str,
                      english: bool = False) -> dict | None:
    """Build a reaction and composition-aware interpretation without scoring claims."""
    mechanism = MECHANISMS.get(reaction)
    if mechanism is None:
        return None
    selected = {_norm(metal) for metal in active_metals if _norm(metal)}
    metals_match = selected == mechanism["metals"]
    support_options = _support_options(support)
    # A list of suggested supports is not one material and cannot establish a
    # direct match to a single-support literature system.
    support_match = len(support_options) == 1 and _norm(support_options[0]) == mechanism["support"]
    promoter_match = _norm(promoter) == _norm(mechanism["promoter"] or "")
    context = {**mechanism, "direct_match": metals_match and support_match and promoter_match,
               "support_options": support_options,
               "metals_match": metals_match, "support_match": support_match, "promoter_match": promoter_match}

    # Methanation has distinct primary studies for Ni/Y2O3 and Ni- or Rh/CeO2;
    # select the matching pathway instead of always showing the Ni/Y2O3 route.
    if reaction == "metanacao" and len(support_options) == 1 and _norm(support_options[0]) == "ceo2" and selected in ({"ni"}, {"rh"}) and not promoter:
        metals_match = support_match = promoter_match = True
        context.update({
            "direct_match": True, "metals_match": True, "support_match": True, "promoter_match": True,
            "steps": ["CO₂ activation at CeO₂ vacancies", "formate* / CO* at metal–ceria interface", "H₂ activation on metal", "CH₄ (and CO pathway-dependent)"],
            "steps_en": ["CO₂ activation at CeO₂ vacancies", "Formate* / CO* at metal–ceria interface", "H₂ activation on metal", "CH₄ (with support-dependent CO pathway)"],
            "finding": "Estudos operando de Ni/CeO₂ e Rh/CeO₂ associaram Ce³⁺/vacâncias à ativação de CO₂ e observaram intermediários formiato. Em Rh/CeO₂, CO adsorvido foi hidrogenado mais prontamente; em Ni/CeO₂, a rota e seletividade dependeram da interação metal–suporte.",
            "finding_en": "Operando studies of Ni/CeO₂ and Rh/CeO₂ linked Ce³⁺/vacancies to CO₂ activation and observed formate intermediates. Adsorbed CO was hydrogenated more readily on Rh/CeO₂; the pathway and selectivity on Ni/CeO₂ depended on metal–support interaction.",
            "citation": "Structure–function study of Rh/Ni/CeO₂ (2019), Catal. Sci. Technol.",
            "doi": "https://doi.org/10.1039/C8CY02097C",
        })

    # Roles below are intentionally limited to statements supported by the
    # displayed reaction-specific literature; unknown metals stay explicitly unknown.
    roles = {
        "reforma": {
            "ni": ("Ni activates CH₄ and can form CHₓ*/C* intermediates; whether carbon is removed depends on oxygen supply and interface.", "Ni activates CH₄ and can form CHₓ*/C* intermediates; carbon removal depends on oxygen supply and the interface."),
            "pt": ("Em Pt–Ni/CeO₂, Pt foi associado à dissociação de CO₂ e à formação de O*; esse papel não está estabelecido para Pt isolado ou outro suporte.", "In Pt–Ni/CeO₂, Pt was associated with CO₂ dissociation and O* formation; this role is not established for Pt alone or another support."),
        },
        "metanacao": {
            "ni": ("Ni fornece sítios para ativação de H₂ e hidrogenação. A rota de CO₂ depende do suporte: formiato em Ni/Y₂O₃ e vias de formiato/CO dependentes da estrutura em céria.", "Ni provides sites for H₂ activation and hydrogenation. The CO₂ pathway depends on support: formate on Ni/Y₂O₃ and structure-dependent formate/CO routes on ceria."),
            "rh": ("Em Rh/CeO₂, CO adsorvido foi hidrogenado a CH₄ mais prontamente que em Ni/CeO₂ no estudo citado; a comparação é específica aos catalisadores estudados.", "On Rh/CeO₂, adsorbed CO was hydrogenated to CH₄ more readily than on Ni/CeO₂ in the cited study; this comparison is specific to those catalysts."),
        },
        "rwgs": {
            "au": ("Au/CeO₂ é o sistema de referência: dados operando/transientes sustentam ali uma rota associativa via carbonato/formiato; não extrapolar automaticamente a outro suporte.", "Au/CeO₂ is the reference system: operando/transient data support an associative carbonate/formate route there; do not automatically extrapolate to another support."),
        },
    }
    unknown_role = ("Este metal foi selecionado, mas a referência exibida não estabelece sua contribuição mecanística nesta composição.", "This metal is selected, but the displayed reference does not establish its mechanistic contribution in this composition.")
    metal_readings = [(str(metal), roles.get(reaction, {}).get(_norm(metal), unknown_role)[1 if english else 0]) for metal in active_metals]

    if len(support_options) > 1:
        support_reading = (
            (f"Estas são alternativas de suporte, não uma composição única: {', '.join(support_options)}. Escolha uma opção antes de comparar com a referência ({mechanism['support']}).",
             f"These are alternative supports, not one composition: {', '.join(support_options)}. Select one option before comparing with the reference ({mechanism['support']}).")
        )
    elif support_match:
        support_reading = ((f"{support} corresponde ao suporte da referência; a contribuição reportada vale para aquele sistema e suas condições."),
                           (f"{support} matches the reference support; the reported contribution applies to that system and its conditions."))
    elif _norm(support) in {"ceo2", "zro2", "tio2", "in2o3"}:
        support_reading = (f"{support} difere do suporte da referência ({mechanism['support']}); redutibilidade/vacâncias são propriedades a investigar, não evidência de mecanismo nesta composição.",
                           f"{support} differs from the reference support ({mechanism['support']}); reducibility/vacancies are properties to investigate, not mechanistic evidence for this composition.")
    else:
        support_reading = (f"{support or 'Não especificado'} difere do suporte da referência ({mechanism['support']}); não transferir rota ou estabilidade sem evidência compatível.",
                           f"{support or 'Not specified'} differs from the reference support ({mechanism['support']}); do not transfer its pathway or stability without matching evidence.")

    promoter_reading = (
        (f"{promoter} foi selecionado, mas não aparece na referência. Seu efeito sobre adsorção, cobertura de sítios, dispersão e estabilidade permanece indeterminado; compare com a mesma composição sem promotor.",
         f"{promoter} is selected but absent from the reference. Its effect on adsorption, site coverage, dispersion, and stability remains undetermined; compare with the same composition without promoter.")
        if promoter else
        ("Sem promotor selecionado; a leitura não inclui efeito de promotor.", "No promoter selected; this interpretation includes no promoter effect."))

    metals_text = ", ".join(active_metals) if active_metals else ("Nenhum especificado" if not english else "None specified")
    support_text = ", ".join(support_options) if support_options else ("Não especificado" if not english else "Not specified")
    if reaction == "reforma":
        risk_reaction = (
            ("Como Ni foi selecionado, ativação de CH₄ pode gerar carbono; avaliar coque nas condições reais. A mitigação por O* citada depende da interface Pt–Ni/CeO₂." if "ni" in selected else "A composição selecionada não tem evidência citada de resistência ao coque; medir carbono depositado sob a razão CH₄/CO₂ e temperatura de operação."),
            ("Because Ni is selected, CH₄ activation can generate carbon; assess coke under actual conditions. The cited O*-assisted mitigation depends on the Pt–Ni/CeO₂ interface." if "ni" in selected else "No cited coke-resistance evidence is available for the selected composition; measure deposited carbon at the operating CH₄/CO₂ ratio and temperature."))
    elif reaction == "metanacao":
        risk_reaction = (
            ("Para a fase com Ni selecionada, verificar carbono e crescimento de partículas na temperatura e razão H₂/CO₂ escolhidas; nenhum dos dois é previsto pela fórmula." if "ni" in selected else "Para os metais selecionados, verificar depósitos de carbono e perda de atividade nas condições escolhidas; a composição não prediz esses efeitos."),
            ("For the selected Ni-containing phase, check carbon and particle growth at the chosen temperature and H₂/CO₂ ratio; neither is predicted by the formula." if "ni" in selected else "For the selected metals, check carbon deposits and activity loss under the chosen conditions; composition does not predict these effects."))
    else:
        risk_reaction = (
            ("Para os metais selecionados, verificar seletividade a CO e mudanças no estado de oxidação da fase ativa/suporte na temperatura e razão H₂/CO₂ reais."),
            ("For the selected metals, check CO selectivity and active-phase/support oxidation-state changes at the actual temperature and H₂/CO₂ ratio."))
    # The checklist is composition-specific in its wording but never assigns an
    # unmeasured probability or presents a missing datum as an observed failure.
    risks = [
        (("Sinterização", "Sintering"),
         (f"{metals_text}/{support_text} não informa tamanho de partícula, teor, ancoragem ou histórico térmico. Medir crescimento/aglomeração após ensaio; suporte diferente não herda a estabilidade da referência.",
          f"{metals_text}/{support_text} does not specify particle size, loading, anchoring, or thermal history. Measure growth/agglomeration after operation; a different support does not inherit the reference stability.")),
        (("Envenenamento", "Poisoning"),
         (f"A composição {metals_text}/{support_text} não informa impurezas da alimentação. Verificar S, Cl e contaminantes compatíveis com a fase metálica; comparar atividade e superfície antes/depois.",
          f"The {metals_text}/{support_text} composition says nothing about feed impurities. Check S, Cl, and contaminants relevant to the metal phase; compare activity and surface before/after.")),
        (("Baixa dispersão", "Poor dispersion"),
         (f"{metals_text} pode estar disperso, segregado ou em liga; promotor {promoter or 'ausente' if not english else promoter or 'absent'} e fórmula não distinguem esses estados. Verificar fases/tamanho por TEM-EDS/XRD e dispersão por quimissorção, quando aplicável.",
          f"{metals_text} may be dispersed, segregated, or alloyed; formula and promoter {promoter or ('absent' if english else 'none')} do not distinguish these states. Check phases/size by TEM-EDS/XRD and dispersion by chemisorption where applicable.")),
        (("Risco da reação", "Reaction-specific risk"), risk_reaction),
    ]
    context.update({"metal_readings": metal_readings,
                    "support_reading": support_reading[1 if english else 0],
                    "support_options": support_options,
                    "promoter_reading": promoter_reading[1 if english else 0],
                    "risks": [(labels[1 if english else 0], text_pair[1 if english else 0]) for labels, text_pair in risks]})
    return context


def render_mechanism_panel(st, reaction: str, formula: str, active_metals: list[str], promoter: str,
                           support: str, english: bool = False) -> None:
    """Render one literature pathway and composition-aware evidence checks."""
    context = mechanism_context(reaction, active_metals, promoter, support, english=english)
    if context is None:
        return

    direct = context["direct_match"]
    title = (("Literature mechanism for the selected reaction" if direct else "Mechanistic context for the selected reaction") if english
             else ("Mecanismo da literatura para a reação selecionada" if direct else "Contexto mecanístico da reação selecionada"))
    status = (("Direct match to the cited system" if direct else "Related reference; composition differs") if english
              else ("Correspondência direta com o sistema citado" if direct else "Referência relacionada; composição diferente"))
    metal_label, promoter_label, support_label = (("Active metals", "Promoter", "Suggested support") if english
                                                   else ("Metais ativos", "Promotor", "Suporte sugerido"))
    metal_readings = context["metal_readings"]
    support_reading = context["support_reading"]
    promoter_reading = context["promoter_reading"]
    risks = context["risks"]
    steps = context["steps_en"] if english else context["steps"]
    pathway = " → ".join(f"<span class='chem-lit-step'>{html.escape(step)}</span>" for step in steps)
    risks_html = "".join(f"<div><b>{html.escape(label)}</b><p>{html.escape(text)}</p></div>" for label, text in risks)
    composition = (f"<div class='chem-lit-composition'><b>{html.escape(metal_label)}:</b> {html.escape(', '.join(active_metals) or '—')}<br>"
                   f"<b>{html.escape(promoter_label)}:</b> {html.escape(promoter or ('None' if english else 'Nenhum'))}<br>"
                   f"<b>{html.escape(support_label)}:</b> {html.escape(support or '—')}</div>")
    components_heading = "How the selected composition is interpreted" if english else "Leitura dos componentes selecionados"
    metal_details = "".join(f"<div><b>{html.escape(metal)}</b><p>{html.escape(role)}</p></div>" for metal, role in metal_readings)
    roles_html = (f"<div class='chem-lit-risks'>{metal_details}<div><b>{html.escape(promoter_label)} {html.escape(promoter or ('(none)' if english else '(nenhum)'))}</b><p>{html.escape(promoter_reading)}</p></div>"
                  f"<div><b>{html.escape(support_label)} {html.escape(support or '—')}</b><p>{html.escape(support_reading)}</p></div></div>")
    finding = context["finding_en"] if english else context["finding"]
    source_label = "Source" if english else "Fonte"
    mechanism_name = context["label"][1 if english else 0]
    exact_evidence = context["direct_match"]
    no_match_notice = (
        "No composition-matched mechanism is available in the curated references. The literature pathway below is therefore not assigned to this candidate." if english
        else "Não há mecanismo correspondente à composição selecionada nas referências curadas. Portanto, uma rota da literatura não será atribuída a este candidato."
    )
    evidence_block = (
        f"<h4>{html.escape('Reported pathway (reference system)' if english else 'Rota reportada (sistema de referência)')}</h4><div class='chem-lit-flow'>{pathway}</div><p>{html.escape(finding)}</p>"
        f"<p><a href='{context['doi']}' target='_blank' rel='noreferrer'>{html.escape(source_label)}: {html.escape(context['citation'])} · DOI</a></p>"
        if exact_evidence else f"<p class='chem-lit-notice'>{html.escape(no_match_notice)}</p>"
    )
    panel_html = f"""<style>
        .chem-lit-panel{{margin:18px 0;padding:16px;border:1px solid #D7E3DD;border-radius:10px;background:#fff;color:#14213D}}
        .chem-lit-panel h3{{margin:0 0 10px;color:#153A70;font-size:.96rem;line-height:1.25;font-weight:850;overflow-wrap:anywhere}}.chem-lit-composition{{padding:10px;border:1px solid #E3EAE6;border-radius:7px;line-height:1.8}}
        .chem-lit-flow{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:12px 0}}.chem-lit-step{{padding:8px 10px;border-radius:7px;background:#EFF7F2;color:#153A70;font-weight:650}}
        .chem-lit-risks{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:10px}}.chem-lit-risks>div{{padding:10px;border-radius:7px;background:#F8FAF9}}
        .chem-lit-risks p{{margin:5px 0 0;color:#40536A;font-size:.84rem}}.chem-lit-status{{display:inline-block;padding:5px 8px;border-radius:6px;background:{'#EAF2FF' if direct else '#FFF4DE'};color:{'#1756A3' if direct else '#875A10'};font-size:.82rem;font-weight:700}}
        .chem-lit-notice{{padding:10px;border-left:3px solid #D89B28;background:#FFF8E8;border-radius:5px;color:#604716}}
        @media(max-width:700px){{.chem-lit-risks{{grid-template-columns:1fr}}}}
        </style><section class='chem-lit-panel'><h3>{html.escape(title)} · {html.escape(mechanism_name)}</h3>
        <p>{html.escape('Screened formula' if english else 'Fórmula triada')}: <b>{html.escape(formula)}</b></p>{composition}
        <h4>{html.escape(components_heading)}</h4>{roles_html}
        {evidence_block}
        <h4>{html.escape('Composition-aware checks' if english else 'Verificações considerando a composição')}</h4><div class='chem-lit-risks'>{risks_html}</div>
        <p><b>{html.escape('Evidence status' if english else 'Status da evidência')}:</b> <span class='chem-lit-status'>{html.escape(status)}</span></p>
        </section>"""
    # st.html parses the markup directly; st.markdown may display literal tags
    # when the HTML is nested/combined with CSS in some Streamlit versions.
    if hasattr(st, "html"):
        st.html(panel_html)
    else:  # compatibility with older Streamlit releases
        st.markdown(panel_html, unsafe_allow_html=True)
