#
# Register file elements: Module, Register and Field classes
#

import re
import os
import json
import code_gen.constants as constants

# ------------------------------------------------------------------------------
# Exceptions
#
    
class FieldError(Exception): 
    def __init__(self, field, message):
        Exception.__init__(self, "'%s': %s" % (field.name, message))

class RegisterError(Exception): 
    def __init__(self, register, message):
        if len(register.name) == 0:
            register.set_name('<unnamed>')
        Exception.__init__(self, "'%s': %s" % (register.name, message))
    
class ModuleError(Exception): 
    def __init__(self, module, message):
        Exception.__init__(self, "'%s': %s" % (module.name, message))

# ------------------------------------------------------------------------------
# Function definitions
#

#
# Convert json element (i.e. integer or string) to integer
#
def int_from_json(json):
    if type(json) == int:
        return json
    else:    
        if json.startswith("0x"):
            return int(json, 16)
        else:
            return int(json, 10)

#
# Checks whether the given string is a valid VHDL basic identifier:
#   basic_identifier ::=
#     letter { [ underline ] letter_or_digit } 
#
def is_valid_identifier(str):
    if len(str) == 0: 
        return False
    if str.lower() in constants.RESERVED_VHDL_KEYWORDS:
        return False
    if str in constants.RESERVED_C_KEYWORDS:
        return False
    pattern = r'[a-zA-Z](_?[a-zA-Z0-9])*$'
    if re.match(pattern, str):
        return True
    else:
        return False        
        
# A module definition
class Module():
    SUPPORTED_WIDTHS = (32,)  # supported bus widths
    MANDATORY_ELEMENTS = ("name", "description", "width", "registers")
    #
    # Module constructor    
    def __init__(self, json_module):
        # default values:
        self.name = ""        
        for key in json_module.keys():
            if key == "name":
                self.name = json_module[key]
            elif key == "description":
                self.description = json_module[key]
            elif key == "interface":
                self.interface = json_module[key]
            elif key == "width":
                self.width = int(json_module[key])                
            elif key == "registers":
                self.registers = [Register(json_reg, parent_module=self) for json_reg in json_module[key]]
        # check for missing mandatory elements
        for e in self.MANDATORY_ELEMENTS:
            if not hasattr(self, e):
                if(e == 'name'): self.name = '<unnamed>'
                raise ModuleError(self, "missing '%s' element" % e)            
        # check for unsupported elements
        for key in json_module.keys():
            if key not in self.MANDATORY_ELEMENTS:
                raise ModuleError(self, "unsupported element '%s'" % key)
        # check for unsupported width
        if self.width not in self.SUPPORTED_WIDTHS:
            str_supported_widths = ["'%s'" % str(w) for w in SUPPORTED_WIDTHS]
            str_supported_widths = ", ".join(str_supported_widths)
            raise ModuleError(self, "unsupported width '%d' -- HDLRegs currently supports only the following register widths: %s" % (self.width, str_supported_widths))
        # elaborate & check
        self.elaborate()   
        self.check()                 #
    # Check a module
    def check(self):
        pass
    #
    # Elaborate a module, i.e. compute values for all undefined parameters such
    # as register addresses, bit field offsets etc.
    def elaborate(self):
        # Register address sanity checks:
        addr_dict = {}
        for reg in self.registers:
            addr = reg.addressOffset
            if addr == None:
                continue            
            if addr_dict.has_key(addr):
                addr_dict[addr].append(reg)
            else:
                addr_dict[addr] = [reg]
        for key in addr_dict.keys():
            # check that no two registers have the same address offset:
            if len(addr_dict[key]) > 1:
                conflicting_regs = [r.name for r in addr_dict[key]]    
                conflicting_regs = ", ".join(conflicting_regs)           
                raise(ModuleError(self, "registers [%s] have the same addressOffset" % conflicting_regs))
        #
        # Allocate register addresses
        for r1 in self.registers:
            if r1.addressOffset == None:
                # Register has not been assigned an address offset -> compute the 
                # next available one
                candidate_addressOffset = 0x0
                while(True):
                    success = True
                    for r2 in self.registers:
                        if r2.addressOffset == candidate_addressOffset:
                            candidate_addressOffset += 4
                            success = False
                            break
                    if success:
                        break
                # print "elaboration: allocated address 0x%.8X for register %s" % (candidate_addressOffset, r1.name)
                r1.addressOffset = candidate_addressOffset
            r1.elaborate()
    # 
    # Returns the module's register with the lowest address
    def base_register(self):
        base_addr_reg = self.registers[0]
        for r in self.registers[1:]:
            if r.addressOffset < base_addr_reg.addressOffset:
                base_addr_reg = r            
        return base_addr_reg
    # 
    # Returns the module's register with the highest address
    def high_register(self):
        base_addr_reg = self.registers[0]
        for r in self.registers[1:]:
            if r.addressOffset > base_addr_reg.addressOffset:
                base_addr_reg = r            
        return base_addr_reg

# A register definition 
class Register:
    MANDATORY_ELEMENTS = ("name", "description")
    OPTIONAL_ELEMENTS = ("access", "addressOffset", "reset", "fields")
    ACCESS = ("read-write", "read-only", "write-only")  # supported access-types
    #
    # Register constructor
    def __init__(self, json_reg, parent_module):
        #
        # default values:
        self.parent_module_ = parent_module
        self.name = ""
        self.description = None
        self.access = "read-write"
        self.addressOffset = None
        self._reset = None                                
        self.fields = []        
        #
        # initialize fields from JSON    
        for key in json_reg.keys():
            if key == "name":
                self.name = json_reg[key]
            elif key == "description":
                self.description = json_reg[key]
            elif key == "access":
                self.access = json_reg[key]
            elif key == "addressOffset":
                self.addressOffset = int_from_json(json_reg[key])
            elif key == "reset":
                self._reset = int_from_json(json_reg[key])                                
            elif key == "fields":
                self.fields = [Field(json_field, self) for json_field in json_reg[key]]
        #
        # check for missing mandatory elements
        for e in self.MANDATORY_ELEMENTS:
            if not hasattr(self, e):
                if(e == 'name'): self.name = '<unnamed>'
                raise RegisterError(self, "missing '%s' element" % e)
        #
        # check for unsupported elements
        for key in json_reg.keys():
            if key not in self.MANDATORY_ELEMENTS + self.OPTIONAL_ELEMENTS:
                raise RegisterError(self, "unsupported element '%s'" % key)
        #
        # elaborate & check
        self.elaborate()   
        self.check()     
    #
    # Returns only the register's bus-writable fields
    def bus_writable_fields(self):
        result = []
        for f in self.fields:
            if f.access() == "write-only" or f.access() == "read-write":
                result += f
        return f
    #
    # Returns True if the register is bus-writable, i.e. if it has at least one bus-writable field
    def is_bus_writable(self):
        for f in self.fields:
            if f.access() == "write-only" or f.access() == "read-write":
                return True        
        return False
    #
    # Returns True if the register is bus-readable, i.e. if it has at least one bus-readable field
    def is_bus_readable(self):
        for f in self.fields:
            if f.access() == "read-only" or f.access() == "read-write":
                return True        
        return False        #
    # Returns True if the register is user-writable, i.e. if it has at least one user-writable field
    def is_user_writable(self):
        for f in self.fields:
            if f.access() == "read-only":
                return True
        return False 
    #
    # Get a registers's reset value        
    def reset(self):
        reset = self._reset  # this is the default reset value, which may be overridden on a field basis

        # if any field has a reset, then all other fields of the register are reset as well (to 0).
        if reset == None:
            for f in self.fields:
                if f.has_reset():
                    reset = 0
                    break
                
        for f in self.fields:
            if f.has_reset():
                and_mask = ~((2 ** f.bitWidth - 1) << f.bitOffset)
                reset &= and_mask
                or_mask = f.reset() << f.bitOffset
                reset |= or_mask
        return reset
    #
    # Get a registers's size
    def size(self):
        return self.parent_module_.width
    #
    # Check the register
    def check(self):
        # check name
        if not is_valid_identifier(self.name):
            raise RegisterError(self, "'%s' is not a valid identifier (it may be a reserved C or VHDL keyword)" % self.name)
        #
        # check access
        if self.access not in self.ACCESS:
            raise RegisterError(self, "'%s' is not a valid access mode" % self.access)
        #
        # check reset value
        if(self._reset != None):  #there is a reset value specified
            if(self._reset < 0 or self._reset > 2 ** self.size() - 1):
                raise(RegisterError(self, "reset value (%d) is of out range" % self._reset))
        #
        # Check that the register is wide-enough to hold all the bit fields
        bit_field_total_length = 0
        for field in self.fields:
            bit_field_total_length += field.bitWidth
        if bit_field_total_length > self.size():
            raise(RegisterError(self, "not enough bits for all fields"))
    #     
    # Elaborate the register
    def elaborate(self):
        # If the register has no fields, allocate one artificial field spanning the whole register
        if len(self.fields) == 0:
            d = dict(name=self.name, description=self.description, bitWidth=self.size())
            field = Field(d, self) 
            self.fields.append(field)            
        # Try to allocate the missing bit fields
        bits = [None] * self.size()  # list of allocated bits
        for field in self.fields:
            if field.bitOffset != None:
                for i in range(field.bitOffset, field.bitOffset + field.bitWidth):
                    if(i < 0 or i >= self.size()):
                        error("Field '%s' has bits outside of register '%s'" % (field.name, self.name))
                    # print "bit %d of register %s fixed to field %s" % (i, self.name, field.name)
                    bits[i] = field

        # print ["%d: %d" % (i, bits[i] != None) for i in range(len(bits))]

        for field in self.fields:
            if field.bitOffset == None:  # unfixed field
                success = False
                for start_pos in range(self.size()):
                    if bits[start_pos] != None:
                        continue
                    num_bits_available = 1
                    for bitOffset in range(1, self.size() - start_pos):
                        if bits[start_pos + bitOffset] != None:
                            break;
                        num_bits_available += 1
                    # print "start position %d: %d bits available" % (start_pos, num_bits_available)
                    if num_bits_available >= field.bitWidth:
                        field.bitOffset = start_pos
                        print "elaboration: allocated field %s of register %s to bit offset %d" % (field.name, self.name, start_pos)
                        for i in range(start_pos, start_pos + field.bitWidth):
                            bits[i] = field
                        # print ["%d: %d" % (i, bits[i] != None) for i in range(len(bits))]
                        success = True
                        break
                if not success:
                    error("could not allocate field %s in register %s" % (field.name, self.name))
        for field in self.fields:
            field.elaborate()    
    
# A register field        
class Field:
    MANDATORY_ELEMENTS = ("name", "description", "bitWidth")
    OPTIONAL_ELEMENTS = ("bitOffset", "reset", "access", "selfClear/Set", "userWriteStrobe")
    #
    # Field constructor    
    def __init__(self, json_field, parent_reg):
        #
        # default values:
        self.parent_reg = parent_reg
        self.name = ""
        self.description = None
        self.bitWidth = None
        self.bitOffset = None
        self._reset = None
        self._access = None
        self.selfClearSet = None
        self.userWriteStrobe = "no"
        #
        # initialize fields from JSON    
        for key in json_field.keys():
            if key == "name":
                self.name = json_field[key]
            elif key == "description":
                self.description = json_field[key]
            elif key == "bitWidth":
                self.bitWidth = json_field[key]
            elif key == "bitOffset":
                self.bitOffset = int_from_json(json_field[key])
            elif key == "reset":
                self._reset = int_from_json(json_field[key])
            elif key == "access":
                self._access = json_field[key]
            elif key == "selfClear/Set":
                self.selfClearSet = int_from_json(json_field[key])
            elif key == "userWriteStrobe":
                self.userWriteStrobe = json_field[key]
            else:
                raise FieldError(self, "unsupported element '%s'" % key)                 
        #
        # check for missing mandatory elements
        for e in self.MANDATORY_ELEMENTS:
            if not hasattr(self, e):
                if(e == 'name'): self.name = '<unnamed>'
                raise ModuleError(self, "missing '%s' element" % e)
        #
        # check for unsupported elements
        for key in json_field.keys():
            if key not in self.MANDATORY_ELEMENTS + self.OPTIONAL_ELEMENTS:
                raise RegisterError(self, "unsupported element '%s'" % key)                                
        #
        # elaborate & check
        self.elaborate()   
        self.check()     
    #
    # Checks a field (before code generation)     
    def check(self):
        #
        # check name
        if not is_valid_identifier(self.name):
            raise FieldError(self, "'%s' is not a valid identifier (it may be a reserved C or VHDL keyword)" % self.name)                
        if(self.bitWidth == None):
            raise FieldError(self, "missing bit width")
        if(self.bitWidth <= 0 or self.bitWidth > self.parent_reg.size()):
            raise FieldError(self, "bit width is out of range")        
        if(self.bitOffset != None):
            if self.bitOffset < 0 or self.bitOffset >= self.parent_reg.size():
                raise FieldError(self, "bit offset outside of register bounds")
            if self.bitOffset + self.bitWidth - 1 >= self.parent_reg.size():
                raise FieldError(self, "out of register bounds")
        if(self._reset != None):
            if(self._reset < 0):
                raise FieldError(self, "reset value out of range")
            if(self._reset > 2 ** self.bitWidth - 1):
                raise FieldError(self, "reset value out of range")
        if(self.selfClearSet != None):
            if(not self.selfClearSet in [0, 1]):
                raise FieldError(self, "selfClear/Set can be either 0 or 1 (all bits of the field are either cleared or set respectively)")
        if self.userWriteStrobe  not in ["yes", "no"]:
            raise FieldError(self, "'%s' is not a valid value for userWriteStrobe (which can be 'yes' or 'no')" % self.access)


    #
    # Returns the reset value of a field, which may be inherited from the parent register
    def reset(self):
        if self._reset == None:
            reset = self.parent_reg._reset # don't call reset() as this would create an infinite recursion
            if reset != None:
                reset >>= self.bitOffset
                and_mask = 2 ** self.bitWidth - 1
                reset &= and_mask
            return reset
        else:
            return self._reset
    #
    # Returns True if the field has a dedicated reset value, 
    # False if the reset inherits its reset value from the 
    # parent register.
    def has_reset(self):
        if self._reset == None:
            return False
        else:
            return True
    #
    # Returns the access mode of a field, which may be inherited from the parent register
    def access(self):
        if self._access == None:
            return self.parent_reg.access
        else:
            return self._access            
    #
    # Elaborate a field, i.e. compute values for all undefined parameters
    def elaborate(self):
        pass
    #
    # Returns True if the field is bus-writable
    def is_bus_writable(self):
        if self.access() == "write-only" or self.access() == "read-write":
            return True   
        return False
    #
    # Returns True if the field is bus-readable
    def is_bus_readable(self):
        if self.access() == "read-only" or self.access() == "read-write":
            return True   
        return False
    #
    # Returns True if the field is user-writable
    def is_user_writable(self):
        if self.access() == "read-only":
            return True   
        return False

    #
    # Returns True if update of the field (in read-only mode) should be conditioned by a user strobe signal.
    # Otherwise, the value of the field (in read-only mode) is updated at every clock cycle.
    def has_userWriteStrobe(self):
        if self.userWriteStrobe == "yes":
            return True
        return False
        
