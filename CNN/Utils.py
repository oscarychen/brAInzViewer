def formatScanName(name):
    return name.strip().replace('.nii','').replace('_750','').replace('.gz','').upper()