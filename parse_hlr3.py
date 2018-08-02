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

# 1) Create a dictionary of all signals { sig_id : sig_name}
sig_dict = {}
cur.execute('SELECT sig_id, sig_name FROM signals')
for row in cur:
    sig_dict[row[0]] = row[1]


# 2) Create a dictionary of all modules { mod_id : mod_name}
mod_dict = {}
cur.execute('SELECT mod_id, mod_name FROM modules')
for row in cur:
    mod_dict[row[0]] = row[1]


# 3) For each signal, build the list of output modules { sig_id : [hlr_out] }
hlrout_dict = {}
for id in list(sig_dict.keys()):
    cur.execute(f'SELECT mod_id FROM modsigs WHERE mod_sig_type = "Output" and sig_id = {id}')
    mods = []
    for mod in cur.fetchall():
        mods.append(mod[0])
    hlrout_dict[id] = mods


# 4) For each signal, build the list of input modules { sig_id : [hlr_in] }
hlrin_dict = {}
for id in list(sig_dict.keys()):
    cur.execute(f'SELECT mod_id FROM modsigs WHERE mod_sig_type = "Input" and sig_id = {id}')
    mods = []
    for mod in cur.fetchall():
        mods.append(mod[0])
    hlrin_dict[id] = mods

con.close()


# 5) Collect vectors of from-to hlr modules and their list of signals {(hlrout,hlrin):[sigs]}
#      and signals
vector_list = {}
for id in list(sig_dict.keys()):
    outlist = list(set(hlrout_dict[id]))  # use set to scrub for unique
    inlist = list(set(hlrin_dict[id]))
    hlr_pair_list = [(x, y) for x in outlist for y in inlist]
    for hlr_pair in hlr_pair_list:
        if hlr_pair in vector_list:
            sigs = vector_list[hlr_pair]
            sigs.append(id)
            vector_list[hlr_pair] = sigs
        else:
            vector_list[hlr_pair] = [id]


# 6) Write data to a csv file format suitable for pivot table analysis
# Columns: HLR1, HLR2, Signal
csv_data = [['HLR_Out', 'HLR_In', 'Signals']]

for vector in vector_list:
    if vector[0] != vector[1]:
        hlr_out = mod_dict[vector[0]]
        hlr_in = mod_dict[vector[1]]
        for sig in vector_list[vector]:
            signal = sig_dict[sig]
            csv_row = [hlr_out, hlr_in, signal]
            csv_data.append(csv_row)

myFile = open(csvfile, 'w', newline='')
with myFile:
    writer = csv.writer(myFile)
    writer.writerows(csv_data)
myFile.close()


# 7) Write data to .dot file suitable for generating graph with Graphiz
myFile = open(dotfile, 'w')
myFile.write("digraph HLR {\n")

for vector in vector_list:
    if vector[0] != vector[1]:
        hlr_out = mod_dict[vector[0]]
        hlr_in = mod_dict[vector[1]]
        count_label = str(len(vector_list[vector]))
        myFile.write(f'  {hlr_out} -> {hlr_in} [label="{count_label}"];\n')
myFile.write("}\n")
myFile.close()



# =========== ERROR ===========
# The current algorithm does not result in the correct data
# The intention is to select signals that are consumed in only one HLR.
# 8) Collect vectors of from-to hlr modules and their list of signals {(hlrout,hlrin):[sigs]}
#      and signals where the signal only goes to one hlrin

for i in hlrin_dict:
    print(i, sig_dict[i], hlrin_dict[i])
    for j in hlrin_dict[i]:
        print("  ", j, mod_dict[j])

vector_list = {}
for id in list(sig_dict.keys()):
    outlist = list(set(hlrout_dict[id]))  # use set to scrub for unique
    inlist = []
    inlist_temp = list(set(hlrin_dict[id]))
    for temp in inlist_temp: # Pull signals that have only one hlrin
        if len(hlrin_dict[temp]) == 1:
            inlist.append(temp)

    hlr_pair_list = [(x, y) for x in outlist for y in inlist]
    for hlr_pair in hlr_pair_list:
        if hlr_pair in vector_list:
            sigs = vector_list[hlr_pair]
            sigs.append(id)
            vector_list[hlr_pair] = sigs
        else:
            vector_list[hlr_pair] = [id]


# 8) Write data to a csv file format suitable for pivot table analysis
#    where there is only one input hlr
#    Columns: HLR1, HLR2, Signal
csv_data = [['HLR_Out', 'HLR_In', 'Signals']]

for vector in vector_list:
    if vector[0] != vector[1] and len(vector_list[vector]) == 1:
        hlr_out = mod_dict[vector[0]]
        hlr_in = mod_dict[vector[1]]
        for sig in vector_list[vector]:
            signal =  sig_dict[sig]
            csv_row = [hlr_out, hlr_in, signal]
            csv_data.append(csv_row)

myFile = open(csvfile2, 'w', newline='')
with myFile:
   writer = csv.writer(myFile)
   writer.writerows(csv_data)
myFile.close()


# 9) Write data to .dot file suitable for generating graph with Graphiz
#    where there is only one input hlr
myFile = open(dotfile2, 'w')
myFile.write("digraph HLR {\n")

for vector in vector_list:
    if vector[0] != vector[1] and len(vector_list[vector]) == 1:
        hlr_out = mod_dict[vector[0]]
        hlr_in = mod_dict[vector[1]]
        count_label = str(len(vector_list[vector]))
        myFile.write(f'  {hlr_out} -> {hlr_in} [label="{count_label}"];\n')
myFile.write("}\n")
myFile.close()
