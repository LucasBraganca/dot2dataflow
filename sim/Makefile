

SRCS=""

LD_FLAGS= -LDFLAGS -Wl,--no-as-needed
build:
	vcs -notice -sverilog -nc -V +vcs+lic+wait -full64 -debug_pp -Mupdate -override_timescale=1ps/1ps $(LD_FLAGS)  $(SRCS)
sim: build
	./simv -ucli -do vcs_run.tcl
wave: sim
	dve -vpd `find . -name inter.vpd` -full64&
clean:
	rm -rf csrc/ DVEfiles/ simv* *.vpd ucli.key
