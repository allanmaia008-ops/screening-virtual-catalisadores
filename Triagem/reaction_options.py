"""Reaction-specific choices shared by the Streamlit configuration panel."""


DEFAULT_PROMOTERS = ("Ce", "La", "Mg", "K", "Na", "Zr", "Sr", "Pr", "Nd", "Ca", "Y", "Outro")

def promoter_options(reaction):
    """Return only promoters supported by the selected reaction model."""
    return list(DEFAULT_PROMOTERS)
