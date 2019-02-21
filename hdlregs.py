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
import datetime

#import structures
from structures import Module, ModuleError, RegisterError, FieldError
import code_gen.vhdl
import code_gen.html
import code_gen.c
            
# ------------------------------------------------------------------------------
# The main() function
#
if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print "usage: python hdlregs.py <register definition file>"
        sys.exit(-1)
        
    try:
        register_definition_file = sys.argv[1]
        
        # Check for non-ascii characters in JSON file, as these are not supported yet
        num_ascii_errors = 0
        with open(register_definition_file, 'r') as f:
            line_number = 1
            for line in f:
                for char in line:
                    if ord(char) > 127:
                        print "Error in line %d: detected non-ascii character '%c'" % (line_number, char)
                        num_ascii_errors += 1
                line_number += 1
        if num_ascii_errors > 0:
            sys.exit(-1)
        
        # Load JSON file
        json_data = json.load(open(register_definition_file, 'r'))
        module = Module(json_data)
           
        # Write HTML output
        g = code_gen.html.HtmlGenerator(module)
        g.save(module.name + '_regs.html')

        # Write C header
        g = code_gen.c.CHeaderGenerator(module)
        g.save(module.name + '_regs.h')

        # Write VHDL package
        g = code_gen.vhdl.VhdlPackageGenerator(module)
        g.save(module.name + '_regs_pkg.vhd')

        # Write VHDL component
        g = code_gen.vhdl.VhdlComponentGenerator(module)
        g.save(module.name + '_regs.vhd')
                            
    except RegisterError as ex:
        print "Error in register " + str(ex)
    
    except FieldError as ex:
        print "Error in field " + str(ex)
    
    except ModuleError as ex:
        print "Error in module " + str(ex)        

