.DEFAULT_GOAL := sim
SIM ?= icarus
TOPLEVEL_LANG := verilog
REPO_ROOT := $(abspath ..)
TOPLEVEL := tb
MODULE := test_correlator
SIM_BUILD := sim_build/rtl

ifeq ($(GATES),yes)
COMPILE_ARGS += -DGL_TEST -DFUNCTIONAL -DUSE_POWER_PINS -DSIM
COMPILE_ARGS += -DUNIT_DELAY=\#1
VERILOG_SOURCES := $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
VERILOG_SOURCES += $(CURDIR)/gate_level_netlist.v
SIM_BUILD := sim_build/gl
else
VERILOG_SOURCES := $(REPO_ROOT)/build/correlator.v
$(REPO_ROOT)/build/correlator.v: $(REPO_ROOT)/src/tt_um_3d2yy_correlator.vhdl $(REPO_ROOT)/scripts/build_verilog.sh
	bash $(REPO_ROOT)/scripts/build_verilog.sh
endif
VERILOG_SOURCES += $(CURDIR)/tb.v
include $(shell cocotb-config --makefiles)/Makefile.sim
