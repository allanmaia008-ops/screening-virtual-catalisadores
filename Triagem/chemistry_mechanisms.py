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


def _property_based_hypotheses(reaction: str, active_metals: list[str], promoter: str,
                               support: str, support_properties: dict | None = None,
                               english: bool = False,
                               support_property_profiles: list[dict] | None = None) -> dict:
    """Build cautious mechanistic hypotheses from curated roles and support proxies.

    The support scores passed by the app are internal normalized heuristics, not
    measured material properties. They can prioritize a hypothesis for testing,
    but never upgrade it to a composition-matched literature mechanism.
    """
    selected = {_norm(metal) for metal in active_metals if _norm(metal)}
    profiles = list(support_property_profiles or [])
    if not profiles and support_properties:
        profiles = [{"suporte": support, **support_properties}]

    def profile_signal(profile: dict) -> str:
        basicity = max(float(profile.get("basicidade", 0) or 0), float(profile.get("afinidade_co2", 0) or 0))
        redox_score = max(float(profile.get("redox", 0) or 0), float(profile.get("vacancia_oxigenio", 0) or 0))
        if basicity >= redox_score + 0.08:
            return "basic"
        if redox_score >= basicity + 0.08:
            return "redox"
        return "mixed"

    support_options = _support_options(support)
    profile_signals = [(str(profile.get("suporte", support)), profile_signal(profile)) for profile in profiles]
    property_signal = (profile_signals[0][1] if len(profile_signals) == 1 else
                       "alternatives" if len(profile_signals) > 1 else None)

    if reaction == "reforma":
        if "ni" in selected:
            metal_role = (
                "Ni tem papel bem documentado na ativação/decomposição de CH₄ em sistemas de reforma seca à base de Ni; isso não determina sozinho a etapa limitante nem o destino de C* nesta composição.",
                "Ni has a well-documented role in CH₄ activation/decomposition in Ni-based dry-reforming systems; this alone does not determine the rate-limiting step or the fate of C* in this composition.")
        elif selected == {"co"}:
            metal_role = (
                "As referências curadas aqui não estabelecem a rota de ativação de CH₄ para Co monometálico nesta composição. A analogia Ni–Co não prova o comportamento de Co isolado.",
                "The references curated here do not establish the CH₄-activation pathway for monometallic Co in this composition. The Ni–Co analogy does not prove the behavior of isolated Co.")
        elif "pt" in selected:
            metal_role = (
                "Pt participa da ativação de CH₄ no sistema Pt/ZrO₂ estudado; fora desse par metal–suporte, a atribuição exige evidência correspondente.",
                "Pt participates in CH₄ activation in the studied Pt/ZrO₂ system; outside that metal–support pair, the assignment requires matching evidence.")
        else:
            metal_role = (
                "As referências curadas não atribuem uma etapa elementar de ativação de CH₄ ao(s) metal(is) selecionado(s) nesta composição.",
                "The curated references do not assign an elementary CH₄-activation step to the selected metal(s) in this composition.")
    elif reaction == "metanacao":
        if selected.intersection({"ni", "ru", "rh"}):
            metal_role = (
                "Ni, Ru e Rh têm evidência de participação em ativação de H₂/hidrogenação nos sistemas específicos citados; o metal sozinho não define se CO₂ segue via formiato, CO ou outra rota.",
                "Ni, Ru, and Rh have evidence of H₂ activation/hydrogenation in the specific cited systems; the metal alone does not determine whether CO₂ follows a formate, CO, or other pathway.")
        else:
            metal_role = (
                "As referências curadas não estabelecem a função elementar do(s) metal(is) selecionado(s) nesta composição de metanação.",
                "The curated references do not establish the elementary role of the selected metal(s) in this methanation composition.")
    else:  # RWGS
        if "au" in selected:
            metal_role = (
                "A rota associativa Au/CeO₂ é sustentada para o sistema citado; para outro suporte ou promotor, a contribuição do metal precisa ser reavaliada.",
                "The associative Au/CeO₂ pathway is supported for the cited system; with another support or promoter, the metal contribution must be reassessed.")
        else:
            metal_role = (
                "As referências curadas não estabelecem uma etapa elementar para o(s) metal(is) selecionado(s) nesta composição RWGS.",
                "The curated references do not establish an elementary step for the selected metal(s) in this RWGS composition.")

    if len(profile_signals) > 1:
        support_descriptions = []
        for name, signal in profile_signals:
            if signal == "basic":
                description = ("basicity/CO₂-affinity proxy: test carbonate species at the surface/interface" if english else
                               "proxy básico/afinidade por CO₂: testar carbonatos na superfície/interface")
            elif signal == "redox":
                description = ("redox/vacancy proxy: test CO₂ activation and oxygen transfer" if english else
                               "proxy redox/vacâncias: testar ativação de CO₂ e transferência de O")
            else:
                description = ("proxies básicos e redox próximos: testar possível cooperação bifuncional" if not english else
                               "similar basic and redox proxies: test possible bifunctional cooperation")
            support_descriptions.append(f"{name}: {description}")
        support_role = (
            "Alternativas — hipóteses distintas, não uma mistura: " + "; ".join(support_descriptions) + ". São tendências de proxies internos, não propriedades medidas nem mecanismos demonstrados.",
            "Alternatives — distinct hypotheses, not a mixture: " + "; ".join(support_descriptions) + ". These are internal-proxy trends, not measured properties or demonstrated mechanisms.")
    elif property_signal == "basic":
        support_role = (
            f"Os proxies internos de basicidade/afinidade por CO₂ são relativamente maiores para {support}; isso sugere testar adsorção de CO₂ como carbonato e reação na interface, mas não demonstra essas espécies.",
            f"The internal basicity/CO₂-affinity proxies are relatively higher for {support}; this suggests testing carbonate-like CO₂ adsorption and interfacial reaction, but does not demonstrate those species.")
    elif property_signal == "redox":
        support_role = (
            f"Os proxies internos redox/vacâncias são relativamente maiores para {support}; isso sugere testar ativação de CO₂ e transferência de oxigênio na interface, mas não comprova vacâncias operantes nem mobilidade de oxigênio.",
            f"The internal redox/oxygen-vacancy proxies are relatively higher for {support}; this suggests testing CO₂ activation and interfacial oxygen transfer, but does not prove operando vacancies or oxygen mobility.")
    elif property_signal == "mixed":
        support_role = (
            f"Os proxies internos de {support} indicam sinais próximos de basicidade/afinidade por CO₂ e redox/vacâncias; uma rota bifuncional é hipótese, não conclusão sobre a superfície real.",
            f"The internal proxies for {support} show similar basicity/CO₂-affinity and redox/vacancy signals; a bifunctional route is a hypothesis, not a conclusion about the real surface.")
    else:
        support_role = (
            "Não há um perfil de propriedades individualizado para este suporte na biblioteca heurística; não é possível usá-lo para favorecer uma etapa de adsorção ou transferência de oxigênio.",
            "No individual property profile is available for this support in the heuristic library; it cannot be used to favor an adsorption or oxygen-transfer step.")

    promoter_norm = _norm(promoter)
    if promoter_norm in {"la", "k", "na", "mg", "ca", "sr"} and reaction == "reforma":
        promoter_role = (
            f"{promoter} pode modificar basicidade e adsorção de CO₂ se estiver em espécie óxida apropriada; há analogias para La₂O₃ e promotores alcalinos/alcalino-terrosos em sistemas Ni de reforma seca. O elemento selecionado não informa fase, teor ou dispersão do promotor.",
            f"{promoter} may modify basicity and CO₂ adsorption if present in a suitable oxide species; analogies exist for La₂O₃ and alkali/alkaline-earth promoters in Ni dry-reforming systems. The selected element does not specify promoter phase, loading, or dispersion.")
    elif promoter_norm == "ce" and reaction in {"reforma", "rwgs", "metanacao"}:
        promoter_role = (
            "Ce pode conferir função redox/armazenamento de oxigênio quando incorporado como fase óxida, mas o símbolo do promotor não prova estado de oxidação, vacâncias ou participação no ciclo.",
            "Ce may provide redox/oxygen-storage functionality when present as an oxide phase, but the promoter symbol does not prove oxidation state, vacancies, or participation in the cycle.")
    elif promoter:
        promoter_role = (
            f"Não há regra mecanística curada para atribuir ao promotor {promoter} uma etapa específica nesta reação. Sua função depende da espécie química, teor, localização e interação com metal/suporte.",
            f"No curated mechanistic rule assigns promoter {promoter} a specific step in this reaction. Its function depends on chemical species, loading, location, and interaction with the metal/support.")
    else:
        promoter_role = (
            "Sem promotor selecionado; a hipótese considera somente os metais ativos e o suporte.",
            "No promoter selected; the hypothesis considers only the active metals and support.")

    if reaction == "reforma":
        if "ni" in selected:
            methane_step = "CH₄ → CHₓ*/C* nos sítios metálicos (papel compatível com Ni; específico da fase ativa)."
        elif selected == {"pt"} and _norm(support) == "zro2":
            methane_step = "CH₄ → CHₓ* + H* em Pt (evidência específica de Pt/ZrO₂)."
        else:
            methane_step = "CH₄ → intermediários superficiais: etapa não atribuída para o metal selecionado."
        if property_signal == "alternatives":
            co2_scenarios = []
            for name, signal in profile_signals:
                role = ("CO₂ → carbonato/O* adsorvidos (hipótese de suporte mais básico)" if signal == "basic" else
                        "CO₂ → espécie ativada/vacância e possível transferência de O* (hipótese de suporte mais redox)" if signal == "redox" else
                        "CO₂ → adsorção em sítios básicos/redox; rota dominante em aberto")
                if english:
                    role = ("CO₂ → adsorbed carbonate/O* (basic-support hypothesis)" if signal == "basic" else
                            "CO₂ → vacancy-activated species and possible O* transfer (redox-support hypothesis)" if signal == "redox" else
                            "CO₂ → adsorption at basic/redox sites; dominant route unresolved")
                co2_scenarios.append(f"{name}: {role}")
            co2_step = ("Cenários por suporte: " if not english else "Support-specific scenarios: ") + "; ".join(co2_scenarios) + (". Selecione/confirme o suporte antes de definir uma rota." if not english else ". Select/confirm the support before assigning a pathway.")
        elif property_signal == "basic":
            co2_step = "CO₂ → espécies carbonato/oxigênio adsorvidas no suporte/interface (hipótese baseada nos proxies de basicidade/afinidade)."
        elif property_signal == "redox":
            co2_step = "CO₂ → espécies ativadas em vacâncias/interface, com possível transferência de O* (hipótese baseada nos proxies redox)."
        elif property_signal == "mixed":
            co2_step = "CO₂ → adsorção em sítios básicos e/ou redox; a rota dominante permanece em aberto."
        else:
            co2_step = "Ativação de CO₂ e remoção de C*: indeterminadas para as propriedades disponíveis."
        pathway = f"{methane_step} {co2_step} A etapa interfacial e a formação de CO precisam ser verificadas experimentalmente."
    elif reaction == "metanacao":
        if property_signal == "basic":
            support_path = "O proxy do suporte favorece testar adsorção de CO₂ como carbonato antes de formiato/CO; essa sequência não foi estabelecida para a composição atual."
        elif property_signal == "redox":
            support_path = "O proxy redox sugere testar ativação de CO₂ em vacâncias e intermediários formiato/CO; participação do suporte ainda não está demonstrada."
        elif property_signal in {"mixed", "alternatives"}:
            support_path = "Os suportes mostram cenários diferentes ou sinais mistos para ativação de CO₂; a rota precisa ser determinada para o suporte efetivamente preparado."
        else:
            support_path = "Os dados de suporte disponíveis não distinguem adsorção de CO₂ no metal ou no suporte."
        pathway = ("H₂ → H* e hidrogenação nos sítios metálicos (hipótese dependente do metal selecionado). "
                   f"{support_path} Não assumir formiato ou CO como intermediário sem evidência operando.")
    else:
        if property_signal == "basic":
            support_path = "O proxy básico sugere testar adsorção de CO₂ em carbonatos no suporte/interface."
        elif property_signal == "redox":
            support_path = "O proxy redox sugere testar ativação de CO₂ em vacâncias e transferência de oxigênio."
        elif property_signal in {"mixed", "alternatives"}:
            support_path = "Os proxies indicam cenários mistos/alternativos para ativação de CO₂; não há uma rota única atribuída."
        else:
            support_path = "Os descritores de suporte disponíveis não distinguem rota associativa ou redox."
        pathway = ("A ativação de H₂ no metal e a formação de CO* são hipóteses a confirmar. "
                   f"{support_path} A sequência até CO + H₂O depende da interface e das condições.")
    if english:
        # Pathway copy is authored below in English to avoid mixing translations.
        if reaction == "reforma":
            if "ni" in selected:
                methane_step = "CH₄ → CHₓ*/C* on metal sites (consistent with Ni; active-phase dependent)."
            elif selected == {"pt"} and _norm(support) == "zro2":
                methane_step = "CH₄ → CHₓ* + H* on Pt (specific evidence for Pt/ZrO₂)."
            else:
                methane_step = "CH₄ → surface intermediates: step not assigned for the selected metal."
            if property_signal == "basic":
                co2_step = "CO₂ → carbonate/adsorbed oxygen species on support/interface (hypothesis from basicity/affinity proxies)."
            elif property_signal == "redox":
                co2_step = "CO₂ → species activated at vacancies/interface, with possible O* transfer (hypothesis from redox proxies)."
            elif property_signal == "mixed":
                co2_step = "CO₂ → adsorption at basic and/or redox sites; the dominant route remains unresolved."
            else:
                co2_step = "CO₂ activation and C* removal: undetermined from available property data."
            pathway = f"{methane_step} {co2_step} Interfacial steps and CO formation require experimental verification."
        elif reaction == "metanacao":
            if property_signal == "basic":
                support_path = "The support proxy suggests testing carbonate-like CO₂ adsorption before formate/CO; this sequence has not been established for the current composition."
            elif property_signal == "redox":
                support_path = "The redox proxy suggests testing CO₂ activation at vacancies and formate/CO intermediates; support participation remains unproven."
            elif property_signal in {"mixed", "alternatives"}:
                support_path = "The supports indicate mixed or distinct CO₂-activation scenarios; the pathway must be determined for the support actually prepared."
            else:
                support_path = "Available support data do not distinguish CO₂ adsorption on the metal or support."
            pathway = ("H₂ → H* and hydrogenation on metal sites (a hypothesis dependent on the selected metal). "
                       f"{support_path} Do not assume formate or CO intermediates without operando evidence.")
        else:
            if property_signal == "basic":
                support_path = "The basicity proxy suggests testing carbonate-like CO₂ adsorption on the support/interface."
            elif property_signal == "redox":
                support_path = "The redox proxy suggests testing CO₂ activation at vacancies and oxygen transfer."
            elif property_signal in {"mixed", "alternatives"}:
                support_path = "The proxies indicate mixed/alternative CO₂-activation scenarios; no single pathway is assigned."
            else:
                support_path = "Available support descriptors do not distinguish associative or redox pathways."
            pathway = ("H₂ activation on metal and CO* formation are hypotheses to verify. "
                       f"{support_path} The sequence to CO + H₂O depends on the interface and conditions.")

    return {
        "cards": [
            (("Metal ativo", "Active metal"), metal_role[1 if english else 0]),
            (("Suporte · propriedades internas", "Support · internal properties"), support_role[1 if english else 0]),
            (("Promotor", "Promoter"), promoter_role[1 if english else 0]),
        ],
        "pathway": pathway,
        "property_signal": property_signal,
    }


def mechanism_context(reaction: str, active_metals: list[str], promoter: str, support: str,
                      english: bool = False, support_properties: dict | None = None,
                      support_property_profiles: list[dict] | None = None) -> dict | None:
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
    literature_notes = []

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

    # The user-provided Ni/Ru review reports reducible-oxide supports for Ru.
    # A separate operando/DFT study supports a composition-matched Ru/CeO2
    # pathway; do not transfer that pathway to other listed supports.
    if reaction == "metanacao" and selected == {"ru"}:
        literature_notes.append({
            "title": ("Supports reported for Ru methanation" if english else "Suportes reportados para metanação com Ru"),
            "text": (("The review reports Ru catalysts on CeO₂, ZrO₂, TiO₂, and In₂O₃. These are literature examples, not equivalent supports or a performance ranking; the detailed pathway below is specific to Ru/CeO₂." if english else
                     "A revisão relata catalisadores de Ru suportados em CeO₂, ZrO₂, TiO₂ e In₂O₃. São exemplos da literatura, não suportes equivalentes nem uma classificação de desempenho; a rota detalhada abaixo é específica de Ru/CeO₂.")),
            "citation": "Usman et al. (2025), Catalysts 15, 203 (review)",
            "doi": "https://doi.org/10.3390/catal15030203",
        })
        if len(support_options) == 1 and _norm(support_options[0]) == "ceo2" and not promoter:
            metals_match = support_match = promoter_match = True
            context.update({
                "direct_match": True, "metals_match": True, "support_match": True, "promoter_match": True,
                "support": "ceo2",
                "steps": ["CO₂ dissociado em Ru / carbonatos-carboxilatos em CeO₂", "Ru–CO* e formiato na interface", "hidrogenação de intermediários C–O", "CH₄"],
                "steps_en": ["CO₂ dissociated on Ru / carbonates-carboxylates on CeO₂", "Interfacial Ru–CO* and formate", "Hydrogenation of C–O intermediates", "CH₄"],
                "finding": "Em Ru/CeO₂, DRIFTS, NAP-XPS e DFT indicaram ativação de CO₂ tanto em Ru quanto em CeO₂: CO₂ pode formar Ru–CO*, carbonatos e carboxilatos; espécies formiato/carboxilato participam da química interfacial. A hidrogenação de Ru–CO* foi indicada como etapa determinante da velocidade no sistema estudado. Não extrapolar para outros suportes ou condições.",
                "finding_en": "For Ru/CeO₂, DRIFTS, NAP-XPS, and DFT indicated CO₂ activation on both Ru and CeO₂: CO₂ can form Ru–CO*, carbonates, and carboxylates; formate/carboxylate species participate in interfacial chemistry. Hydrogenation of Ru–CO* was identified as rate-determining in that system. Do not extrapolate to other supports or conditions.",
                "citation": "Rogatis et al. (2022), J. Phys. Chem. C",
                "doi": "https://doi.org/10.1021/acs.jpcc.1c07537",
            })

    # Schmal's Chapter 8 discusses the bifunctional Pt/ZrO2 pathway for DRM;
    # the composition-matched primary study is Bitter et al. (1998).
    if reaction == "reforma" and selected == {"pt"} and len(support_options) == 1 and _norm(support_options[0]) == "zro2" and not promoter:
        metals_match = support_match = promoter_match = True
        context.update({
            "direct_match": True, "metals_match": True, "support_match": True, "promoter_match": True,
            "steps": ["CH₄ dissociado em Pt → CHₓ* / H*", "CO₂ adsorvido como carbonato próximo à interface Pt–ZrO₂", "C* + carbonato → formiato* + CO", "formiato* → CO + OH*; OH* → H₂O"],
            "steps_en": ["CH₄ dissociated on Pt → CHₓ* / H*", "CO₂ adsorbed as carbonate near the Pt–ZrO₂ perimeter", "C* + carbonate → formate* + CO", "Formate* → CO + OH*; OH* → H₂O"],
            "finding": "Em Pt/ZrO₂, a atividade foi relacionada à quantidade de perímetro Pt–ZrO₂ disponível. O estudo propôs ativação de CH₄ no Pt e formação de carbonato no suporte próximo à interface; carbono superficial reduz o carbonato a formiato e CO. É uma rota reportada para Pt/ZrO₂, não para Pt em qualquer suporte.",
            "finding_en": "For Pt/ZrO₂, activity was related to the available Pt–ZrO₂ perimeter. The study proposed CH₄ activation on Pt and carbonate formation on the nearby support; surface carbon reduces carbonate to formate and CO. This pathway was reported for Pt/ZrO₂, not for Pt on any support.",
            "citation": "Bitter et al. (1998), Journal of Catalysis 176, 93–101",
            "doi": "https://doi.org/10.1006/jcat.1998.2022",
        })

    # Closest mechanistic analogy for the user's Co–La dry-reforming example:
    # the primary study contains Ni–Co alloy and La2O3 support, not Co–La alone.
    if reaction == "reforma" and ("co" in selected or _norm(promoter) == "la"):
        literature_notes.append({
            "title": ("Literature analogy: Ni–Co/La₂O₃ (not the selected composition)" if english else "Analogia da literatura: Ni–Co/La₂O₃ (não é a composição selecionada)"),
            "text": (("Under dry reforming, an in-situ XRD study found that Co addition to Ni/La₂O₃ increased La₂O₂CO₃ formation; the oxycarbonate accelerated removal of carbonaceous deposits next to the active particles. The studied active phase was Ni–Co and La₂O₃ was the support. This is not evidence that monometallic Co with La promoter on MgAlOx, La₂O₃–Al₂O₃, or MgAl₂O₄ behaves the same way." if english else
                     "Na reforma seca, um estudo por DRX in situ observou que adicionar Co a Ni/La₂O₃ aumentou a formação de La₂O₂CO₃; o oxicarbonato acelerou a remoção de depósitos carbonáceos próximos às partículas ativas. A fase ativa estudada era Ni–Co e La₂O₃ era o suporte. Isso não comprova o mesmo comportamento para Co monometálico com La promotor em MgAlOx, La₂O₃–Al₂O₃ ou MgAl₂O₄.")),
            "citation": "Tsoukalou et al. (2016), Journal of Catalysis 343, 208–214",
            "doi": "https://doi.org/10.1016/j.jcat.2016.03.018",
        })

    if reaction == "reforma" and support_properties and (
        max(float(support_properties.get("basicidade", 0) or 0), float(support_properties.get("afinidade_co2", 0) or 0))
        >= max(float(support_properties.get("redox", 0) or 0), float(support_properties.get("vacancia_oxigenio", 0) or 0)) + 0.08
    ):
        literature_notes.append({
            "title": ("Property analogy: basic sites and CO₂ adsorption" if english else "Analogia de propriedades: sítios básicos e adsorção de CO₂"),
            "text": (("A DRM review describes basic oxygen sites and carbonate-like CO₂ adsorption as a proposed route to react with carbon formed from CH₄. A separate Ni/La₂O₃ study links promoter oxides to changes in basicity. These are reaction-family analogies; the selected support proxy is not a measured surface property and does not establish this pathway for the current catalyst." if english else
                     "Uma revisão de DRM descreve sítios básicos de oxigênio e adsorção de CO₂ como espécies carbonato em uma rota proposta para reagir com o carbono formado a partir de CH₄. Um estudo de Ni/La₂O₃ também relaciona óxidos promotores a mudanças de basicidade. São analogias da família de reação; o proxy do suporte selecionado não é medida da superfície e não estabelece essa rota para o catalisador atual.")),
            "citation": "Khan et al. (2020), Catalysis Science & Technology; DOI: 10.1039/C9CY01519A",
            "doi": "https://doi.org/10.1039/C9CY01519A",
        })

    if reaction == "reforma" and _norm(promoter) in {"la", "k", "na", "mg", "ca", "sr"}:
        literature_notes.append({
            "title": ("Promoter-property analogy: basicity and CO₂ uptake" if english else "Analogia de propriedades do promotor: basicidade e adsorção de CO₂"),
            "text": (("A DRM review discusses La₂O₃ and alkali/alkaline-earth oxide promoters as modifiers of surface basicity and CO₂ adsorption in selected Ni catalysts. This supports a testable hypothesis only: the selected element does not specify its oxide phase, amount, distribution, or effect in the present catalyst." if english else
                     "Uma revisão sobre reforma seca discute promotores óxidos de La e de metais alcalinos/alcalino-terrosos como modificadores da basicidade superficial e adsorção de CO₂ em certos catalisadores de Ni. Isso sustenta apenas uma hipótese testável: o elemento selecionado não informa fase óxida, teor, distribuição nem efeito no catalisador atual.")),
            "citation": "Understanding the role of surface basic sites... (2020), Catalysis Science & Technology",
            "doi": "https://doi.org/10.1039/C9CY01519A",
        })
    context["literature_notes"] = literature_notes

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
            "ru": ("Em Ru/CeO₂, o estudo citado observou ativação de CO₂ em Ru e no suporte. Isso não define o mecanismo de Ru em ZrO₂, TiO₂ ou In₂O₃.", "On Ru/CeO₂, the cited study observed CO₂ activation on Ru and the support. This does not establish the mechanism of Ru on ZrO₂, TiO₂, or In₂O₃."),
        },
        "rwgs": {
            "au": ("Au/CeO₂ é o sistema de referência: dados operando/transientes sustentam ali uma rota associativa via carbonato/formiato; não extrapolar automaticamente a outro suporte.", "Au/CeO₂ is the reference system: operando/transient data support an associative carbonate/formate route there; do not automatically extrapolate to another support."),
        },
    }
    unknown_role = ("Este metal foi selecionado, mas a referência exibida não estabelece sua contribuição mecanística nesta composição.", "This metal is selected, but the displayed reference does not establish its mechanistic contribution in this composition.")
    metal_readings = [(str(metal), roles.get(reaction, {}).get(_norm(metal), unknown_role)[1 if english else 0]) for metal in active_metals]
    if reaction == "reforma" and selected == {"pt"} and support_match and _norm(support) == "zro2" and not promoter:
        metal_readings = [(str(metal),
                           "No Pt/ZrO₂, CH₄ se dissocia em Pt e as espécies resultantes reagem com espécies derivadas de CO₂ na interface Pt–ZrO₂." if not english else
                           "On Pt/ZrO₂, CH₄ dissociates on Pt and the resulting species react with CO₂-derived species at the Pt–ZrO₂ interface.")
                          for metal in active_metals]

    if len(support_options) > 1 and reaction == "metanacao" and selected == {"ru"}:
        support_reading = (
            (f"Estas são alternativas de suporte, não uma composição única: {', '.join(support_options)}. A revisão relata exemplos com Ru, mas a evidência mecanística precisa ser ligada a um suporte e a condições específicos.",
             f"These are alternative supports, not one composition: {', '.join(support_options)}. The review reports Ru examples, but mechanistic evidence must be tied to one support and specific conditions."))
    elif len(support_options) > 1:
        support_reading = (
            (f"Estas são alternativas de suporte, não uma composição única: {', '.join(support_options)}. Escolha uma opção antes de comparar com a referência ({mechanism['support']}).",
             f"These are alternative supports, not one composition: {', '.join(support_options)}. Select one option before comparing with the reference ({mechanism['support']}).")
        )
    elif reaction == "metanacao" and selected == {"ru"} and not support_match and _norm(support) in {"ceo2", "zro2", "tio2", "in2o3"}:
        support_reading = (
            (f"{support} é um suporte reportado para Ru na revisão citada. Isso não transfere automaticamente uma rota mecanística: a evidência direta detalhada deste painel é para Ru/CeO₂.",
             f"{support} is reported as a Ru support in the cited review. This does not automatically transfer a mechanism: the detailed composition-matched evidence in this panel is for Ru/CeO₂."))
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
    context["property_hypotheses"] = _property_based_hypotheses(
        reaction, active_metals, promoter, support, support_properties, english=english,
        support_property_profiles=support_property_profiles)
    return context


def render_mechanism_panel(st, reaction: str, formula: str, active_metals: list[str], promoter: str,
                           support: str, english: bool = False,
                           support_properties: dict | None = None,
                           support_property_profiles: list[dict] | None = None) -> None:
    """Render one literature pathway and composition-aware evidence checks."""
    context = mechanism_context(reaction, active_metals, promoter, support, english=english,
                                support_properties=support_properties,
                                support_property_profiles=support_property_profiles)
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
    property_hypotheses = context["property_hypotheses"]
    property_cards = "".join(
        f"<div><b>{html.escape(labels[1 if english else 0])}</b><p>{html.escape(text)}</p></div>"
        for labels, text in property_hypotheses["cards"]
    )
    hypothesis_heading = ("Property-based mechanistic hypothesis · not a confirmed pathway" if english
                         else "Hipótese mecanística baseada nas propriedades · não é rota confirmada")
    hypothesis_intro = (
        "This qualitative reading combines curated reaction-specific roles with the platform's normalized support heuristics. Those heuristics are not measured properties, and this section does not calculate a microkinetic mechanism." if english else
        "Esta leitura qualitativa combina papéis reacionais da literatura com heurísticas normalizadas do suporte na plataforma. Essas heurísticas não são propriedades medidas, e esta seção não calcula um mecanismo microcinético."
    )
    hypothesis_path_label = "Sequence to test" if english else "Sequência a investigar"
    hypothesis_html = (
        f"<h4>{html.escape(hypothesis_heading)}</h4><p class='chem-lit-note'>{html.escape(hypothesis_intro)}</p>"
        f"<div class='chem-lit-risks'>{property_cards}</div>"
        f"<div class='chem-lit-hypothesis'><b>{html.escape(hypothesis_path_label)}</b><p>{html.escape(property_hypotheses['pathway'])}</p></div>"
        f"<p class='chem-lit-note'>{html.escape('Referencial conceitual: Schmal (2011), cap. 8, pp. 331–344; as rotas específicas devem ser conferidas nas referências primárias.' if not english else 'Conceptual framework: Schmal (2011), ch. 8, pp. 331–344; system-specific pathways should be checked against primary studies.')}</p>"
    )
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
    literature_notes_html = ""
    if context.get("literature_notes"):
        notes_heading = "Comparative literature evidence (not automatically transferable)" if english else "Evidências comparativas da literatura (não transferíveis automaticamente)"
        notes_cards = "".join(
            f"<div><b>{html.escape(note['title'])}</b><p>{html.escape(note['text'])}</p>"
            f"<a href='{note['doi']}' target='_blank' rel='noreferrer'>{html.escape(source_label)}: {html.escape(note['citation'])} · DOI</a></div>"
            for note in context["literature_notes"]
        )
        literature_notes_html = f"<h4>{html.escape(notes_heading)}</h4><div class='chem-lit-literature'>{notes_cards}</div>"
    panel_html = f"""<style>
        .chem-lit-panel{{margin:18px 0;padding:16px;border:1px solid #D7E3DD;border-radius:10px;background:#fff;color:#14213D}}
        .chem-lit-panel h3{{margin:0 0 10px;color:#153A70;font-size:.96rem;line-height:1.25;font-weight:850;overflow-wrap:anywhere}}.chem-lit-composition{{padding:10px;border:1px solid #E3EAE6;border-radius:7px;line-height:1.8}}
        .chem-lit-flow{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:12px 0}}.chem-lit-step{{padding:8px 10px;border-radius:7px;background:#EFF7F2;color:#153A70;font-weight:650}}
        .chem-lit-risks{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:10px}}.chem-lit-risks>div{{padding:10px;border-radius:7px;background:#F8FAF9}}
        .chem-lit-literature{{display:grid;grid-template-columns:1fr;gap:9px;margin:10px 0}}.chem-lit-literature>div{{padding:12px;border:1px solid #E3EAE6;border-radius:7px;background:#F8FAF9}}.chem-lit-literature a{{font-size:.82rem}}
        .chem-lit-hypothesis{{margin-top:10px;padding:12px;border-left:3px solid #4A78B7;border-radius:6px;background:#F2F6FC}}.chem-lit-hypothesis p,.chem-lit-note{{margin:6px 0 0;color:#40536A;font-size:.82rem;line-height:1.5}}
        .chem-lit-risks p{{margin:5px 0 0;color:#40536A;font-size:.84rem}}.chem-lit-status{{display:inline-block;padding:5px 8px;border-radius:6px;background:{'#EAF2FF' if direct else '#FFF4DE'};color:{'#1756A3' if direct else '#875A10'};font-size:.82rem;font-weight:700}}
        .chem-lit-notice{{padding:10px;border-left:3px solid #D89B28;background:#FFF8E8;border-radius:5px;color:#604716}}
        @media(max-width:700px){{.chem-lit-risks{{grid-template-columns:1fr}}}}
        </style><section class='chem-lit-panel'><h3>{html.escape(title)} · {html.escape(mechanism_name)}</h3>
        <p>{html.escape('Screened formula' if english else 'Fórmula triada')}: <b>{html.escape(formula)}</b></p>{composition}
        <h4>{html.escape(components_heading)}</h4>{roles_html}
        {evidence_block}
        {hypothesis_html}
        {literature_notes_html}
        <h4>{html.escape('Composition-aware checks' if english else 'Verificações considerando a composição')}</h4><div class='chem-lit-risks'>{risks_html}</div>
        <p><b>{html.escape('Evidence status' if english else 'Status da evidência')}:</b> <span class='chem-lit-status'>{html.escape(status)}</span></p>
        </section>"""
    # st.html parses the markup directly; st.markdown may display literal tags
    # when the HTML is nested/combined with CSS in some Streamlit versions.
    if hasattr(st, "html"):
        st.html(panel_html)
    else:  # compatibility with older Streamlit releases
        st.markdown(panel_html, unsafe_allow_html=True)
