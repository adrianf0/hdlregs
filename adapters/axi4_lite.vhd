--------------------------------------------------------------------------------
-- HDLRegs adapter for AXI4 Lite. 
--------------------------------------------------------------------------------
-- Copyright (c) 2018, Fastree3D
-- All rights reserved.
-- 
-- Redistribution and use in source and binary forms, with or without
-- modification, are permitted provided that the following conditions are met: 
-- 
-- 1. Redistributions of source code must retain the above copyright notice, this
--    list of conditions and the following disclaimer. 
-- 2. Redistributions in binary form must reproduce the above copyright notice,
--    this list of conditions and the following disclaimer in the documentation
--    and/or other materials provided with the distribution. 
-- 
-- THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
-- ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
-- WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
-- DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
-- ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
-- (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
-- LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
-- ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
-- (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
-- SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-- 
-- The views and conclusions contained in the software and documentation are those
-- of the authors and should not be interpreted as representing official policies, 
-- either expressed or implied, of the FreeBSD Project.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity axi4_adapter is
  port(
    -- AXI4 Lite interface
    axi_clk     : in  STD_LOGIC;
    axi_rst_n   : in  STD_LOGIC;
    axi_awvalid : in  STD_LOGIC;
    axi_awready : out STD_LOGIC;
    axi_awaddr  : in  STD_LOGIC_VECTOR(31 downto 0);
    axi_awprot  : in  STD_LOGIC_VECTOR(2 downto 0);
    axi_wvalid  : in  STD_LOGIC;
    axi_wready  : out STD_LOGIC;
    axi_wdata   : in  STD_LOGIC_VECTOR(31 downto 0);
    axi_wstrb   : in  STD_LOGIC_VECTOR(3 downto 0);
    axi_bvalid  : out STD_LOGIC;
    axi_bready  : in  STD_LOGIC;
    axi_bresp   : out STD_LOGIC_VECTOR(1 downto 0);
    axi_arvalid : in  STD_LOGIC;
    axi_arready : out STD_LOGIC;
    axi_araddr  : in  STD_LOGIC_VECTOR(31 downto 0);
    axi_arprot  : in  STD_LOGIC_VECTOR(2 downto 0);
    axi_rvalid  : out STD_LOGIC;
    axi_rready  : in  STD_LOGIC;
    axi_rdata   : out STD_LOGIC_VECTOR(31 downto 0);
    axi_rresp   : out STD_LOGIC_VECTOR(1 downto 0);

    -- register file interface
    regs_clk     : out STD_LOGIC;
    regs_rst     : out STD_LOGIC;
    regs_addr    : out STD_LOGIC_VECTOR(31 downto 0);
    regs_cs      : out STD_LOGIC;
    regs_rnw     : out STD_LOGIC;
    regs_datain  : out STD_LOGIC_VECTOR(31 downto 0);
    regs_dataout : in  STD_LOGIC_VECTOR(31 downto 0)
    );
end entity axi4_adapter;

architecture RTL of axi4_adapter is
  type WRITE_FSM_STATE is (IDLE, WRITE_RESPONSE);
  signal write_state, write_state_n : WRITE_FSM_STATE;
  
  type READ_FSM_STATE is (IDLE, WAIT_FOR_RREADY);
  signal read_state, read_state_n : READ_FSM_STATE;
  signal rdata                    : STD_LOGIC_VECTOR(axi_rdata'RANGE);

  signal rnw : STD_LOGIC;               --internal regs_rnw signal
  signal cs  : STD_LOGIC;               --internal regs_cs  signal
begin
  regs_clk <= axi_clk;
  regs_rst <= not axi_rst_n;

  --write has priority over readout
  --AXI addresses single bytes, thus address needs to be shifted by 2
  regs_addr <= ("00" & axi_awaddr(axi_awaddr'HIGH downto 2)) when axi_awvalid = '1' else ("00" & axi_araddr(axi_araddr'HIGH downto 2));
  rnw       <= '0'        when axi_wvalid = '1'  else '1';
  regs_rnw  <= rnw;
  cs        <= axi_awvalid or axi_arvalid;
  regs_cs   <= cs;

  --write channel
  axi_awready <= axi_awvalid and axi_wvalid;
  axi_wready  <= '1';
  regs_datain <= axi_wdata;

  --write response channel
  axi_bresp  <= "00";                   --OKAY

  write_fsm_comb : process(all) is
  begin
    -- default
    axi_bvalid <= '0';
    write_state_n <= write_state;

    case(write_state) is
      when IDLE =>
        if ( axi_awvalid = '1' and axi_wvalid = '1') then
          axi_bvalid <= '1';
          if( axi_bready = '0') then
            write_state_n <= WRITE_RESPONSE;
          end if;
        end if;
      when WRITE_RESPONSE =>
        axi_bvalid <= '1';
        if axi_bready = '1' then
          write_state_n <= IDLE;
        end if;
    end case;
  end process;

  write_fsm_seq : process (axi_clk, axi_rst_n) is
  begin
    if(axi_rst_n = '0') then
      write_state <= IDLE;
    elsif rising_edge(axi_clk) then
      write_state <= write_state_n;
    end if;
  end process;
  
  --read channel
  axi_arready <= '0' when axi_awvalid = '1' else '1';

  read_fsm_comb : process(all) is
  begin
    --default
    axi_rdata    <= regs_dataout;
    axi_rvalid   <= '0';
    read_state_n <= read_state;
    
    case read_state is
      when IDLE =>
        if(axi_wvalid = '0') then       --write access has priority
          axi_rvalid <= axi_arvalid;
        end if;

        if(axi_wvalid = '0' and axi_arvalid = '1') then
          if(axi_rready = '0') then
            read_state_n <= WAIT_FOR_RREADY;
          end if;
        end if;

      when WAIT_FOR_RREADY =>
        axi_rdata  <= rdata;
        axi_rvalid <= '0';

        if(axi_rready = '1') then
          read_state_n <= IDLE;
        end if;
    end case;
  end process read_fsm_comb;

  read_fsm_seq : process(axi_clk, axi_rst_n) is
  begin
    if(axi_rst_n = '0') then
      read_state <= IDLE;
    elsif rising_edge(axi_clk) then
      read_state <= read_state_n;
      if(cs = '1' and rnw = '1') then
        rdata <= regs_dataout;
      end if;
    end if;
  end process;

  --read response channel
  axi_rresp <= "00";                    --OKAY

end architecture RTL;
