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
import csv

signal_list = {}  # will contain a key:value; key = signal_name, value is a list[modules]
modules = {}      # will contain a key:value; key = module name, value = flag if has signal pair
hlr_list = {}     # will contain a key:value; key = (hlr pair), value is list[signals]

csvfile = 'hlr_signals.csv'
dotfile = 'hlr_signals.gfz'

# Parse all rtf files for signals and store results in signal_list dictionary
for filename in glob.iglob('*.rtf'):
    rtffile = open(filename,"r")
    module_name = filename[0:filename.find(".")].upper()
    title = "Not Assigned"

    for line in rtffile:    # Parse file for all [signal_names] and module name
        if line.find("Inputs") >= 0 and line.find("Outputs") == -1:
            print("Input\t", filename, "\t", line)
        if line.find("Output") >= 0 and line.find("Inputs") == -1:
            print("Output\t", filename, "\t", line)
        if line.find("{\\info") >= 0:    # Look for /info line to get module name
            start = line.find("{\\subject") + 10
            stop = line.find("}", start)
            title = line[start:stop]
            module_name += " - " + title
            modules[module_name] = False # Create dictionary entry for module
        signals = re.findall(r'(\[(.*?)\])', line) # returns a tuple ([signal], signal)
        for signal in signals:
            signal_name = signal[0]
            if signal_name.upper() == signal_name: #and len(signal_name) < 50: # Eliminate things that have brackets but not uppercase
                if signal_name in signal_list: # Append module to signal's existing module list
                    module_list = signal_list[signal_name]
                    if module_name not in module_list:
                        module_list.append(module_name)
                else:
                    module_list = [module_name] # Create a module list for new signal
                signal_list[signal_name] = module_list # Create or update signal_list
                modules[module_name] = True # Change flag to show module has signal pair(s)
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

# Write data to a csv file format suitable for pivot table analysis
# Columns: HLR1, HLR2, Signal
csv_data = [['HLR1', 'HLR2', 'Signals']]

for hlr_pair in hlr_list:
    hlr1 = hlr_pair[0]
    hlr2 = hlr_pair[1]
    for sig in hlr_list[hlr_pair]:
        csv_row = [hlr1, hlr2, sig]
        csv_data.append(csv_row)
#         csv_row = [hlr2, hlr1, sig]
#         csv_data.append(csv_row)
#
# for module in modules:
#     if modules[module] == False:
#         hlr1 = module
#         hlr2 = module
#         csv_row = [hlr1, hlr2]
#         csv_data.append(csv_row)

myFile = open(csvfile, 'w', newline='')
with myFile:
   writer = csv.writer(myFile)
   writer.writerows(csv_data)
myFile.close()

# Write data to .dot file suitable for generating graph with Graphiz
#    process hlr_list for graph
#    open file for write
#    write 'header' part
#    loop: write each line HLR pair with a label for number of signals
myFile = open(dotfile, 'w')
myFile.write("graph HLR {\n")

for hlr_pair in hlr_list:
    hlr1 = hlr_pair[0][:5]
    hlr2 = hlr_pair[1][:5]
    sigcount = len(hlr_list[hlr_pair])
    myFile.write(f'  {hlr1} -- {hlr2} [label="{sigcount}"]\n')

myFile.write("}\n")
myFile.close()





