#
# VHDL code blocks
#

import os
import datetime

from .shared import CodeGenerator
from .shared import VhdlDeclaration
from .shared import VhdlStatement
from .shared import VhdlCodeBlock
from .shared import indent
import code_gen.templates.vhdl as vhdl_templates
import code_gen.constants as constants

class VhdlRecord:
    #
    def __init__(self, name, description, elements):
        self.name = name
        self.description = description
        self.elements_ = elements
    #
    def add_element(self, element):
        self.elements_.append(element)
    #
    def __str__(self):
        raise NotImplementedError
    #
    def to_str(self, level):
        str = '\n'
        str += indent(level) + "-- %s\n" % self.description
        str += indent(level) + "type %s is record\n" % self.name
        level += 1
        for e in self.elements_:
            str += indent(level) + e + ";\n"
        level -= 1
        str += indent(level) + "end record;\n"
        return str
    #
    def name(self):
        return self.name
    #
    # Returns the number elements within the record
    def num_elements(self):
        return len(self.elements_)
    
class VhdlPackage:
    #
    def __init__(self, name):
        self.name = name
        self.declarations_ = []
    #
    def add_declaration(self, declaration):
        self.declarations_.append(declaration)
    #
    def __str__(self):
        str_declarations = ''
        for d in self.declarations_:
            str_declarations += d.to_str(1)
        d = dict(package_name = self.name, 
                 declarations = str_declarations,
                 json_module_name = self.name,
                 hdlregs_version = constants.HDLREGS_VERSION,
                 date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        return vhdl_templates.VHDL_PACKAGE_TEMPLATE.substitute(d)

class VhdlIfStatement:
    #
    def __init__(self, condition):
        self._condition = condition
        self.statements = []
    #
    def to_str(self, level):
        str = indent(level) + 'if %s then\n' % self._condition
        level += 1
        for s in self.statements:
            str += "%s" % s.to_str(level)
        level -= 1
        str += indent(level) + 'end if;\n'
        return str
    #   
    def __str__(self):
        raise NotImplementedError

class VhdlClockedProcess:
    #
    def __init__(self, name, clock, reset):
        self.name = name
        self.clock = clock
        self.reset = reset
        self.reset_statements = []
        self.statements = []
    #
    def to_str(self, level):
        s = indent(level) + '%s : process(%s, %s) is\n' % (self.name, self.clock, self.reset)
        s += indent(level) + 'begin\n'
        level += 1
        s += indent(level) + "if %s = '1' then\n" % self.reset
        level += 1
        for st in self.reset_statements:
            s += "%s" % st.to_str(level)
        level -= 1
        s += indent(level) + "elsif rising_edge(%s) then\n" % self.clock
        level += 1
        for st in self.statements:            
            s += st.to_str(level)
        level -= 1
        s += indent(level) + "end if;\n"
        level -= 1        
        s += indent(level) + 'end process %s;\n' % self.name
        return s
    #   
    def __str__(self):
        raise NotImplementedError
    
class VhdlAsyncProcess():
    #
    def __init__(self, name):
        self.name = name
        self.sensitivity = []
        self.statements = []        
    #
    def to_str(self, level):
        if len(self.sensitivity) > 0:
             sensitivity = "(%s)" % (','.join(self.sensitivity))
        else:
             sensitivity = ''        
        s = indent(level) + '%s : process %s is\n' % (self.name, sensitivity)
        s += indent(level) + 'begin\n'
        level += 1
        for st in self.statements:            
            s += st.to_str(level)
        level -= 1
        s += indent(level) + 'end process %s;\n' % self.name
        return s
    #
    def __str__(self):
        raise NotImplementedError

#
# VHDL component generator
#
class VhdlComponentGenerator(CodeGenerator):
    def __init__(self, module):
        #
        # Signal declarations
        signal_declarations = VhdlCodeBlock()
        for r in module.registers:
            signal_declarations.statements.append(VhdlStatement('signal %s : std_logic_vector(31 downto 0);\n' % (self.vhdl_data_signal(r))))
            if r.is_bus_writable():
                signal_declarations.statements.append(VhdlStatement("signal %s : std_logic := '0';\n" % (self.vhdl_strobe_signal(r))))
        #
        # Register-write process
        register_write_proc = VhdlClockedProcess("register_write", "clk", "rst")
        # resets
        for r in module.registers:
            if r.reset() != None:
                register_write_proc.reset_statements.append(VhdlStatement('%s <= x"%.8X";\n' % (self.vhdl_data_signal(r), r.reset())))

        # defaults
        register_write_proc.statements.append(VhdlStatement("-- defaults:\n"))
        for r in module.registers:
            if r.is_bus_writable():
                register_write_proc.statements.append(VhdlStatement("%s <= '0';\n" % self.vhdl_strobe_signal(r)))
        # self-clearing fields
        register_write_proc.statements.append(VhdlStatement("-- self-clearing fields:\n"))
        for r in module.registers:
            if r.is_bus_writable():
                reg_data_signal = self.vhdl_data_signal(r)
                for f in r.fields:
                    if f.selfClear:
                        index_high = "%s + %s - 1" % (self.bitOffset_identifier(f), self.bitWidth_identifier(f))
                        index_low = self.bitOffset_identifier(f)
                        register_write_proc.statements.append(VhdlStatement("%s(%s downto %s) <= (others => '0');\n" % (reg_data_signal, index_high, index_low)))
        # bus-write
        register_write_proc.statements.append(VhdlStatement("-- bus write:\n"))
        bus_write_block = VhdlIfStatement("cs = '1' and rnw = '0'")
        for r in module.registers:
            reg_data_signal = self.vhdl_data_signal(r)
            reg_strobe_signal = self.vhdl_strobe_signal(r)
            if r.is_bus_writable():
                register_write_block = VhdlIfStatement("addr = %s" % self.address_identifier(r))
                for f in r.fields:
                    if f.is_bus_writable():
                        index_high = "%s + %s - 1" % (self.bitOffset_identifier(f), self.bitWidth_identifier(f))
                        index_low = self.bitOffset_identifier(f)
                        register_write_block.statements.append(VhdlStatement("%s(%s downto %s) <= datain(%s downto %s);\n" % (reg_data_signal, index_high, index_low, index_high, index_low)))
                        register_write_block.statements.append(VhdlStatement("%s <= '1';\n" % (reg_strobe_signal)))
                bus_write_block.statements.append(register_write_block)
        register_write_proc.statements.append(bus_write_block)
        # user-logic write
        register_write_proc.statements.append(VhdlStatement("-- user-logic write:\n"))        
        for r in module.registers:
            for f in r.fields:
                if f.is_user_writable():
                    field_write_block = VhdlIfStatement("user2regs.%s.%s.strobe = '1'" % (r.name, f.name))
                    field_write_block.statements.append(VhdlStatement("%s(%s + %s - 1 downto %s) <= user2regs.%s.%s.value;\n" % (self.vhdl_data_signal(r), self.bitOffset_identifier(f), self.bitWidth_identifier(f), self.bitOffset_identifier(f), r.name, f.name)))
                    register_write_proc.statements.append(field_write_block)
        #
        # Bus-read process
        bus_read_proc = VhdlAsyncProcess("bus_read")
        bus_read_proc.sensitivity.append('cs')
        bus_read_proc.sensitivity.append('rnw')
        bus_read_proc.sensitivity.append('addr')
        bus_read_proc.statements.append(VhdlStatement("dataout <= (others => 'X'); -- default\n"))
        cs_block = VhdlIfStatement("cs = '1' and rnw = '1'")
        for r in module.registers:
            if r.is_bus_readable():
                bus_read_proc.sensitivity.append(self.vhdl_data_signal(r))
                reg_read_block = VhdlIfStatement("addr = %s" % self.address_identifier(r))
                for f in r.fields:
                    if f.is_bus_readable():
                        index_high = "%s + %s - 1" % (self.bitOffset_identifier(f), self.bitWidth_identifier(f))
                        index_low = self.bitOffset_identifier(f)
                        reg_read_block.statements.append(VhdlStatement("dataout(%s downto %s) <= %s(%s downto %s);\n" % (index_high, index_low, self.vhdl_data_signal(r), index_high, index_low)))
                cs_block.statements.append(reg_read_block)                
        bus_read_proc.statements.append(cs_block)
        #
        # Concurrent signal assignments
        concurrent_signal_assignments = VhdlCodeBlock()
        for r in module.registers:
            for f in r.fields:
                if f.is_bus_writable():
                    concurrent_signal_assignments.statements.append(VhdlStatement("regs2user.%s.%s.value <= %s(%s + %s - 1 downto %s);\n" % (r.name, f.name, self.vhdl_data_signal(r), self.bitOffset_identifier(f), self.bitWidth_identifier(f), self.bitOffset_identifier(f))))
                    concurrent_signal_assignments.statements.append(VhdlStatement("regs2user.%s.%s.strobe <= %s;\n" % (r.name, f.name, self.vhdl_strobe_signal(r))))                   
        d = dict(entity_name = self.vhdl_entity_name(module),
                 signal_declarations = signal_declarations.to_str(1),
                 package_name = self.vhdl_package_name(module),
                 register_write_proc = register_write_proc.to_str(1),
                 concurrent_signal_assignments = concurrent_signal_assignments.to_str(1),
                 register_read_proc = bus_read_proc.to_str(1),
                 json_module_name = module.name,
                 hdlregs_version = constants.HDLREGS_VERSION,
                 date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        self._code = vhdl_templates.VHDL_COMPONENT_TEMPLATE.substitute(d)        
    #
    # Save the generated VHDL component to a file
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self._code)    

#
# VHDL package generator
#
class VhdlPackageGenerator(CodeGenerator):
    def __init__(self, module):
        vhdl_package = VhdlPackage(self.vhdl_package_name(module))
        # Interface record types     
        user2regs = VhdlRecord('t_user2regs', 'User-logic -> register file interface', [])
        regs2user = VhdlRecord('t_regs2user', 'Register file -> user-logic interface', [])
        # Register address offsets
        for r in module.registers:
            vhdl_package.add_declaration(VhdlDeclaration('constant %s : std_logic_vector(31 downto 0) := x"%.8X";\n' % (self.address_identifier(r), r.addressOffset)))
        # Lowest address in register file 
        identifier = module.name.upper() + "_REGS_BASEADDR"
        base_register_identifier = self.address_identifier(module.base_register())
        vhdl_package.add_declaration(VhdlDeclaration('constant %s : std_logic_vector(31 downto 0) := %s; -- lowest register address\n' % (identifier, base_register_identifier)))        
        # Highest address in register file
        identifier = module.name.upper() + "_REGS_HIGHADDR"
        high_register_identifier = self.address_identifier(module.high_register())
        vhdl_package.add_declaration(VhdlDeclaration('constant %s : std_logic_vector(31 downto 0) := %s; -- highest register address\n' % (identifier, high_register_identifier)))
        # Field constants:
        for r in module.registers:
            for f in r.fields:
                vhdl_package.add_declaration(self.to_vhdl_constants(f))
        # Field record types
        field_types = ''
        for r in module.registers:
            for f in r.fields:
                description = "Field '%s' of register '%s' (%s)" % (f.name, r.name, f.access())
                elements = []
                elements.append("value : std_logic_vector(%s - 1 downto 0)" % (self.bitWidth_identifier(f)))
                elements.append("strobe : std_logic")
                record = VhdlRecord(self.vhdl_record_name(f), description, elements)
                vhdl_package.add_declaration(record)       
        # Register record types (XXX_regs2user and/or XXX_user2regs)
        for r in module.registers:
            records = self.to_vhdl_records(r)
            for record in records:
                if record.name.endswith('user2regs'):
                    user2regs.add_element(r.name + ": " + record.name)
                if record.name.endswith('regs2user'):
                    regs2user.add_element(r.name + ": " + record.name)
                vhdl_package.add_declaration(record)
        # Add dummy signals in case of empty records, as these are not allowed in VHDL
        if 0 == user2regs.num_elements():
            user2regs.add_element("dummy : std_logic")
        if 0 == regs2user.num_elements():
            regs2user.add_element("dummy : std_logic")
        #
        vhdl_package.add_declaration(user2regs)        
        vhdl_package.add_declaration(regs2user)
        self._code = str(vhdl_package)
    #
    # Generate VHDL constants for a field
    def to_vhdl_constants(self, field):
        field_name = field.name.upper()
        field_mask = (2 ** field.bitWidth - 1) << field.bitOffset
        code_block = VhdlCodeBlock()
        code_block.statements.append(VhdlStatement("-- Field '%s' of register '%s'\n" % (field.name, field.parent_reg.name)))
        code_block.statements.append(VhdlDeclaration("constant %s : natural := %d;\n" % (self.bitOffset_identifier(field), field.bitOffset)))
        code_block.statements.append(VhdlDeclaration("constant %s : natural := %d;\n" % (self.bitWidth_identifier(field), field.bitWidth)))
        code_block.statements.append(VhdlDeclaration('constant %s : std_logic_vector(31 downto 0) := x"%.8X";\n' % (self.bitMask_identifier(field), field_mask)))
        return code_block    
    #
    # Generate VHDL record types for a register
    def to_vhdl_records(self, register):
        records = []
        # user-writable fields:
        name = "t_%s_user2regs" % (register.name)
        description = "Register '%s'" % register.name
        elements = []
        for f in register.fields:
            if f.access() == "read-only":
                elements.append('%s : %s' % (f.name, self.vhdl_record_name(f)))
        if len(elements) > 0:
            records.append(VhdlRecord(name, description, elements))
        # bus-writable fields:
        name = "t_%s_regs2user" % (register.name)
        description = "Register '%s'" % register.name
        elements = []
        for f in register.fields:
            if f.access() == "read-write" or f.access() == "write-only":
                elements.append('%s : %s' % (f.name, self.vhdl_record_name(f)))       
        if len(elements) > 0:
            records.append(VhdlRecord(name, description, elements))        
        return records 
    #
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self._code)
    
