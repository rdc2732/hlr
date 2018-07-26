# parse_hlr.py
# This program will loop through the text version created by DOORS of an HLR module, and search for signals.
# Signals are identified by the a string enclosed in square brackets, e.g. [signal]
# The Input and Output sections in the HLR will be identified and signals tagged accordingly.
# The program will output a .csv file to be the input for an Excel Pivot Table, and a .gfz file to allow Graphiz
# to build a directed graph of the signals and modules.

# Parsing the HLRxx.txt file:
#   - If the first character of the line is a number, the line is a heading (e.g. 1, 1.1, 1.2.2, ...)
#   - If the first character of the line is '[', the line is a signal name, if the signal name is the only
#     thing on the line; some requirements begin with a signal name.
#   - Any line that begins with a tab is DOORS attribute data.
#   - Any text that begins in the first character of the line is requirements text.

# Usage: python parse_hlr2.py  (execute in directory with HLR text files)

import sys
import re
import glob
import csv

signal_list = {}  # will contain a key:value; key = signal_name, value is a list[(modules, io_state)]
modules = {}      # will contain a key:value; key = module name, value = flag if has signal pair
hlr_list = {}     # will contain a key:value; key = (hlr pair), value is list[signals]


csvfile = 'hlr_signals.csv'
dotfile = 'hlr_signals.gfz'

# Parse all txt files for signals and store results in signal_list dictionary
for filename in glob.iglob('*.txt'):
    hlrfile = open(filename, "r")
    module_name = filename[0:filename.find(".")].upper()
    modules[module_name] = False # Preset that this module does not have any signals defined
    title = "Not Assigned"
    io_state = "None" # This is a flag that should be one of None, Input, Output
    line_type = "None" # This is a flag for each line; None, Signal, Attribute, Requirement, Heading

    for line in hlrfile:    # Parse file for all [signal_names] and module name
        print(module_name, line)
        # Determine line_type and extract signal name and type
        line = line.rstrip()

        if len(line) > 0:
            signals = re.findall(r'(\[(.*?)\])', line) # returns a list of tuples ([signal], signal) if present
            line_type = "Requirement"

            if line[0] == "\t": # lines beginning with tab are DOORS attributes
                line_type = "Attribute"
            elif len(signals) == 1 and line == signals[0][0]: # regex determined line is a signal name
                line_type = "Signal"
                signal_name = line
                if signal_name in signal_list: # Append module to signal's existing module list
                    module_list = signal_list[signal_name]
                    if (module_name, io_state) not in module_list:
                        module_list.append((module_name, io_state))
                else:
                    module_list = [(module_name, io_state)] # Create a module list for new signal
                signal_list[signal_name] = module_list # Create or update signal_list
                modules[module_name] = True  # Set true that this module does have signals defined
            elif line[0].isnumeric(): # line starting with a number are headings
                line_type = "Heading"
                if line.find("Input") >= 0 and line.find("Output") == -1: # heading starts input section
                    io_state = "Input"
                elif line.find("Output") >= 0 and line.find("Input") == -1: # heading starts output section
                    io_state = "Output"
                else:
                    io_state = "None" # some other kind of heading

    hlrfile.close()

# for s in signal_list:
#     print(s, signal_list[s])
#
# for m in modules:
#     print(m, modules[m])

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

#
# # Write data to a csv file format suitable for pivot table analysis
# # Columns: HLR1, HLR2, Signal
# csv_data = [['HLR1', 'HLR2', 'Signals']]
#
# for hlr_pair in hlr_list:
#     hlr1 = hlr_pair[0]
#     hlr2 = hlr_pair[1]
#     for sig in hlr_list[hlr_pair]:
#         csv_row = [hlr1, hlr2, sig]
#         csv_data.append(csv_row)
# #         csv_row = [hlr2, hlr1, sig]
# #         csv_data.append(csv_row)
# #
# # for module in modules:
# #     if modules[module] == False:
# #         hlr1 = module
# #         hlr2 = module
# #         csv_row = [hlr1, hlr2]
# #         csv_data.append(csv_row)
#
# myFile = open(csvfile, 'w', newline='')
# with myFile:
#    writer = csv.writer(myFile)
#    writer.writerows(csv_data)
# myFile.close()
#
# # Write data to .dot file suitable for generating graph with Graphiz
# #    process hlr_list for graph
# #    open file for write
# #    write 'header' part
# #    loop: write each line HLR pair with a label for number of signals
# myFile = open(dotfile, 'w')
# myFile.write("graph HLR {\n")
#
# for hlr_pair in hlr_list:
#     hlr1 = hlr_pair[0][:5]
#     hlr2 = hlr_pair[1][:5]
#     sigcount = len(hlr_list[hlr_pair])
#     myFile.write(f'  {hlr1} -- {hlr2} [label="{sigcount}"]\n')
#
# myFile.write("}\n")
# myFile.close()
#
#
#
#
#
