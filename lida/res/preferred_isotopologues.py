import requests
from pyvalem.formula import Formula

from atomic_isotope_abundances import isotope_abundances


def get_preferred_isotopologues():
    exomol_all_raw = requests.get('https://www.exomol.com/db/exomol.all').text

    # TODO: utilize the exomol_all parsing script, rather than this hack:
    all_exomol_formulas = [
        row.split('#')[0].strip() for row in exomol_all_raw.split('\n') if
        row.strip().endswith('Molecule chemical formula')
    ]

    preferred_isotopologues = {}
    for formula in all_exomol_formulas:
        pvf = Formula(formula)
        iso_formula = ''
        if formula.startswith('cis-'):
            iso_formula += 'cis-'
        elif formula.startswith('trans-'):
            iso_formula += 'trans-'
        for atom, stoich in pvf.atom_stoich.items():
            iso_formula += isotope_abundances[atom][0][0]
            if stoich > 1:
                iso_formula += str(stoich)
        if pvf.charge:
            assert pvf.charge == 1
            iso_formula += '+'
        # validation of the name:
        Formula(iso_formula)
        preferred_isotopologues[formula] = iso_formula

    return preferred_isotopologues


# isotopologues = get_preferred_isotopologues()
# print(isotopologues)

isotopologues = {
    'H2O': '(1H)2(16O)', 'CO2': '(12C)(16O)2', 'CO': '(12C)(16O)', 'CH4': '(12C)(1H)4', 'NO': '(14N)(16O)',
    'SO2': '(32S)(16O)2', 'NH3': '(14N)(1H)3', 'HNO3': '(1H)(14N)(16O)3', 'OH': '(16O)(1H)', 'HF': '(1H)(19F)',
    'HCl': '(1H)(35Cl)', 'H2CO': '(1H)2(12C)(16O)', 'N2': '(14N)2', 'HCN': '(1H)(12C)(14N)',
    'CH3Cl': '(12C)(1H)3(35Cl)', 'H2O2': '(1H)2(16O)2', 'C2H2': '(12C)2(1H)2', 'PH3': '(31P)(1H)3', 'H2S': '(1H)2(32S)',
    'C2H4': '(12C)2(1H)4', 'CS': '(12C)(32S)', 'H2': '(1H)2', 'LiH': '(7Li)(1H)', 'LiH+': '(7Li)(1H)+',
    'FeH': '(56Fe)(1H)', 'TiH': '(48Ti)(1H)', 'BeH': '(9Be)(1H)', 'CaH': '(40Ca)(1H)', 'CrH': '(52Cr)(1H)',
    'SiH': '(28Si)(1H)', 'AlH': '(27Al)(1H)', 'NaH': '(23Na)(1H)', 'MgH': '(24Mg)(1H)', 'SiO': '(28Si)(16O)',
    'TiO': '(48Ti)(16O)', 'MgO': '(24Mg)(16O)', 'H3+': '(1H)3+', 'HeH+': '(4He)(1H)+', 'H2+': '(1H)2+', 'C2': '(12C)2',
    'CN': '(12C)(14N)', 'CH': '(12C)(1H)', 'LiCl': '(7Li)(35Cl)', 'NaCl': '(23Na)(35Cl)', 'NH': '(14N)(1H)',
    'SO3': '(32S)(16O)3', 'YO': '(89Y)(16O)', 'VO': '(51V)(16O)', 'SH': '(32S)(1H)', 'AlO': '(27Al)(16O)',
    'ScH': '(45Sc)(1H)', 'KCl': '(39K)(35Cl)', 'CaO': '(40Ca)(16O)', 'CP': '(12C)(31P)', 'PN': '(31P)(14N)',
    'PS': '(31P)(32S)', 'PO': '(31P)(16O)', 'SiH4': '(28Si)(1H)4', 'NS': '(14N)(32S)', 'CH3F': '(12C)(1H)3(19F)',
    'SiS': '(28Si)(32S)', 'LiF': '(7Li)(19F)', 'NaF': '(23Na)(19F)', 'KF': '(39K)(19F)', 'AlCl': '(27Al)(35Cl)',
    'AlF': '(27Al)(19F)', 'CaF': '(40Ca)(19F)', 'MgF': '(24Mg)(19F)', 'OH+': '(16O)(1H)+', 'AsH3': '(75As)(1H)3',
    'PF3': '(31P)(19F)3', 'PH': '(31P)(1H)', 'CH3': '(12C)(1H)3', 'SiH2': '(28Si)(1H)2', 'SiO2': '(28Si)(16O)2',
    'cis-P2H2': 'cis-(31P)2(1H)2', 'trans-P2H2': 'trans-(31P)2(1H)2', 'H3O+': '(1H)3(16O)+', 'KOH': '(39K)(16O)(1H)',
    'NaOH': '(23Na)(16O)(1H)'
}
