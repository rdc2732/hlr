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
import glob

signal_list = {}  # will contain a key:value; key = signal_name, value is a dict[modules]

for filename in glob.iglob('*.rtf'):
    rtffile = open(filename,"r")
    module_name = filename[0:filename.find(".")].upper()
    title = "Not Assigned"

    for line in rtffile:    # Parse file for all [signal_names] and module name
        if line.find("{\\info") >= 0:    # Look for /info line to get module name
            start = line.find("{\\subject") + 10
            stop = line.find("}", start)
            title = line[start:stop]
            module_name += " - " + title
        signals = re.findall(r'(\[(.*?)\])', line) # returns a tuple ([signal], signal)
        for signal in signals:
            signal_name = signal[0]
            # if signal_name == "WOW":
            #     print(module_name)
            if signal_name in signal_list: # Append module to signal's existing module list
                module_list = signal_list[signal_name]
                if module_name not in module_list:
                    module_list.append(module_name)
            else:
                module_list = [module_name] # Create a module list for new signal
            signal_list[signal_name] = module_list # Create or update signal_list

    rtffile.close()

print("====================")
print("Total Signals:", len(signal_list))
for signal in sorted(signal_list):
    print(signal, signal_list[signal])
print("====================")


