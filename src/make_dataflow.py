from veriloggen import *


def create_wires(m, df):
    data_width = m.get_params()['data_width']
    wires = {}
    for no in df.nodes:
        op = str.lower(df.nodes[no]['op'])
        for n in df.successors(no):
            req_r = m.Wire('req_%s_%s' % (no, n))
            wires[req_r.name] = req_r
        if op == 'in':
            req_r = m.Output('din_req_%s' % no)
            ack_r = m.Input('din_ack_%s' % no)
            d = m.Input('din_%s' % no, data_width)
            wires[req_r.name] = req_r
            wires[ack_r.name] = ack_r
            wires[d.name] = d
            ack_r = m.Wire('ack_%s' % no)
            d = m.Wire('d%s' % no, data_width)
            wires[ack_r.name] = ack_r
            wires[d.name] = d
        elif op == 'out':
            parent = [n for n in df.predecessors(no)][0]
            req_r = m.Input('dout_req_%s' % no)
            ack_r = m.Output('dout_ack_%s' % no)
            d = m.Output('dout_%s' % no, data_width)
            wires['req_%s' % parent] = req_r
            wires['ack_%s' % parent] = ack_r
            wires['d%s' % parent] = d
        else:
            ack_r = m.Wire('ack_%s' % no)
            d = m.Wire('d%s' % no, data_width)
            wires[ack_r.name] = ack_r
            wires[d.name] = d

    return wires


def get_immediate(no):
    immediate = 0
    operators = ['addi', 'subi', 'muli','andi','ori','xori','landi','lori','lxori']
    name = str.lower(no['label'])
    if name in operators:
        immediate = int(no['value'])
    return immediate


def create_con_node(df, no):
    din = ''
    req_l = ''
    ack_l = ''
    req_r = ''
    dout = ''
    ack_r = ''

    if df.nodes[no]['op'] == 'in':
        req_l = 'din_req_%s' % no
        ack_l = 'din_ack_%s' % no
        ack_r = 'ack_%s' % no
        din = 'din_%s' % no
        dout = 'd%s' % no
        req_r = '{'
        for d in df.successors(no):
            req_r += 'req_%s_%s, ' % (no, d)
        req_r = req_r[:-2]
        req_r += '}'
    elif df.nodes[no]['op'] == 'out':
        req_r = 'dout_req_%s' % no
        ack_r = 'dout_ack_%s' % no
        dout = 'dout_%s' % no
        for d in df.predecessors(no):
            req_l = 'req_%s_%s' % (d, no)
            ack_l = 'ack_%s' % d
            din = 'd%s' % d
            break
    else:
        req_l = '{'
        ack_l = '{'
        din = '{'
        req_r = '{'
        ack_r = ''
        dout = ''
        for d in df.successors(no):
            req_r += 'req_%s_%s, ' % (no, d)
        req_r = req_r[:-2]
        req_r += '}'
        ack_r += 'ack_%s' % no
        dout += 'd%s' % no
        portsl = [0 for _ in df.predecessors(no)]
        for d in df.predecessors(no):
            portsl[int(df.edges[(d, no)]['port'])] = d
            req_l += 'req_%s_%s, ' % ('%s', no)
            ack_l += 'ack_%s, '
            din += 'd%s, '
        req_l = req_l[:-2]
        ack_l = ack_l[:-2]
        din = din[:-2]
        req_l += '}'
        ack_l += '}'
        din += '}'
        portsl = tuple(reversed(portsl))
        req_l = req_l % portsl
        ack_l = ack_l % portsl
        din = din % portsl

    req_l = EmbeddedCode(req_l)
    ack_l = EmbeddedCode(ack_l)
    din = EmbeddedCode(din)
    req_r = EmbeddedCode(req_r)
    ack_r = EmbeddedCode(ack_r)
    dout = EmbeddedCode(dout)
    con = req_l, ack_l, din, req_r, ack_r, dout

    return con


def make_async_operator():
    m = Module('async_operator')
    data_width = m.Parameter('data_width', 8)
    op = m.Parameter('op', 'reg')
    immediate = m.Parameter('immediate', data_width)
    input_size = m.Parameter('input_size', 1)
    output_size = m.Parameter('output_size', 1)

    clk = m.Input('clk')
    rst = m.Input('rst')
    req_l = m.OutputReg('req_l', input_size)
    ack_l = m.Input('ack_l', input_size)
    req_r = m.Input('req_r', output_size)
    ack_r = m.Output('ack_r')
    din = m.Input('din', Mul(data_width, input_size))
    dout = m.Output('dout', data_width)

    din_r = m.Reg('din_r', Mul(data_width, input_size))
    has_all = m.Wire('has_all')
    req_r_all = m.Wire('req_r_all')
    ack_r_all = m.Reg('ack_r_all', output_size)
    has = m.Reg('has', input_size)

    i = m.Integer('i')
    g = m.Genvar('g')

    has_all.assign(Uand(has))
    req_r_all.assign(Uand(req_r))
    ack_r.assign(Uand(ack_r_all))
    m.Always(Posedge(clk))(
        If(rst)(
            has(Repeat(Int(0, 1, 2), input_size)),
            ack_r_all(Repeat(Int(0, 1, 2), output_size)),
            req_l(Repeat(Int(0, 1, 2), input_size))
        ).Else(
            For(i(0), i < input_size, i.inc())(
                If(~has[i] & ~req_l[i])(
                    req_l[i](Int(1, 1, 2))
                ),
                If(ack_l[i])(
                    has[i](Int(1, 1, 2)),
                    req_l[i](Int(0, 1, 2))
                )
            ),
            If(has_all & req_r_all)(
                ack_r_all(Repeat(Int(1, 1, 2), output_size)),
                has(Repeat(Int(0, 1, 2), input_size)),
            ),
            If(~has_all)(
                ack_r_all(Repeat(Int(0, 1, 2), output_size)),
            )
        )
    )
    genfor = m.GenerateFor(g(0), g < input_size, g.inc(), 'rcv')
    genfor.Always(Posedge(ack_l[g]))(
        din_r[Mul(data_width, g):Mul(data_width, g + 1)](din[Mul(data_width, g):Mul(data_width, g + 1)])
    )

    operator = make_operator()
    param = [('num_inputs', input_size), ('op', op), ('immediate', immediate), ('data_width', data_width)]
    con = [('din', din_r), ('dout', dout)]
    m.Instance(operator, 'operator', param, con)

    return m


def make_operator():
    m = Module('operator')
    num_inputs = m.Parameter('num_inputs', 1)
    op = m.Parameter('op', 'reg')
    immediate = m.Parameter('immediate', 0, signed=True)
    data_width = m.Parameter('data_width', 32)

    din = m.Input('din', Mul(data_width, num_inputs), signed=True)
    dout = m.Output('dout', data_width, signed=True)

    unary_code = 'assign dout = din%simmediate;'
    binary_code = 'assign dout = din[data_width-1:0]%sdin[data_width*2-1:data_width];'
    ternary_code = 'assign dout = din[data_width-1:0]%sdin[data_width*2-1:data_width]%sdin[data_width*3-1:data_width*2];'
    mux_code = 'assign dout = din[data_width-1:0]==0?din[data_width*2-1:data_width]:din[data_width*3-1:data_width*2];'

    genif = m.GenerateIf(num_inputs == 1, 'gen_op')
    genif.GenerateIf(OrList(Eql(op, "reg"), Eql(op, "in"), Eql(op, "out"))).EmbeddedCode('assign dout = din;')
    genif.GenerateIf(Eql(op, "addi")).EmbeddedCode(unary_code % '+')
    genif.GenerateIf(Eql(op, "subi")).EmbeddedCode(unary_code % '-')
    genif.GenerateIf(Eql(op, "muli")).EmbeddedCode(unary_code % '*')

    genif.GenerateIf(Eql(op, "andi")).EmbeddedCode(unary_code % '&')
    genif.GenerateIf(Eql(op, "ori")).EmbeddedCode(unary_code % '|')
    genif.GenerateIf(Eql(op, "not")).EmbeddedCode('assign dout = ~din;')
    genif.GenerateIf(Eql(op, "landi")).EmbeddedCode(unary_code % '&&')
    genif.GenerateIf(Eql(op, "lori")).EmbeddedCode(unary_code % '||')
    genif.GenerateIf(Eql(op, "lnot")).EmbeddedCode('assign dout = !din;')
    genif.GenerateIf(Eql(op, "xori")).EmbeddedCode(unary_code % '^')

    genif = genif.Else.GenerateIf(num_inputs == 2)
    genif.GenerateIf(Eql(op, "add")).EmbeddedCode(binary_code % '+')
    genif.GenerateIf(Eql(op, "sub")).EmbeddedCode(binary_code % '-')
    genif.GenerateIf(Eql(op, "mul")).EmbeddedCode(binary_code % '*')
    genif.GenerateIf(Eql(op, "and")).EmbeddedCode(binary_code % '&')
    genif.GenerateIf(Eql(op, "or")).EmbeddedCode(binary_code % '|')
    genif.GenerateIf(Eql(op, "land")).EmbeddedCode(binary_code % '&&')
    genif.GenerateIf(Eql(op, "lor")).EmbeddedCode(binary_code % '||')
    genif.GenerateIf(Eql(op, "xor")).EmbeddedCode(binary_code % '^')
    genif = genif.Else.GenerateIf(num_inputs == 3)
    genif.GenerateIf(Eql(op, "add")).EmbeddedCode(ternary_code % ('+', '+'))
    genif.GenerateIf(Eql(op, "sub")).EmbeddedCode(ternary_code % ('-', '-'))
    genif.GenerateIf(Eql(op, "mul")).EmbeddedCode(ternary_code % ('*', '*'))
    genif.GenerateIf(Eql(op, "madd")).EmbeddedCode(ternary_code % ('*', '+'))
    genif.GenerateIf(Eql(op, "msub")).EmbeddedCode(ternary_code % ('*', '-'))
    genif.GenerateIf(Eql(op, "addadd")).EmbeddedCode(ternary_code % ('+', '+'))
    genif.GenerateIf(Eql(op, "subsub")).EmbeddedCode(ternary_code % ('-', '-'))
    genif.GenerateIf(Eql(op, "addsub")).EmbeddedCode(ternary_code % ('+', '-'))
    genif.GenerateIf(Eql(op, "mux")).EmbeddedCode(mux_code)

    return m


def make_dataflow(df):
    m = Module(df.name)
    data_width = m.Parameter('data_width', 8)
    clk = m.Input('clk')
    rst = m.Input('rst')
    wires = create_wires(m, df)
    operator = make_async_operator()
    for no in df.nodes:
        op = str.lower(df.nodes[no]['op'])
        immediate = get_immediate(df.nodes[no])
        input_size = df.in_degree(no)
        output_size = df.out_degree(no)
        if op == 'in':
            input_size += 1
        if op == 'out':
            output_size += 1

        req_l, ack_l, din, req_r, ack_r, dout = create_con_node(df, no)
        param = [('data_width', data_width),
                 ('op', op),
                 ('immediate', immediate),
                 ('input_size', input_size),
                 ('output_size', output_size)
                 ]
        con = [('clk', clk),
               ('rst', rst),
               ('req_l', req_l),
               ('ack_l', ack_l),
               ('req_r', req_r),
               ('ack_r', ack_r),
               ('din', din),
               ('dout', dout)]
        m.Instance(operator, '%s_%s' % (op, no), param, con)

    return m
