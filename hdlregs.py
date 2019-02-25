#!/usr/bin/python

# Copyright (c) 2013, Guy Eschemann,
#               2019, Fastree3D
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies, 
# either expressed or implied, of the FreeBSD Project.

import sys
import json
import os
import datetime
import argparse

#import structures
from structures import Module, ModuleError, RegisterError, FieldError
import code_gen.vhdl
import code_gen.html
import code_gen.c
            
# ------------------------------------------------------------------------------
# The main() function
#
if __name__ == "__main__":

    class writable_dir(argparse.Action):
        #Class checking if provided directory path is actually writable
        def __call__(self, parser, namespace, values, option_string=None):
            prospective_dir=values
            if not os.path.isdir(prospective_dir):
                raise argparse.ArgumentError(self, "writable_dir:{0} is not a valid path".format(prospective_dir))
            if os.access(prospective_dir, os.W_OK):
                setattr(namespace,self.dest,prospective_dir)
            else:
                raise argparse.ArgumentError(self, "writable_dir:{0} is not a writable dir".format(prospective_dir))
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description=
'''
HDLRegs is an open-source HDL register file generator written in the Python programming language. 
It takes a register specification in JSON format and generates the following output files:
 * VHDL package
 * Synthesizable VHDL component
 * C header
 * HTML documentation.
''')
    parser.add_argument('register_definition_file', type=file, 
                        help='register definition file in JSON format')
    parser.add_argument('-novhdl', action='store_false',
                        help='prevents VHDL output generation')
    parser.add_argument('-vhdl_output_dir', action=writable_dir, default='.',
                        help='path to the VHDL output directory')
    parser.add_argument('-noc', action='store_false',
                        help='prevents C output generation')
    parser.add_argument('-c_output_dir', action=writable_dir, default='.',
                        help='path to the C output directory')
    parser.add_argument('-nohtml', action='store_false',
                        help='prevents html output generation')
    parser.add_argument('-html_output_dir', action=writable_dir, default='.',
                        help='path to the HTML output directory')
    arguments = parser.parse_args()

    # Check for non-ascii characters in JSON file, as these are not supported yet
    num_ascii_errors = 0
    line_number = 1
    for line in arguments.register_definition_file:
        for char in line:
            if ord(char) > 127:
                print "Error in line %d: detected non-ascii character '%c'" % (line_number, char)
                num_ascii_errors += 1
        line_number += 1
    if num_ascii_errors > 0:
        sys.exit(-1)

    arguments.register_definition_file.seek(0)
    try:
        # Load JSON file
        json_data = json.load(arguments.register_definition_file)
        module = Module(json_data)
           
        # Write HTML output
        if arguments.nohtml:
            g = code_gen.html.HtmlGenerator(module)
            g.save(arguments.html_output_dir + module.name + '_regs.html')

        # Write C header
        if arguments.noc:
            g = code_gen.c.CHeaderGenerator(module)
            g.save(arguments.c_output_dir + module.name + '_regs.h')

        # Write VHDL output
        if arguments.novhdl:
            # Write VHDL package
            g = code_gen.vhdl.VhdlPackageGenerator(module)
            g.save(arguments.vhdl_output_dir + module.name + '_regs_pkg.vhd')

            # Write VHDL component
            g = code_gen.vhdl.VhdlComponentGenerator(module)
            g.save(arguments.vhdl_output_dir + module.name + '_regs.vhd')
                            
    except RegisterError as ex:
        print "Error in register " + str(ex)
    
    except FieldError as ex:
        print "Error in field " + str(ex)
    
    except ModuleError as ex:
        print "Error in module " + str(ex)        

