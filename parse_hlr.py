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

signal_list = {}  # will contain a key:value; key = signal_name, value is a list[modules]
hlr_list = {}     # will contain a key:value; key = (hlr pair), value is list[signals]

# Parse all rtf files for signals and store results in signal_list dictionary
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
            if signal_name.upper() == signal_name: # Eliminate things that have brackets but not uppercase
                if signal_name in signal_list: # Append module to signal's existing module list
                    module_list = signal_list[signal_name]
                    if module_name not in module_list:
                        module_list.append(module_name)
                else:
                    module_list = [module_name] # Create a module list for new signal
                signal_list[signal_name] = module_list # Create or update signal_list
            else:
                print(filename, "||", module_name, "||", signal_name)

    rtffile.close()

print("====================")
print("Total Signals:", len(signal_list))
print("====================")
for signal in sorted(signal_list):
    if len(signal_list[signal]) > 1:
        hlr_used = signal_list[signal]
        hlr_used.sort()
        for x in range(len(hlr_used) - 1):
            for y in range(x + 1, len(hlr_used)):
                hlr_tuple = (hlr_used[x], hlr_used[y])
                if hlr_tuple in hlr_list:  # Append signal to signal's existing hlr list
                    signals = hlr_list[hlr_tuple]
                    if signal not in signals:
                        signals.append(signal)
                else:
                    signals = [signal]  # Create a module list for new signal
                hlr_list[hlr_tuple] = signals  # Create or update signal_list
print("====================")
print("Total HLR Pairs:", len(hlr_list))
print("====================")
