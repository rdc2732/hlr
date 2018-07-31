# parse_hlr.py
# This program will loop through the text version created by DOORS of an HLR module, and search for signals.
# Signals are identified by the a string enclosed in square brackets, e.g. [signal]
# The Input and Output sections in the HLR will be identified and signals tagged accordingly.
# The program will output a .csv file to be the input for an Excel Pivot Table, and a .gfz file to allow Graphiz
# to build a directed graph of the signals and modules.

# This version of the program will use sqlite to store the signals as they are found, and then be used via queries
# To create the data sets for the .csv and .gfx files.  This will also permit future reports that will be much
# easier to achieve from the database.

# Parsing the HLRxx.txt file:
#   - If the first character of the line is a number, the line is a heading (e.g. 1, 1.1, 1.2.2, ...)
#   - If the first character of the line is '[', the line is a signal name, if the signal name is the only
#     thing on the line; some requirements begin with a signal name.
#   - Any line that begins with a tab is DOORS attribute data.
#   - Any text that begins in the first character of the line is requirements text.

# Usage: python parse_hlr3.py  (execute in directory with HLR text files)

import sys
import re
import glob
import csv
import codecs
import sqlite3

input_signals = {}  # will contain a key:value; key = signal_name, value is a list[(modules, io_state)]
output_signals = {}  # will contain a key:value; key = signal_name, value is a list[(modules, io_state)]
modules = {}      # will contain a key:value; key = module name, value = flag if has signal pair
hlr_list = {}     # will contain a key:value; key = (hlr pair), value is list[signals]
sig_in_list = {}  # will contain a key:value; key = (signal), value is list[hlr_in]

# Define files
sqldbfile = 'hlr.db'
csvfile = 'hlr_signals.csv'
csvfile2 = 'hlr_signals2.csv'
dotfile = 'hlr_signals.gfz'
dotfile2 = 'hlr_signals2.gfz'

# Set up sqlite database
con = sqlite3.connect(sqldbfile)
cur = con.cursor()

cur.execute("DROP TABLE IF EXISTS Modules")
cur.execute("DROP TABLE IF EXISTS Signals")
cur.execute("DROP TABLE IF EXISTS ModSigs")
cur.execute("CREATE TABLE Modules (mod_id INTEGER PRIMARY KEY, mod_name TEXT, UNIQUE (mod_name))")
cur.execute("CREATE TABLE Signals (sig_id INTEGER PRIMARY KEY, sig_name TEXT, UNIQUE (sig_name))")
cur.execute("CREATE TABLE ModSigs (mod_sig_type TEXT, mod_sig_line INTEGER, \
                mod_id INTEGER, sig_id INTEGER, \
                FOREIGN KEY(mod_id) REFERENCES Modules(mod_id), \
                FOREIGN KEY (sig_id) REFERENCES Signals(sig_id))")


# Parse all txt files for signals and store results in database
for filename in glob.iglob('*.txt'):
    hlrfile = open(filename, "r")
    hlrfile_line_count = 0
    module_name = filename[0:filename.find(".")].upper()
    modules[module_name] = False # Preset that this module does not have any signals defined
    title = "Not Assigned"
    io_state = "None" # This is a flag that should be one of None, Input, Output
    line_type = "None" # This is a flag for each line; None, Signal, Attribute, Requirement, Heading

    # Insert module name into the database, get the row_id for the FK relations
    cur.execute('INSERT OR IGNORE INTO Modules (mod_name) VALUES (?)', (module_name,))
    cur.execute('SELECT mod_id FROM Modules WHERE mod_name = ?', (module_name,))
    module_id = cur.fetchone()[0]

    for line in hlrfile:    # Parse file for all [signal_names] and module name
        # Determine line_type and extract signal name and type
        hlrfile_line_count += 1
        line = line.rstrip()

        if len(line) > 0:
            signals = re.findall(r'(\[(.*?)\])', line) # returns a list of tuples ([signal], signal) if present
            line_type = "Requirement"

            if line[0] == "\t": # lines beginning with tab are DOORS attributes
                line_type = "Attribute"
            elif len(signals) == 1 and line == signals[0][0]: # regex determined line is a signal name
                line_type = "Signal"
                signal_name = line
                cur.execute('INSERT OR IGNORE INTO Signals (sig_name) VALUES (?)', (signal_name,))
                cur.execute('SELECT sig_id FROM Signals WHERE sig_name = ?', (signal_name,))
                signal_id = cur.fetchone()[0]
                cur.execute('INSERT INTO ModSigs (mod_sig_type, mod_sig_line, mod_id, sig_id) \
                    VALUES (?,?,?,?)', (io_state, hlrfile_line_count, module_id, signal_id))

                modules[module_name] = True  # Set true that this module does have signals defined
            elif line[0].isnumeric(): # line starting with a number are headings
                line_type = "Heading"
                if line.find("Input") >= 0 and line.find("Output") == -1: # heading starts input section
                    io_state = "Input"
                elif line.find("Output") >= 0 and line.find("Input") == -1: # heading starts output section
                    io_state = "Output"
                else:
                    io_state = "None" # some other kind of heading

# Commit and close database
con.commit()

# # Write data to .dot file suitable for generating graph with Graphiz
# #    process hlr_list for graph
# #    open file for write
# #    write 'header' part
# #    loop: write each line HLR pair with a label for number of signals
# myFile = open(dotfile, 'w')
# myFile.write("digraph HLR {\n")
#
# common_signal_list = sorted(list(set(input_signals.keys()).intersection(output_signals.keys())))
# for sign in common_signal_list:
#     for output in output_signals[sign]:
#         for input in input_signals[sign]:
#             # Create list of signals between modules in hlr_list; {(hlr_out, hlr_in): [list of signals]}
#             if output != input and (output, input) in hlr_list:
#                 sig_list = hlr_list[(output, input)]
#                 sig_list.append(sign)
#                 hlr_list[(output, input)] = sig_list
#             else:
#                 hlr_list[(output, input)] = [sign]
#
#             # Create list of hlr_in for each signals in sig_in_list; {signal: [hlr_in]}
#             if output != input and sign in sig_in_list:
#                 hlr_in_list = sig_in_list[sign]
#                 hlr_in_list.append(input)
#                 sig_in_list[sign] = hlr_in_list
#             else:
#                 sig_in_list[sign] = [input]
# for hlr_pair in hlr_list:
#     outhlr = hlr_pair[0]
#     inhlr = hlr_pair[1]
#     if outhlr != inhlr:
#         sigcount = len(hlr_list[hlr_pair])
#         count_label = str(sigcount)
#         myFile.write(f'  {outhlr} -> {inhlr} [label="{count_label}"];\n')
# myFile.write("}\n")
# myFile.close()


# select
#     t1.sig_id, t1.mod_id, t2.mod_id
# from
#     modsigs as t1, modsigs as t2
# where
#     t1.mod_sig_type = 'Output' and
#     t2.mod_sig_type = 'Input' and
#     t1.sig_id = t2.sig_id and
#     t1.mod_id != t2.mod_id
# ;

# select
#     mod_name, sig_name, mod_sig_type, mod_sig_line
# from
#     Modules, Signals, ModSigs
# where
#     modules.mod_id = modsigs.mod_id and
#     signals.sig_id = modsigs.sig_id
# ;


query = '''
select
	sig_name, t1.sig_id, mod_name, t1.mod_id, mod_name, t2.mod_id		
from 
	modsigs as t1, modsigs as t2, Signals, Modules
where 
	t1.mod_sig_type = 'Output' and 
	t2.mod_sig_type = 'Input' and 
	t1.sig_id = t2.sig_id and
	Signals.sig_id = t1.sig_id and
	Modules.mod_id = t1.mod_id and
	Modules.mod_id = t2.mod_id
'''
cur.execute(query)


# Write data to a csv file format suitable for pivot table analysis
# Columns: HLR1, HLR2, Signal
csv_data = [['HLR_Out', 'HLR_In', 'Signals']]

for row in cur:
    hlr_out = row[2]
    hlr_in = row[4]
    sig = row[0]
    csv_row = [hlr_out, hlr_in, sig]
    csv_data.append(csv_row)

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










# # Make version that shows pairs where there is only one input hlr
# myFile = open(dotfile2, 'w')
# myFile.write("digraph HLR {\n")
#
# hlr_pair_list = {}  # counter of hlr_pairs {hlr_pair : count}
# for sign in sig_in_list:
#     if len(sig_in_list[sign]) == 1:
#         hlr_in = sig_in_list[sign][0]
#         for hlr_pair in hlr_list:
#             if hlr_in == hlr_pair[1]:
#                 if hlr_pair[0] != hlr_pair[1] and sign in hlr_list[hlr_pair]:
#                     if hlr_pair in hlr_pair_list:
#                         sig_list = hlr_pair_list[hlr_pair]
#                         sig_list.append(sign)
#                     else:
#                         sig_list = [sign]
#                     hlr_pair_list[hlr_pair] = sig_list
#
# for hlr_pair in hlr_pair_list:
#     hlr_out = hlr_pair[0]
#     hlr_in = hlr_pair[1]
#     label = str(len(hlr_pair_list[hlr_pair]))
#     outhlr = hlr_pair[0]
#     inhlr = hlr_pair[1]
#     myFile.write(f'  {outhlr} -> {inhlr} [label="{label}"];\n')
#
# myFile.write("}\n")
# myFile.close()
#
#
# # Write data to a csv file format suitable for pivot table analysis
# # Columns: HLR1, HLR2, Signal
# csv_data = [['HLR_Out', 'HLR_In', 'Signals']]
#
# for hlr_pair in hlr_pair_list:
#     hlr_out = hlr_pair[0]
#     hlr_in = hlr_pair[1]
#     if hlr_out != hlr_in:
#         for sig in hlr_pair_list[hlr_pair]:
#             csv_row = [hlr_out, hlr_in, sig]
#             csv_data.append(csv_row)
#
# myFile = open(csvfile2, 'w', newline='')
# with myFile:
#    writer = csv.writer(myFile)
#    writer.writerows(csv_data)
# myFile.close()
#

con.close()
