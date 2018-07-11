# parse_hlr.py
# This program will loop through an HLR file and search for signals
# Signals are identified by the a string enclosed in square brackets, e.g. [signal]
# Initial functionality is just to output signals.  Future functionality will
#   be to detect signal lists in Inputs and Outputs sections of the document.  Additionally,
#   checks can be added that flag signals found in the document that are not in Inputs/Outputs sections.
# The input file will be assumed to be an .rtf file, which is treated as merely a text file, without
#   attempts to deal with the document structure.  RTF is used because it can be handled easily with Python
#   and is easily genereated from DOORS.

# Usage: python parse_hlr.py input_file

import sys
import re

signal_list = []
filename = sys.argv[1]
rtffile = open(filename,"r")

for line in rtffile:
    if line.find("{\\info") == 0:    # Look for /info line to get module name
        start = line.find("{\\subject") + 10
        stop = line.find("}", start)
        module_name = filename[0:filename.find(".")].upper() + " - " + line[start:stop]
        print(module_name)
    signals = re.findall(r'(\[(.*?)\])', line)
    for signal in signals:
        if (len(signal[0]) < 100) and signal[0] not in signal_list:
            signal_list.append(signal[0])

rtffile.close()

print("Signals Found = ", len(signal_list))
signal_list.sort()
for signal in signal_list:
    print(signal)


