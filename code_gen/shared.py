import code_gen.constants as constants

class VhdlCodeBlock():
    #
    def __init__(self):
        self.statements = []
    #
    def to_str(self, level):
        s = '\n'
        for st in self.statements:
            s += st.to_str(level)
        return s    
    #
    def __str__(self):
        raise NotImplementedError
        
class VhdlStatement():
    #
    def __init__(self, value):
        self._value = value
    #
    def to_str(self, level):
        return indent(level) + self._value
    #
    def __str__(self):
        raise NotImplementedError

class VhdlDeclaration():
    #
    def __init__(self, value):
        self._value = value
    #
    def to_str(self, level):
        return indent(level) + self._value
    #
    def __str__(self):
        raise NotImplementedError

# ------------------------------------------------------------------------------
# Function definitions
#
    

def indent(level):
    return " " * constants.INDENTATION_WIDTH * level    

# ------------------------------------------------------------------------------
# Code generators
#

#
# The mother of all code generators
#
class CodeGenerator():    
    #
    # Returns a field's bit width identifier, e.g. 'WIDTH_CONTROL_RESET'
    def bitWidth_identifier(self, field):
        return 'WIDTH_' + field.parent_reg.name.upper() + '_' + field.name.upper()
    #
    # Returns a field's bit offset identifier, e.g. 'OFFSET_CONTROL_RESET'
    def bitOffset_identifier(self, field):
        return 'OFFSET_' + field.parent_reg.name.upper() + '_' + field.name.upper()
    #
    # Returns a field's bit mask identifier, e.g. 'MASK_CONTROL_RESET'
    def bitMask_identifier(self, field):
        return 'MASK_' + field.parent_reg.name.upper() + '_' + field.name.upper()
    #
    # Returns the name of the record type corresponding to this field
    def vhdl_record_name(self, field):        
        return 't_' + field.parent_reg.name.lower() + '_' + field.name.lower()
    #
    # Returns the name of the VHDL package for a module
    def vhdl_package_name(self, module):
        return module.name.lower() + '_regs_pkg'      
    #
    # Return a register's address identifier, e.g. 'ADDR_CONTROL'
    def address_identifier(self, register):
        return "ADDR_" + register.name.upper()
    #
    # Get a registers's data signal name    
    def vhdl_data_signal(self, register):
        return 's_' + register.name.lower() + "_r"    
    #
    # Get a registers's strobe signal name    
    def vhdl_strobe_signal(self, register):
        return 's_' + register.name.lower() + "_strobe_r"    
    #
    # Returns the name of the VHDL entity for a module
    def vhdl_entity_name(self, module):
        return module.name.lower() + '_regs'      

