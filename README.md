About HDLRegs
=============

HDLRegs is an open-source HDL register file generator written in the Python programming language. It takes a register specification in JSON format, 
and generates the following output files:

  * VHDL package
  * Synthesizable VHDL component
  * C header
  * HTML documentation

Register Specification
======================

The register structure for a given module (e.g. UART, timer etc.) is specified in a text-file formatted according to the JavaScript Object Notation (JSON).
Here is an example register specification showcasing a few capabilities of HDLRegs:

    {
      "name"        : "example",
      "description" : "An example module demonstrating the capabilities of HDLRegs",
      "width"       : 32,
      "registers":
        [
            {
              "name"          : "version",
              "description"   : "Version register implemented using read-only fields",
              "access"        : "read-only",
              "fields"        :
                  [
                    {
                        "name"            : "high",
                        "description"     : "high-byte of the version number",
                        "bitWidth"        : 8,
			"userWriteStrobe" : "yes",
                        "reset"           : 1
                    },                            
                    {
                        "name"            : "low",
                        "description"     : "low-byte of the version number",
                        "bitWidth"        : 8,
                        "reset"           : 0                        
                    }
                  ]                        
            },
            
            {
              "name"          : "control",
              "description"   : "Control register with a mix of read/write, write-only and read-only fields",
              "access"        : "read-write",
              "addressOffset" : "0x100",
              "reset"         : 0,
              "fields"        :
                  [
                    {
                        "name"          : "reset",
                        "description"   : "reset the module",
                        "bitOffset"     : 31,
                        "bitWidth"      : 1,
                        "reset"         : 1
                    },
                    {
                        "name"          : "done",
                        "description"   : "signals that the processing has completed",
                        "bitWidth"      : 1,
                        "access"        : "read-only"
                    },                                      
                    {
                        "name"          : "start",
                        "description"   : "start the processing",
                        "bitWidth"      : 1,
                        "access"        : "write-only",
                        "bitOffset"     : 0,
                        "selfClear/Set" : 0
                    }                  
                  ]          
            }
        ]
    }    

Reset
-----
If "reset" attribute is defined, the tool generates a register with an asynchronous reset. Otherwise, reset is not generated. If any field of a register has a reset attribute defined, then all other fields of the register are reset as well (to '0').

Self Clear/Set
--------------
If defined, value of "selfClear/Set" attribute defines whether a field of the register is cleared (0) or set (1). In "read-write" and "write-only" access mode, the clear/set operation occurs at the write operation. In "read-only" access mode, the clear/set takes place during read operation.  

You can have a look at the [example configuration](example/example.json) and the generated files in the [example](example/) directory.

Usage
=====
hdlregs.py [-h] [-novhdl] [-vhdl_output_dir VHDL_OUTPUT_DIR] [-noc]
           [-c_output_dir C_OUTPUT_DIR] [-nohtml]
           [-html_output_dir HTML_OUTPUT_DIR] [--version]
           register_definition_file

HDLRegs is an open-source HDL register file generator written in the Python programming language. 
It takes a register specification in JSON format and generates the following output files:
 * VHDL package
 * Synthesizable VHDL component
 * C header
 * HTML documentation.

positional arguments:
  register_definition_file
                        register definition file in JSON format

optional arguments:
  -h, --help            show this help message and exit
  -novhdl               prevents VHDL output generation
  -vhdl_output_dir VHDL_OUTPUT_DIR
                        path to the VHDL output directory
  -noc                  prevents C output generation
  -c_output_dir C_OUTPUT_DIR
                        path to the C output directory
  -nohtml               prevents html output generation
  -html_output_dir HTML_OUTPUT_DIR
                        path to the HTML output directory
  --version             show program's version number and exit

Compatibility
=============

The VHDL register file component generated by HDLRegs has a generic host processor interface, which consists of the following ports:

    clk     : in  std_logic;                     -- system clock
    rst     : in  std_logic;                     -- asynchronous, high-active
    addr    : in  std_logic_vector(31 downto 0); -- read/write address
    cs      : in  std_logic;                     -- chip select
    rnw     : in  std_logic;                     -- read (1) or write (0)
    datain  : in  std_logic_vector(31 downto 0); -- write data
    dataout : out std_logic_vector(31 downto 0); -- read data
    
VHDL adapter components are provided for connecting an HDLRegs-generated register file to Xilinx IPIF and AXI4-Lite interfaces.

Limitations
===========

HDLRegs development started in the summer of 2013, and although it has already been used with great success in a commercial project, I still consider it work in progress.

The most important limitation is that it currently supports only 32-bit wide registers files.
