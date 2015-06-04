#!/usr/bin/env python
import collections
import re
import sets
import sys, os.path
import code
import re

#
# final step is to create the "dependency graph": based on goto, call/return
# statements
# goto statement deduction is easy and has been done
# call/return is tricky as this can be made from reading the ucode_in_c.c file alone
# At C level file, the call/return information has been normalized and is lost
# Instead, go read the ".dis" file; all labels that have entry of the form
#   Push PC+1 = 0x606 (flow_ctrl_pkt_read_ktree_result) on the call stack
# are return instructions and must be entered in "special_labels"; the line immediately
# next to it is the function entry and must also be put in "special_labels"
# the functions are normalized as "goto" already, so they must be already taken care of
# by logic that handles goto;
#
# str1[str1.find("(")+1:str1.find(")")]
#

dep_graph_dict = {}
label_id_map={}
total_instructions = 0

# according to the profile data, this function takes up about 82% of the time.
# it is called about 6500 times, one for each instruction being optimized.
# for each iteration it takes 7.3 seconds cumulative time and 3.75 seconds native time.
# it makes lots of str.find and str.endswith calls.
# plan is to optimize as much as possible natively in python code.
# then move to cython level optimizations. But focus is going to be just this one function.

# filename is "ucode_in_cfile"; label is the label for which code is being optimized for.

# given a label, make a list of all the labels which can lead to it.
# "goto" statements, immediate next label, "call" statements determine code execution sequence.
# "call" statements are converted to "goto" statements in ucode_to_c compiler, creating
# appropriate "return_to" statements.
# the calculated information is stored as a list in "dep_graph_dict"

def dependency_graph(filename, label):
    #
    # Need to create a dictionary; key is label; data is list of all labels that can lead to it;
    # {label:[l1, l2, l3]}
    # simplest way is to read from beginning of the file, identify goto & call statements; see if any of them
    # can lead to it; by default add the preceding label, if suitable statements found add those labels too
    #

    #
    # open the file again, identify required code section
    #
    working_label = prev_label = ""
    match_str = label + ":\n"
    start_work = False

    expr = r'.*goto.*' + label + r' |.*RETURN_TO.*' + label + r'[ \)].*'
    rec = re.compile(expr)

    with open(filename) as f:
        for line in f:

          ending = line[-2:]
          if (ending == ":\n"):
              #label seen, start work
              prev_label = working_label
              working_label = line[:-2]
              start_work = True

          if (start_work == False):
              continue

          if (ending == "}\n"):
              # all labels scanned
              #break
              pass

          # one call C-level find which could be faster; one could try Cython or
          # ctypes to go to C-level function

          # create a compiled regex which will match for ((goto | RETURN_TO) AND (label))
          # this will eliminate 3 find and use one compiled regex instead
          # one can check which one will be faster by profiling
          #match = rec.match(line)
          #if (match):
          if (line.find(label) != -1):
          #if (line.find("goto") != -1 or line.find("RETURN_TO") != -1):
                  # line of interest... does it have my name?
          #        if (line.find(label) != -1):
                     ### extend dict's list;
                     try:
                        dep_graph_dict[label].append(working_label)
                     except KeyError:
                        dep_graph_dict[label] = [working_label]

          if (line == match_str):
                  # my own label found, at the very least I need to add my previous guy to compare to
                  # could be optimized further by checking if the previous label will lead to me 
                  # (ie previous label has all goto statements and none lead to me)

                  try:
                     dep_graph_dict[label].append(prev_label)
                  except KeyError:
                     dep_graph_dict[label] = [prev_label]
      
# time to make the code more sophisticated
# when deciding to filter a line, one needs to check what variables are there in the line
# if any of the variable has been affected so far in this label, then even if that
# line is identical to previous label, it should be retained.
#
# label1:
#    x = 2;
#    y = 3
#    z = x + y
#
# label2:
#    x = 3
#    y = 3
#    z = x + y
#
# in this example, even if "z = x + y" is same, it needs to be retained as x has 
# changed 

special_keywords = sets.Set (["ror64", "-1ull", "rol64", "lmem_read64"])
special_labels = []

def variable_dep_check(lc, full_code_dict, lc_index):
    # split the string but seperator could be one of " ,()&~<<>> - +"
    retain = False
    code = re.split(r'(\W+)', lc)
    for splits in code:
        if (splits.isalnum()):
            # only interested in alpha-nums
            if (splits.isdigit()):
                # pure num, ignore
                continue
            if (splits[0:1] == "0x"):
                # hex num, ignore
                continue
            if (splits in special_keywords):
                continue
            var = splits
            # has this var been referenced before in full_code_dict so far?
            for index,key in enumerate(full_code_dict):
                if (index > (lc_index -1)):
                    # checked enough
                    break
                #cmp_code = key + " " + full_code_dict[key]
                #if (cmp_code.find(var) != -1):
                # cleanse the key as it has spaces in it;

                if (var == (key.lstrip()).rstrip()):
                    retain = True
                    break
                
    return (retain)

def process_ucode_file(name):
    ## for each line in file, look for "const label " 
    ## from first match, look for "=" and take the last token
    ## if "};" is hit, we are done for this block and keep looking

    in_block = False
    with open(name) as f:
        for line in f:
          if ((line.lstrip()).startswith("const label ")):
              def_line = line
              in_block = True
          if (line.find("};") != -1):
              in_block = False
          if (in_block):
              split_l = line.split("=")
              if (len(split_l) != 2):
                  print "strange line", line, "for ", def_line
                  continue
              s_label = (split_l[1]).rstrip(",\n")
              ## check and add it to the special labels list
              try:
                  special_labels.index(s_label)
              except ValueError:
                  special_labels.append(s_label)
              except:
                  raise
              
def process_dis_file(name):
    with open(name) as f:
        for line in f:
             if (line.find("on the call stack") != -1):
                 ret_label = line[line.find("(")+1:line.find(")")]
                 try:
                     special_labels.index(ret_label)
                 except ValueError:
                     special_labels.append(ret_label)
                 except:
                     raise

def map_labels_to_id(name):
    with open(name) as f:
        for line in f:
           if (line.find("label name") != -1):
               index1 = line.find("=")
               index2 = line[index1+2:].find('"')
               if (index1 == -1 or index2 == -1):
                   continue
               label = line[index1+2:index1+2+index2]

               index1 = line.rfind("=")
               index2 = line[index1+2:].rfind('"')
               if (index1 == -1 or index2 == -1):
                   continue
               id = line[index1+2:index1+2+index2]

               key = str(hex(int(id[1:])))
               key = "Ix"+ key[2:]
               label_id_map[key] = label

def form_special_labels(path):
    ## open all *.t and *.th files;

    dis_file_found = False
    xml_file_name = None
    dir_generator = os.walk(path)
    while True:
        try:
            dir_tuple = dir_generator.next()
            file_list = dir_tuple[2]
            for file_name in file_list:
                is_t_file = file_name.endswith(".t") or file_name.endswith(".th")
                if (is_t_file):
                    full_file_name = dir_tuple[0] + "/" + file_name
                    process_ucode_file(full_file_name)
                is_dis_file = file_name.endswith(".dis")
                if (is_dis_file):
                    dis_file_found = True
                    full_file_name = dir_tuple[0] + "/" + file_name
                    process_dis_file(full_file_name)
                is_xml_file = "a.xml"
        except StopIteration:
            if (dis_file_found == False):
                print "dis file needed, please build it and try again...aborting"
                raise
            break
    xml_file_name = path + "/" + "a.xml"
    map_labels_to_id(xml_file_name)

def check_special_label(id_label):
   ## this is the place we have to move away from ucode_in_c.c file to other ways..
   ## generic way: look for all "const label " struc definitions
   ## need to do mapping; special_labels is in name form id_label is in id form;
   try:
       return (label_id_map[id_label] in special_labels)
   except:
       ## if I don't have this id_label, be conservative, return True so that
       ## code for this label won't be optimized
       return (True)
#
# given a line, identify its depedent variables; need regex matching skills;
# form list of matching variables;
# for each item in list, check if item was in cleansed key or key of previous items
# in ordered dict; if present then, it needs to be not skipped as it falls into
# category "z = x + y" above; else it can be safely skipped;

def deep_inspection(ordered_full_dict, line_of_code, lc_index, label):
    retain = True

    ## now use the label to find out if label is special ie entry point for any
    ## registered JNH opcode; these can be dynamically entered, so ignore it.
    ## this mus tuse ctypes to call into C-style code to get this

    retain = check_special_label(label)
    if (retain == True):
       return True

    ## next level of checking
    retain = variable_dep_check(line_of_code, ordered_full_dict, lc_index)
    return (retain)

# first arg: list of code lines which will be used as basis for comparison.
# second arg: list of code lines which will be optimized
# third arg: out file to write optimized lines
# fourth arg: flag to indicate if this is the very first label, so there is nothing to compare to.
# fifth arg: label which is being optimized. If this is a special label, no optimization will be done.

# takes care of special labels

def compare_code(**kw_args):

   full_code_dict = collections.OrderedDict()
   optimized_code_dict = collections.OrderedDict()
   which = None

   out = kw_args['outfile']
   first_label_flag = kw_args['flag']
   label = kw_args['label']

   ## cleanup this mess....
   which = full_code_dict
   compare_lines = kw_args['compare_lines']

   for line in compare_lines:
        if (line.find("=") != -1):
          split_l = line.split("=")
          which[split_l[0]] = split_l[1]
        else:
          which[line]  = ""

   which = optimized_code_dict
   optimize_lines = kw_args['optimize_lines']

   for line in optimize_lines:
        if (line.find("=") != -1):
          split_l = line.split("=")
          which[split_l[0]] = split_l[1]
        else:
          which[line]  = ""

   # print full_code_dict
   # print optimized_code_dict

   retain = False
   for lc_index, item in enumerate(full_code_dict):
      if (optimized_code_dict.has_key(item)):
          if (full_code_dict[item] == optimized_code_dict[item]):
              ## duplicates
              # print "duplicate item found", item, full_code_dict[item]
              full_lineofcode = item + "=" + optimized_code_dict[item]
              retain = deep_inspection(full_code_dict, full_lineofcode, lc_index, label)
              if (retain == False):
                  del optimized_code_dict[item]

   # print "after removing dups", optimized_code_dict

   write_cmp = []

   for item in optimized_code_dict:
       if (optimized_code_dict[item] != ""):
           str1 = item + "=" + optimized_code_dict[item]
       else:
           str1 = item
       write_cmp.append(str1)

   ### write compare_lines to file, only based on flag ...
   # ie if this is the very first label

   if (first_label_flag):
       for line in compare_lines:
          out.write(line)

   # print "writing phase"
   # print write_cmp
   # print "orig code..."
   # print arg_list[1]

   ### only lines in write_cmp needs to be written
   for line in optimize_lines:
       try:
          write_cmp.index(line)
       except  ValueError:
          # print "err in", line
          pass
       except:
           raise
       else:
           out.write(line)

#
# walk over the ucode_in_c file and identify the labels.
# for each label, form "optimize_for_lines", list of lines that would be optimized.
# for each label find out its "dependency graph".
# for each dependency_label, form the "compare_lines", list of lines that would be compared with
# "compare_code" takes "compare_lines" and "optimize_for_lines"; it writes the optimized lines directly
# This is incorrect and needs to be fixed.
# XXXX: Incomplete..... a good logic needs to be found first.
#

def optimize_code(input, output):
    out = file(output, 'w')
    lines1 = []
    lines2 = []
    which = None
    toggle = 0
    write_first = 1
    global total_instructions

    with open(input) as f:
        for line in f:
          if line.endswith("}\n"):
              # end of work, as all labels have been processed; rest of code just needs to be copied
              # blindly.
              which = None
          if line.endswith(":\n"):
             ## label seen, form depedency graph for this label
             total_instructions += 1
             dependency_graph(input, line[:-2])

             ## if both lines1 and lines2 not empty, time to compare
             if (len(lines1) != 0 and len(lines2) != 0):
                 print "processing label: ", line[:-2]
                 # the logic is incorrect as
                 compare_code(compare_lines=lines1, optimize_lines=lines2, outfile=out, flag=write_first, label=line[:-2])
                 lines1 = list(lines2)
                 lines2 = []
                 toggle = 1
                 write_first = 0

             if (toggle == 0):
                which = lines1
             else:
                which = lines2
             toggle = toggle ^ 1

          if (which == None):
              # lines past the last label. Just blindly write them to the outfile to form
              # complete file
              out.write(line)
          else:
              which.append(line)

def main():
    form_special_labels("/b/harih/tdf/src/pfe/ucode/lu")
    # print "special labels are ", special_labels

    input_file = "/homes/haribala/logs/ucode_in_c.c"
    #input_file = "./comp.c"
    output_file = "./comp_opt.c"
    optimize_code(input_file, output_file)

    print "dependency info"
    print dep_graph_dict

if(__name__ == "__main__"):
    main()
    #code.interact(local=globals())
