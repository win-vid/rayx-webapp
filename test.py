import rayx, flask

bl = rayx.import_beamline("./resources/METRIX_U41_G1_H1_318eV_PS_MLearn_v114.rml")

rays = bl.trace()

print(rays)
