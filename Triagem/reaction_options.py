"""Reaction-specific choices shared by the Streamlit configuration panel."""


DEFAULT_PROMOTERS = ("Ce", "La", "Mg", "K", "Na", "Zr", "Sr", "Pr", "Nd", "Ca", "Y", "Outro")

# Keep this list aligned with ltft.PROMOTERS and the approved FT scientific scope.
LTFT_PROMOTERS = ("K", "Na", "Mn", "Cu", "Ru", "Re", "La", "Ce", "Zr")


def promoter_options(reaction):
    """Return only promoters supported by the selected reaction model."""
    if reaction == "fischer_tropsch":
        return list(LTFT_PROMOTERS)
    return list(DEFAULT_PROMOTERS)
