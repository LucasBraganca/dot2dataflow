from veriloggen import *

from make_dataflow import make_dataflow

def make_producer():
    m = Module('producer')
    data_width = m.Parameter('data_width', 8)
    fail_rate = m.Parameter('fail_rate', 0)
    is_const = m.Parameter('is_const', 'false')
    initial_value = m.Parameter('initial_value', 0)
    clk = m.Input('clk')
    rst = m.Input('rst')
    req = m.Input('req')
    ack = m.OutputReg('ack')
    dout = m.OutputReg('dout', data_width)
    count = m.OutputReg('count', 32)

    dout_next = m.Reg('dout_next', data_width)
    stop = m.Reg('stop')
    randd = m.Real('randd')
    m.Always(Posedge(clk))(
        If(rst)(
            dout(initial_value),
            dout_next(initial_value),
            ack(0),
            count(0),
            stop(0),
            randd(EmbeddedCode('$abs($random%101)+1')),
        ).Else(
            ack(0),
            randd(EmbeddedCode('$abs($random%101)+1')),
            stop(Mux(randd > fail_rate, 0, 1)),
            If(req & ~ack & Not(stop))(
                ack(1),
                dout(dout_next),
                If(is_const == "false")(
                    dout_next.inc()
                ),
                count.inc()
            )
        )
    )

    return m


def make_consumer():
    m = Module('consumer')
    data_width = m.Parameter('data_width', 8)
    fail_rate = m.Parameter('fail_rate', 0)
    clk = m.Input('clk')
    rst = m.Input('rst')
    req = m.OutputReg('req')
    ack = m.Input('ack')
    din = m.Input('din', data_width)
    count = m.OutputReg('count', 32)
    stop = m.Reg('stop')
    randd = m.Real('randd')
    m.Always(Posedge(clk))(
        If(rst)(
            req(0),
            count(0),
            stop(0),
            randd(EmbeddedCode('$abs($random%101)+1'))
        ).Else(
            req(0),
            randd(EmbeddedCode('$abs($random%101)+1')),
            stop(Mux(randd > fail_rate, 0, 1)),
            If(Not(stop))(
                req(1)
            ),
            If(ack)(
                count.inc()
            )
        )
    )
    return m

def make_test_bench(dataflow_dot):
    dataflow = make_dataflow(dataflow_dot)
    m = Module('test_bench_'+dataflow_dot.name)
    data_width = m.Localparam('data_width', 8)
    fail_rate_producer = m.Localparam('fail_rate_producer', 0)
    fail_rate_consumer = m.Localparam('fail_rate_consumer', 0)
    is_const = m.Localparam('is_const', 'false')
    initial_value = m.Localparam('initial_value', 0)

    max_data_size = m.Localparam('max_data_size', 5000)

    clk = m.Reg('clk')
    rst = m.Reg('rst')

    df_ports = dataflow.get_ports()
    ports = m.get_vars()
    for p in df_ports:
        if p not in ports:
            m.Wire(p, df_ports[p].width)

    ports = m.get_vars()
    count_producer = m.Wire('count_producer', 32)
    count_consumer = m.Wire('count_consumer', 32)
    count_clock = m.Real('count_clock', 32)

    simulation.setup_clock(m, clk, hperiod=1)
    simulation.setup_reset(m, rst, period=1)

    m.Always(Posedge(clk))(
        If(rst)(
            count_clock(0)
        ),
        count_clock.inc(),
        If(count_consumer >= max_data_size)(
            Display('test_bench_'+dataflow_dot.name + " throughput: %5.2f%%", Mul(100.0, (count_consumer / (count_clock / 4.0)))),
            Finish()
        )
    )
    p = make_producer()
    c = make_consumer()
    for no in dataflow_dot.nodes:
        op = str.lower(dataflow_dot.nodes[no]['op'])
        if op == 'in':
            param = [('data_width', data_width), ('fail_rate', fail_rate_producer), ('initial_value', initial_value),
                     ('is_const', is_const)]
            con = [('clk', clk), ('rst', rst), ('req', ports['din_req_%s' % no]), ('ack', ports['din_ack_%s' % no]),
                   ('dout', ports['din_%s' % no]), ('count', count_producer)]
            m.Instance(p, p.name + '_%s' % no, param, con)
        elif op == 'out':
            param = [('data_width', data_width), ('fail_rate', fail_rate_consumer)]
            con = [('clk', clk), ('rst', rst), ('req', ports['dout_req_%s' % no]), ('ack', ports['dout_ack_%s' % no]),
                   ('din', ports['dout_%s' % no]), ('count', count_consumer)]
            m.Instance(c, c.name + '_%s' % no, param, con)

    m.Instance(dataflow, dataflow.name, dataflow.get_params(), dataflow.get_ports())

    return m
