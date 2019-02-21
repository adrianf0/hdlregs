#
# C header generator
#

import os
import datetime
import constants
from .shared import CodeGenerator
import code_gen.templates.c as c_templates

class CHeaderGenerator(CodeGenerator):
    def __init__(self, module):
        # Register address offsets
        address_offsets = ""
        for r in module.registers:
            address_offsets += '#define %s 0x%.8X\n' % (self.address_identifier(r), r.addressOffset)
        # Field bit offsets
        fields = ""
        for r in module.registers:
            register_name = r.name.upper()
            fields += "//\n"
            fields += "// Fields in register '%s'\n" % register_name
            fields += "//\n"
            for f in r.fields:
                field_name = f.name.upper()
                field_mask = (2 ** f.bitWidth - 1) << f.bitOffset
                fields += "// Field '%s'\n" % f.name
                fields += "#define %s %d\n" % (self.bitOffset_identifier(f), f.bitOffset)
                fields += "#define %s %d\n" % (self.bitWidth_identifier(f), f.bitWidth)
                fields += "#define %s 0x%.8X\n" % (self.bitMask_identifier(f), field_mask)
                fields += "\n"
            fields += "\n"
        module_name = module.name.upper() + "_REGS"
        d = dict(module_name = module_name,
                 address_offsets = address_offsets,
                 fields = fields,
                 json_module_name = module.name,
                 hdlregs_version = constants.HDLREGS_VERSION,
                 date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        self._code = c_templates.C_HEADER_TEMPLATE.substitute(d)
                
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self._code)
