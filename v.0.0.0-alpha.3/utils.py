def kg_to_lbs(kg):
    if kg is None:
        return None
    return kg * 2.20462  # Conversion factor for kg to lbs

def lbs_to_kg(lbs):
    if lbs is None:
        return None
    return lbs / 2.20462  # Conversion factor for lbs to kg

def cm_to_ft_in(cm):
    if cm is None:
        return {'feet': None, 'inches': None}
    inches = cm * 0.393701  # cm to inches
    feet = int(inches / 12)
    remaining_inches = inches % 12
    return {'feet': feet, 'inches': remaining_inches}

def ft_in_to_cm(feet, inches):
    if feet is None or inches is None:
        return None
    total_inches = (feet * 12) + inches
    return total_inches * 2.54  # inches to cm
