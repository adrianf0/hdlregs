# ------------------------------------------------------------------------------
# String templates for HTML documents
#

from string import Template

HTML_DOC_TEMPLATE = Template("""
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Registers in '$module_name' module</title>
    <style type="text/css" media="screen,print">

    body, html{
        margin:0;
        padding:0;    
        font-family:Verdana,Geneva,Arial,sans-serif;        
        font-size: small;
    }

    h1 {
        margin:0;
    }

    /* registers table */
    table.register { 
        border: thin solid #aaa; 
        border-collapse: collapse;
        border-spacing:0;
        }    
    table.register tr.Header{
        background-color: #edf0f9;
        height: 2em;
        font-size: 125%;
        }
    table.register td.RegisterAddr {
        width: 10em; 
        text-align: left; 
        font-weight: bold; 
        padding: 5px;
        }
    table.register td.RegisterName {
        font-weight: bold; 
        padding: 5px;  
        }
    table.register td.RegisterDescription {
        border-bottom: thin solid #aaa; 
        padding: 5px; 
        padding-top: 0; 
        background-color: #edf0f9;
        }
    table.register td.BitFieldIndex {
        padding-right: 1em; 
        padding-top: 3px; 
        width: 5em; text-align: right; 
        vertical-align: top; 
        border-top: thin solid #aaa; 
        }
    table.register td.BitFieldName {
        width: 25em; 
        text-align: left; 
        border-top: thin solid #aaa; 
        font-weight: bold; 
        }
    table.register td.BitFieldMode {
        width: 3em; 
        text-align: left; 
        border-top: thin solid #aaa; 
        }
    table.register td.BitFieldReset {
        text-align: left;
        vertical-align: top; 
        border-top: thin solid #aaa; 
        }  
        
    /* overview table format */
    table#overview{
        width: 200px;
        border: none;
    }    
    table#overview tr {
        height: 1.5em;
    }        
    table#overview td {
        padding-left: 1em;
    }        
    .even{
        background-color: #eee;
    }
    a.overview {
        color: black;
        text-decoration: none;
    }    
        
    #footer p {
        margin:0;
    }
    
    #sidebar ul {
        margin:0;
        padding:0;
        list-style:none;
    }    
    
    div#wrap {
        width:750px;
        margin:1em auto;
        border: solid 2px #aaa;
        padding: 5px;
        -webkit-border-radius: 10px;
        -moz-border-radius: 10px;
        -o-border-radius: 10px;
        -ms-border-radius: 10px;
        -khtml-border-radius: 10px;
        border-radius: 3px;        
        
    }    
    
    div#header {
        padding:10px 10px;
        /*border-width: 0 0 0.1em 0;*/
        /*border-style: double;*/
        border-color: #aaa;        
    }        
    
    div#footer {
        clear:both; /*push footer down*/
        padding:5px 10px;
        text-align:center;
        border-width: 0.1em 0 0 0;
        border-style: double;
        border-color: #aaa;        
        font-size: x-small;
        
    }        

    div#sidebar {
        width:200px; /* subtract padding from actual width*/
        float:left;
        padding:10px;        
    }    
    
    div#main {
        width: 510px; /* subtract padding from actual width*/
        float:right;
        padding:10px;
    }        
    
    </style>
    
</head>
<body>

    <div id="wrap">

        <div id="header">
            <h1>Registers in '$module_name' module</h1>
        </div>

        <div id="sidebar">
            <h2>Overview</h2>
$overview
        </div>
        
        <div id="main">
            <h2>Detailed description</h2>
            $registers           
        </div>
        
        <div id="footer">
        <p>Generated: $date_time by <a href="https://github.com/noasic/hdlregs">HDLRegs</a> version $hdlregs_version</p>
        </div>
    </div>

</body>
</html>""")    

# ------------------------------------------------------------------------------

HTML_REGISTER_TEMPLATE = Template("""    
  <p>
  <a id="$register_name"></a>
  <table class="register">
    <tr class="Header">
      <td class="RegisterName" colspan="3">$register_name</td>    
      <td class="RegisterAddr">$register_addr_offset</td>          
    </tr>
    <tr>
      <td class="RegisterDescription" colspan="4">$register_description</td>          
    </tr>
    $register_fields   
  </table>
  </p>""")  # html_register_template

# ------------------------------------------------------------------------------

HTML_REGISTER_FIELD_TEMPLATE = Template("""
    <tr class="BitField">
      <td class="BitFieldIndex" rowspan="2">[$field_range]</td>
      <td class="BitFieldName">$field_name</td>
      <td class="BitFieldMode">$field_access</td>
      <td class="BitFieldReset">Reset: $field_reset</td>            
    </tr>
    <tr>
      <td class="BitFieldDescription">$field_description</td>
      <td>&nbsp;</td>
      <td class="BitFieldSelfClear">$field_selfClear</td>
    </tr>  
""")  # html_register_field_template
