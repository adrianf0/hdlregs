#
# HTML code generator
#

import datetime
import constants
import structures
import code_gen.templates.html as html_templates
from .shared import indent

class HtmlGenerator():
    def __init__(self, module):       
        # HTML overview list
        
        html_overview = indent(4) + '<table id="overview">\n'
        html_cell_class = 'even'
        for r in module.registers:
            html_overview += indent(5) + '<tr><td class="%s"><a class="overview" href="#%s">%s</d></td></tr>\n' % (html_cell_class, r.name, r.name)
            # cycle cell colors:
            if html_cell_class == 'even': html_cell_class = 'odd'
            elif html_cell_class == 'odd': html_cell_class = 'even'
        html_overview += indent(4) + '</table>\n'        
        # HTML detailed description
        html_registers = ""
        for r in module.registers:
            html_registers += self.to_html(r)
        d = dict(module_name=module.name,
                 date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                 hdlregs_version=constants.HDLREGS_VERSION,
                 registers=html_registers,
                 overview=html_overview)
        self._code = html_templates.HTML_DOC_TEMPLATE.substitute(d)    
        
    def to_html(self, element):
        # Register -> HTML
        if isinstance(element, structures.Register):
            r = element
            fields_sorted = sorted(r.fields, key=lambda field: field.bitOffset, reverse=True)  # sort fields in order of descending bit offset
            fields_html = ""
            for f in fields_sorted:
                fields_html += self.to_html(f)
            str_addressOffset = "0x%.8X" % r.addressOffset
            d = dict(register_name=r.name,
                     register_description=r.description,
                     register_addr_offset=str_addressOffset,
                     register_fields=fields_html)
            return html_templates.HTML_REGISTER_TEMPLATE.substitute(d)
        # Field -> HTML
        elif isinstance(element, structures.Field):
            if element.bitWidth == 1:
                field_range = element.bitOffset
            else:
                field_range = "%d:%d" % (element.bitOffset + element.bitWidth - 1, element.bitOffset)
            #
            access = element.access()
            if access == "read-write":
                field_access = "RW"
            elif access == "read-only":
                field_access = "R"
            elif access == "write-only":
                field_access = "W"
            #
            if element.selfClear:
                field_selfClear = "Self-clearing"
            else:
                field_selfClear = "&nbsp;"
            #
            d = dict(field_range=field_range,
                     field_name=element.name,
                     field_access=field_access,
                     field_reset=element.reset(),
                     field_description=element.description,
                     field_selfClear=field_selfClear)
            return html_templates.HTML_REGISTER_FIELD_TEMPLATE.substitute(d)            
        
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self._code)
