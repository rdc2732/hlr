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
import codecs

input_signals = {}  # will contain a key:value; key = signal_name, value is a list[(modules, io_state)]
output_signals = {}  # will contain a key:value; key = signal_name, value is a list[(modules, io_state)]
modules = {}      # will contain a key:value; key = module name, value = flag if has signal pair
hlr_list = {}     # will contain a key:value; key = (hlr pair), value is list[signals]
sig_in_list = {}  # will contain a key:value; key = (signal), value is list[hlr_in]


csvfile = 'hlr_signals.csv'
dotfile = 'hlr_signals.gfz'
dotfile2 = 'hlr_signals2.gfz'

# Parse all txt files for signals and store results in signal_list dictionary
for filename in glob.iglob('*.txt'):
    hlrfile = open(filename, "r")
    module_name = filename[0:filename.find(".")].upper()
    modules[module_name] = False # Preset that this module does not have any signals defined
    title = "Not Assigned"
    io_state = "None" # This is a flag that should be one of None, Input, Output
    line_type = "None" # This is a flag for each line; None, Signal, Attribute, Requirement, Heading

    for line in hlrfile:    # Parse file for all [signal_names] and module name
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
                if io_state == "Input":
                    if signal_name in input_signals: # Append module to signal's existing module list
                        module_list = input_signals[signal_name]
                        if module_name not in module_list:
                            module_list.append(module_name)
                    else:
                        module_list = [module_name] # Create a module list for new signal
                    input_signals[signal_name] = module_list # Create or update signal_list
                elif io_state == "Output":
                    if signal_name in output_signals: # Append module to signal's existing module list
                        module_list = output_signals[signal_name]
                        if module_name not in module_list:
                            module_list.append(module_name)
                    else:
                        module_list = [module_name] # Create a module list for new signal
                    output_signals[signal_name] = module_list # Create or update signal_list
                modules[module_name] = True  # Set true that this module does have signals defined
            elif line[0].isnumeric(): # line starting with a number are headings
                line_type = "Heading"
                if line.find("Input") >= 0 and line.find("Output") == -1: # heading starts input section
                    io_state = "Input"
                elif line.find("Output") >= 0 and line.find("Input") == -1: # heading starts output section
                    io_state = "Output"
                else:
                    io_state = "None" # some other kind of heading


# Write data to .dot file suitable for generating graph with Graphiz
#    process hlr_list for graph
#    open file for write
#    write 'header' part
#    loop: write each line HLR pair with a label for number of signals
myFile = open(dotfile, 'w')
myFile.write("digraph HLR {\n")

common_signal_list = sorted(list(set(input_signals.keys()).intersection(output_signals.keys())))
for sign in common_signal_list:
    for output in output_signals[sign]:
        for input in input_signals[sign]:
            # Create list of signals between modules in hlr_list; {(hlr_out, hlr_in): [list of signals]}
            if output != input and (output, input) in hlr_list:
                sig_list = hlr_list[(output, input)]
                sig_list.append(sign)
                hlr_list[(output, input)] = sig_list
            else:
                hlr_list[(output, input)] = [sign]

            # Create list of hlr_in for each signals in sig_in_list; {signal: [hlr_in]}
            if output != input and sign in sig_in_list:
                hlr_in_list = sig_in_list[sign]
                hlr_in_list.append(input)
                sig_in_list[sign] = hlr_in_list
            else:
                sig_in_list[sign] = [input]
for hlr_pair in hlr_list:
    outhlr = hlr_pair[0]
    inhlr = hlr_pair[1]
    if outhlr != inhlr:
        sigcount = len(hlr_list[hlr_pair])
        count_label = str(sigcount)
        myFile.write(f'  {outhlr} -> {inhlr} [label="{count_label}"];\n')
myFile.write("}\n")
myFile.close()

# Make version that shows pairs where there is only one input hlr
myFile = open(dotfile2, 'w')
myFile.write("digraph HLR {\n")

hlr_pair_count = {}  # counter of hlr_pairs {hlr_pair : count}
for sign in sig_in_list:
    if len(sig_in_list[sign]) == 1:
        hlr_in = sig_in_list[sign][0]
        for hlr_pair in hlr_list:
            if hlr_in == hlr_pair[1]:
                if hlr_pair[0] != hlr_pair[1] and sign in hlr_list[hlr_pair]:
                    if hlr_pair in hlr_pair_count:
                        hlr_pair_count[hlr_pair] += 1
                    else:
                        hlr_pair_count[hlr_pair] = 1

for hlr_pair in hlr_pair_count:
    label = str(hlr_pair_count[hlr_pair])
    outhlr = hlr_pair[0]
    inhlr = hlr_pair[1]
    myFile.write(f'  {outhlr} -> {inhlr} [label="{label}"];\n')

myFile.write("}\n")
myFile.close()

# Write data to a csv file format suitable for pivot table analysis
# Columns: HLR1, HLR2, Signal
csv_data = [['HLR_Out', 'HLR_In', 'Signals']]

for hlr_pair in hlr_list:
    hlr_out = hlr_pair[0]
    hlr_in = hlr_pair[1]
    if hlr_out != hlr_in:
        for sig in hlr_list[hlr_pair]:
            csv_row = [hlr_out, hlr_in, sig]
            csv_data.append(csv_row)

for module in modules:
    if modules[module] == False:
        hlr1 = module
        hlr2 = module
        csv_row = [hlr1, hlr2]
        csv_data.append(csv_row)

myFile = open(csvfile, 'w', newline='')
with myFile:
   writer = csv.writer(myFile)
   writer.writerows(csv_data)
myFile.close()

