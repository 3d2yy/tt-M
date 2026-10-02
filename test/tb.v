`timescale 1ns/1ps
module tb;
    reg clk = 0;
    reg rst_n = 0;
    reg ena = 1;
    reg [7:0] ui_in = 0;
    reg [7:0] uio_in = 0;
    wire [7:0] uo_out, uio_out, uio_oe;
    tt_um_3d2yy_correlator dut (
`ifdef GL_TEST
        .VPWR(1'b1), .VGND(1'b0),
`endif
        .ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in),
        .uio_out(uio_out), .uio_oe(uio_oe),
        .ena(ena), .clk(clk), .rst_n(rst_n)
    );
    initial begin
        $dumpfile("tb.vcd");
        $dumpvars(0, tb);
    end
endmodule
