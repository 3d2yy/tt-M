-- SPDX-License-Identifier: Apache-2.0
-- Eight-tap signed correlator. A command is accepted on a rising clock edge
-- only when ena='1', ready='1' and uio_in(0)='1'. All inputs are synchronous.
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tt_um_3d2yy_correlator is
    port (
        ui_in   : in  std_logic_vector(7 downto 0);
        uo_out  : out std_logic_vector(7 downto 0);
        uio_in  : in  std_logic_vector(7 downto 0);
        uio_out : out std_logic_vector(7 downto 0);
        uio_oe  : out std_logic_vector(7 downto 0);
        ena     : in  std_logic;
        clk     : in  std_logic;
        rst_n   : in  std_logic
    );
end entity;

architecture rtl of tt_um_3d2yy_correlator is
    -- Tap zero is the NEWEST sample. Packed vectors avoid inter-file VHDL types.
    signal history   : std_logic_vector(63 downto 0);
    signal weights   : std_logic_vector(31 downto 0);
    signal weight_ix : unsigned(2 downto 0);
    signal tap       : unsigned(2 downto 0);
    signal filled    : unsigned(3 downto 0);
    signal threshold : unsigned(13 downto 0);
    signal acc       : signed(14 downto 0);
    signal result    : signed(14 downto 0);
    signal busy      : std_logic;
    signal valid     : std_logic;
    signal hit       : std_logic;
    signal ready     : std_logic;
    signal selected_x : signed(7 downto 0);
    signal selected_h : signed(3 downto 0);
    signal product    : signed(11 downto 0);
    signal next_acc   : signed(14 downto 0);
    signal read_result : signed(15 downto 0);
begin
    -- Constant slices are accepted by the GHDL versions used in the flow.
    with tap select selected_x <=
        signed(history(7 downto 0)) when "000",
        signed(history(15 downto 8)) when "001",
        signed(history(23 downto 16)) when "010",
        signed(history(31 downto 24)) when "011",
        signed(history(39 downto 32)) when "100",
        signed(history(47 downto 40)) when "101",
        signed(history(55 downto 48)) when "110",
        signed(history(63 downto 56)) when others;
    with tap select selected_h <=
        signed(weights(3 downto 0)) when "000",
        signed(weights(7 downto 4)) when "001",
        signed(weights(11 downto 8)) when "010",
        signed(weights(15 downto 12)) when "011",
        signed(weights(19 downto 16)) when "100",
        signed(weights(23 downto 20)) when "101",
        signed(weights(27 downto 24)) when "110",
        signed(weights(31 downto 28)) when others;
    -- One shared 8 x 4 signed multiplier and one 15-bit accumulator.
    product <= selected_x * selected_h;
    next_acc <= acc + resize(product, acc'length);

    ready <= ena and not busy and rst_n;
    read_result <= resize(result, read_result'length);
    uo_out <= std_logic_vector(read_result(15 downto 8)) when uio_in(4)='1'
              else std_logic_vector(read_result(7 downto 0));
    uio_oe <= x"E0";
    uio_out <= hit & valid & ready & "00000";

    process(clk, rst_n)
    begin
        if rst_n='0' then
            history <= (others => '0');
            -- Time-order pattern: +1,+1,-1,-1,+1,-1,+1,-1.
            -- Coefficients are reversed because tap zero is newest.
            weights <= x"11FF1F1F";
            weight_ix <= (others => '0');
            tap <= (others => '0');
            filled <= (others => '0');
            threshold <= to_unsigned(160, threshold'length);
            acc <= (others => '0');
            result <= (others => '0');
            busy <= '0';
            valid <= '0';
            hit <= '0';
        elsif rising_edge(clk) then
            if ena='1' then
                if busy='1' then
                    acc <= next_acc;
                    if tap=7 then
                        result <= next_acc;
                        valid <= '1';
                        busy <= '0';
                        -- Padded windows are calculated but cannot trigger.
                        if filled=8 and next_acc >= signed('0' & threshold) then
                            hit <= '1';
                        else
                            hit <= '0';
                        end if;
                    else
                        tap <= tap + 1;
                    end if;
                elsif uio_in(0)='1' then
                    case uio_in(3 downto 1) is
                        when "000" => -- SAMPLE: signed two's-complement byte
                            history <= history(55 downto 0) & ui_in;
                            if filled < 8 then
                                filled <= filled + 1;
                            end if;
                            tap <= (others => '0');
                            acc <= (others => '0');
                            busy <= '1';
                            valid <= '0';
                            hit <= '0';
                        when "001" => -- INDEX: coefficient address 0..7
                            weight_ix <= unsigned(ui_in(2 downto 0));
                        when "010" => -- WEIGHT: signed low nibble -8..7
                            case weight_ix is
                                when "000" => weights(3 downto 0) <= ui_in(3 downto 0);
                                when "001" => weights(7 downto 4) <= ui_in(3 downto 0);
                                when "010" => weights(11 downto 8) <= ui_in(3 downto 0);
                                when "011" => weights(15 downto 12) <= ui_in(3 downto 0);
                                when "100" => weights(19 downto 16) <= ui_in(3 downto 0);
                                when "101" => weights(23 downto 20) <= ui_in(3 downto 0);
                                when "110" => weights(27 downto 24) <= ui_in(3 downto 0);
                                when others => weights(31 downto 28) <= ui_in(3 downto 0);
                            end case;
                        when "011" => -- THRESHOLD_LOW
                            threshold(7 downto 0) <= unsigned(ui_in);
                        when "100" => -- THRESHOLD_HIGH (six low bits)
                            threshold(13 downto 8) <= unsigned(ui_in(5 downto 0));
                        when "101" => -- CLEAR: keep coefficients and threshold
                            history <= (others => '0');
                            filled <= (others => '0');
                            acc <= (others => '0');
                            result <= (others => '0');
                            valid <= '0';
                            hit <= '0';
                        when "110" => -- ACK: clear flags, keep last result
                            valid <= '0';
                            hit <= '0';
                        when others => null; -- NOP
                    end case;
                end if;
            end if;
        end if;
    end process;
end architecture;
