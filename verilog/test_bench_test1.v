

module test_bench_test1
(

);

  localparam data_width = 8;
  localparam fail_rate_producer = 0;
  localparam fail_rate_consumer = 0;
  localparam is_const = "false";
  localparam initial_value = 0;
  localparam max_data_size = 5000;
  reg clk;
  reg rst;
  wire din_req_0;
  wire din_ack_0;
  wire [data_width-1:0] din_0;
  wire dout_req_3;
  wire dout_ack_3;
  wire [data_width-1:0] dout_3;
  wire [32-1:0] count_producer;
  wire [32-1:0] count_consumer;
  real count_clock;

  initial begin
    clk = 0;
    forever begin
      #1 clk = !clk;
    end
  end


  initial begin
    rst = 0;
    #1;
    rst = 1;
    #1;
    rst = 0;
  end


  always @(posedge clk) begin
    if(rst) begin
      count_clock <= 0;
    end 
    count_clock <= count_clock + 1;
    if(count_consumer >= max_data_size) begin
      $display("test_bench_test1 throughput: %5.2f%%", (100.0 * (count_consumer / (count_clock / 4.0))));
      $finish;
    end 
  end


  producer
  #(
    .data_width(data_width),
    .fail_rate(fail_rate_producer),
    .initial_value(initial_value),
    .is_const(is_const)
  )
  producer_0
  (
    .clk(clk),
    .rst(rst),
    .req(din_req_0),
    .ack(din_ack_0),
    .dout(din_0),
    .count(count_producer)
  );


  consumer
  #(
    .data_width(data_width),
    .fail_rate(fail_rate_consumer)
  )
  consumer_3
  (
    .clk(clk),
    .rst(rst),
    .req(dout_req_3),
    .ack(dout_ack_3),
    .din(dout_3),
    .count(count_consumer)
  );


  test1
  #(
    .data_width(data_width)
  )
  test1
  (
    .clk(clk),
    .rst(rst),
    .din_req_0(din_req_0),
    .din_ack_0(din_ack_0),
    .din_0(din_0),
    .dout_req_3(dout_req_3),
    .dout_ack_3(dout_ack_3),
    .dout_3(dout_3)
  );


endmodule



module producer #
(
  parameter data_width = 8,
  parameter fail_rate = 0,
  parameter is_const = "false",
  parameter initial_value = 0
)
(
  input clk,
  input rst,
  input req,
  output reg ack,
  output reg [data_width-1:0] dout,
  output reg [32-1:0] count
);

  reg [data_width-1:0] dout_next;
  reg stop;
  real randd;

  always @(posedge clk) begin
    if(rst) begin
      dout <= initial_value;
      dout_next <= initial_value;
      ack <= 0;
      count <= 0;
      stop <= 0;
      randd <= $abs($random%101)+1;
    end else begin
      ack <= 0;
      randd <= $abs($random%101)+1;
      stop <= (randd > fail_rate)? 0 : 1;
      if(req & ~ack & !stop) begin
        ack <= 1;
        dout <= dout_next;
        if(is_const == "false") begin
          dout_next <= dout_next + 1;
        end 
        count <= count + 1;
      end 
    end
  end


endmodule



module consumer #
(
  parameter data_width = 8,
  parameter fail_rate = 0
)
(
  input clk,
  input rst,
  output reg req,
  input ack,
  input [data_width-1:0] din,
  output reg [32-1:0] count
);

  reg stop;
  real randd;

  always @(posedge clk) begin
    if(rst) begin
      req <= 0;
      count <= 0;
      stop <= 0;
      randd <= $abs($random%101)+1;
    end else begin
      req <= 0;
      randd <= $abs($random%101)+1;
      stop <= (randd > fail_rate)? 0 : 1;
      if(!stop) begin
        req <= 1;
      end 
      if(ack) begin
        count <= count + 1;
      end 
    end
  end


endmodule



module test1 #
(
  parameter data_width = 8
)
(
  input clk,
  input rst,
  output din_req_0,
  input din_ack_0,
  input [data_width-1:0] din_0,
  input dout_req_3,
  output dout_ack_3,
  output [data_width-1:0] dout_3
);

  wire req_0_1;
  wire req_0_2;
  wire ack_0;
  wire [data_width-1:0] d0;
  wire req_1_2;
  wire ack_1;
  wire [data_width-1:0] d1;
  wire req_2_3;
  wire ack_2;
  wire [data_width-1:0] d2;

  async_operator
  #(
    .data_width(data_width),
    .op("in"),
    .immediate(0),
    .input_size(1),
    .output_size(2)
  )
  in_0
  (
    .clk(clk),
    .rst(rst),
    .req_l(din_req_0),
    .ack_l(din_ack_0),
    .req_r({req_0_1, req_0_2}),
    .ack_r(ack_0),
    .din(din_0),
    .dout(d0)
  );


  async_operator
  #(
    .data_width(data_width),
    .op("reg"),
    .immediate(0),
    .input_size(1),
    .output_size(1)
  )
  reg_1
  (
    .clk(clk),
    .rst(rst),
    .req_l({req_0_1}),
    .ack_l({ack_0}),
    .req_r({req_1_2}),
    .ack_r(ack_1),
    .din({d0}),
    .dout(d1)
  );


  async_operator
  #(
    .data_width(data_width),
    .op("add"),
    .immediate(0),
    .input_size(2),
    .output_size(1)
  )
  add_2
  (
    .clk(clk),
    .rst(rst),
    .req_l({req_1_2, req_0_2}),
    .ack_l({ack_1, ack_0}),
    .req_r({req_2_3}),
    .ack_r(ack_2),
    .din({d1, d0}),
    .dout(d2)
  );


  async_operator
  #(
    .data_width(data_width),
    .op("out"),
    .immediate(0),
    .input_size(1),
    .output_size(1)
  )
  out_3
  (
    .clk(clk),
    .rst(rst),
    .req_l(req_2_3),
    .ack_l(ack_2),
    .req_r(dout_req_3),
    .ack_r(dout_ack_3),
    .din(d2),
    .dout(dout_3)
  );


endmodule



module async_operator #
(
  parameter data_width = 8,
  parameter op = "reg",
  parameter immediate = 8,
  parameter input_size = 1,
  parameter output_size = 1
)
(
  input clk,
  input rst,
  output reg [input_size-1:0] req_l,
  input [input_size-1:0] ack_l,
  input [output_size-1:0] req_r,
  output ack_r,
  input [data_width*input_size-1:0] din,
  output [data_width-1:0] dout
);

  reg [data_width*input_size-1:0] din_r;
  wire has_all;
  wire req_r_all;
  reg [output_size-1:0] ack_r_all;
  reg [input_size-1:0] has;
  integer i;
  genvar g;
  assign has_all = &has;
  assign req_r_all = &req_r;
  assign ack_r = &ack_r_all;

  always @(posedge clk) begin
    if(rst) begin
      has <= { input_size{ 1'b0 } };
      ack_r_all <= { output_size{ 1'b0 } };
      req_l <= { input_size{ 1'b0 } };
    end else begin
      for(i=0; i<input_size; i=i+1) begin
        if(~has[i] & ~req_l[i]) begin
          req_l[i] <= 1'b1;
        end 
        if(ack_l[i]) begin
          has[i] <= 1'b1;
          req_l[i] <= 1'b0;
        end 
      end
      if(has_all & req_r_all) begin
        ack_r_all <= { output_size{ 1'b1 } };
        has <= { input_size{ 1'b0 } };
      end 
      if(~has_all) begin
        ack_r_all <= { output_size{ 1'b0 } };
      end 
    end
  end


  generate for(g=0; g<input_size; g=g+1) begin : rcv

    always @(posedge ack_l[g]) begin
      din_r[data_width*(g+1)-1:data_width*g] <= din[data_width*(g+1)-1:data_width*g];
    end

  end
  endgenerate


  operator
  #(
    .num_inputs(input_size),
    .op(op),
    .immediate(immediate),
    .data_width(data_width)
  )
  operator
  (
    .din(din_r),
    .dout(dout)
  );


endmodule



module operator #
(
  parameter num_inputs = 1,
  parameter op = "reg",
  parameter signed immediate = 0,
  parameter data_width = 32
)
(
  input signed [data_width*num_inputs-1:0] din,
  output signed [data_width-1:0] dout
);


  generate if(num_inputs == 1) begin : gen_op
    if((op === "reg") || (op === "in") || (op === "out")) begin
      assign dout = din;
    end 
    if(op === "addi") begin
      assign dout = din+immediate;
    end 
    if(op === "subi") begin
      assign dout = din-immediate;
    end 
    if(op === "muli") begin
      assign dout = din*immediate;
    end 
    if(op === "andi") begin
      assign dout = din&immediate;
    end 
    if(op === "ori") begin
      assign dout = din|immediate;
    end 
    if(op === "not") begin
      assign dout = ~din;
    end 
    if(op === "landi") begin
      assign dout = din&&immediate;
    end 
    if(op === "lori") begin
      assign dout = din||immediate;
    end 
    if(op === "lnot") begin
      assign dout = !din;
    end 
    if(op === "xori") begin
      assign dout = din^immediate;
    end 
  end else begin
    if(num_inputs == 2) begin
      if(op === "add") begin
        assign dout = din[data_width-1:0]+din[data_width*2-1:data_width];
      end 
      if(op === "sub") begin
        assign dout = din[data_width-1:0]-din[data_width*2-1:data_width];
      end 
      if(op === "mul") begin
        assign dout = din[data_width-1:0]*din[data_width*2-1:data_width];
      end 
      if(op === "and") begin
        assign dout = din[data_width-1:0]&din[data_width*2-1:data_width];
      end 
      if(op === "or") begin
        assign dout = din[data_width-1:0]|din[data_width*2-1:data_width];
      end 
      if(op === "land") begin
        assign dout = din[data_width-1:0]&&din[data_width*2-1:data_width];
      end 
      if(op === "lor") begin
        assign dout = din[data_width-1:0]||din[data_width*2-1:data_width];
      end 
      if(op === "xor") begin
        assign dout = din[data_width-1:0]^din[data_width*2-1:data_width];
      end 
    end else begin
      if(num_inputs == 3) begin
        if(op === "add") begin
          assign dout = din[data_width-1:0]+din[data_width*2-1:data_width]+din[data_width*3-1:data_width*2];
        end 
        if(op === "sub") begin
          assign dout = din[data_width-1:0]-din[data_width*2-1:data_width]-din[data_width*3-1:data_width*2];
        end 
        if(op === "mul") begin
          assign dout = din[data_width-1:0]*din[data_width*2-1:data_width]*din[data_width*3-1:data_width*2];
        end 
        if(op === "madd") begin
          assign dout = din[data_width-1:0]*din[data_width*2-1:data_width]+din[data_width*3-1:data_width*2];
        end 
        if(op === "msub") begin
          assign dout = din[data_width-1:0]*din[data_width*2-1:data_width]-din[data_width*3-1:data_width*2];
        end 
        if(op === "addadd") begin
          assign dout = din[data_width-1:0]+din[data_width*2-1:data_width]+din[data_width*3-1:data_width*2];
        end 
        if(op === "subsub") begin
          assign dout = din[data_width-1:0]-din[data_width*2-1:data_width]-din[data_width*3-1:data_width*2];
        end 
        if(op === "addsub") begin
          assign dout = din[data_width-1:0]+din[data_width*2-1:data_width]-din[data_width*3-1:data_width*2];
        end 
        if(op === "mux") begin
          assign dout = din[data_width-1:0]==0?din[data_width*2-1:data_width]:din[data_width*3-1:data_width*2];
        end 
      end 
    end
  end
  endgenerate


endmodule

