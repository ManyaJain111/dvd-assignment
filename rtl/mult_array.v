// 4-bit x 4-bit unsigned array multiplier
//   - a and b are registered on every rising clock edge
//   - the array (16 AND gates + 12 full adders) is built from the registered values
//   - the 8-bit product is registered into p
//   => 16 flip-flops, 2-cycle latency, one result per clock
module mult_array (
    input  wire       clk,
    input  wire       rst_n,   // asynchronous, active low
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg  [7:0] p
);

    // ------------------------------------------------------------------
    // Input registers
    // ------------------------------------------------------------------
    reg [3:0] a_r, b_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_r <= 4'b0;
            b_r <= 4'b0;
        end else begin
            a_r <= a;
            b_r <= b;
        end
    end

    // ------------------------------------------------------------------
    // Partial products: pp_i[j] = a[j] AND b[i]  (16 AND gates)
    // ------------------------------------------------------------------
    wire [3:0] pp0 = a_r & {4{b_r[0]}};
    wire [3:0] pp1 = a_r & {4{b_r[1]}};
    wire [3:0] pp2 = a_r & {4{b_r[2]}};
    wire [3:0] pp3 = a_r & {4{b_r[3]}};

    // ------------------------------------------------------------------
    // Row 0: AND gates only
    // ------------------------------------------------------------------
    wire [3:0] r0 = {1'b0, pp0[3], pp0[2], pp0[1]};

    // ------------------------------------------------------------------
    // Row 1: pp1 + r0
    // ------------------------------------------------------------------
    wire [3:0] s1;
    wire [4:0] c1;
    assign c1[0] = 1'b0;

    full_adder fa1_0 (.a(pp1[0]), .b(r0[0]), .cin(c1[0]), .sum(s1[0]), .cout(c1[1]));
    full_adder fa1_1 (.a(pp1[1]), .b(r0[1]), .cin(c1[1]), .sum(s1[1]), .cout(c1[2]));
    full_adder fa1_2 (.a(pp1[2]), .b(r0[2]), .cin(c1[2]), .sum(s1[2]), .cout(c1[3]));
    full_adder fa1_3 (.a(pp1[3]), .b(r0[3]), .cin(c1[3]), .sum(s1[3]), .cout(c1[4]));

    wire [3:0] r1 = {c1[4], s1[3], s1[2], s1[1]};

    // ------------------------------------------------------------------
    // Row 2: pp2 + r1
    // ------------------------------------------------------------------
    wire [3:0] s2;
    wire [4:0] c2;
    assign c2[0] = 1'b0;

    full_adder fa2_0 (.a(pp2[0]), .b(r1[0]), .cin(c2[0]), .sum(s2[0]), .cout(c2[1]));
    full_adder fa2_1 (.a(pp2[1]), .b(r1[1]), .cin(c2[1]), .sum(s2[1]), .cout(c2[2]));
    full_adder fa2_2 (.a(pp2[2]), .b(r1[2]), .cin(c2[2]), .sum(s2[2]), .cout(c2[3]));
    full_adder fa2_3 (.a(pp2[3]), .b(r1[3]), .cin(c2[3]), .sum(s2[3]), .cout(c2[4]));

    wire [3:0] r2 = {c2[4], s2[3], s2[2], s2[1]};

    // ------------------------------------------------------------------
    // Row 3: pp3 + r2
    // ------------------------------------------------------------------
    wire [3:0] s3;
    wire [4:0] c3;
    assign c3[0] = 1'b0;

    full_adder fa3_0 (.a(pp3[0]), .b(r2[0]), .cin(c3[0]), .sum(s3[0]), .cout(c3[1]));
    full_adder fa3_1 (.a(pp3[1]), .b(r2[1]), .cin(c3[1]), .sum(s3[1]), .cout(c3[2]));
    full_adder fa3_2 (.a(pp3[2]), .b(r2[2]), .cin(c3[2]), .sum(s3[2]), .cout(c3[3]));
    full_adder fa3_3 (.a(pp3[3]), .b(r2[3]), .cin(c3[3]), .sum(s3[3]), .cout(c3[4]));

    // ------------------------------------------------------------------
    // Combinational product
    // ------------------------------------------------------------------
    wire [7:0] prod = {c3[4], s3[3], s3[2], s3[1], s3[0], s2[0], s1[0], pp0[0]};

    // ------------------------------------------------------------------
    // Output register
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            p <= 8'b0;
        else
            p <= prod;
    end

endmodule
