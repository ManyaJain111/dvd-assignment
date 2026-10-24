`timescale 1ns / 1ps

// Exhaustive self-checking testbench for mult_array
//   - 10 ns clock, rst_n held low for the first 2 cycles
//   - applies all 256 (a, b) combinations
//   - waits for the 2-cycle latency, then compares p against a*b
//   - prints a line per mismatch and one PASS/FAIL summary line
//   - dumps waveforms to mult.vcd
module tb_mult;

    reg        clk;
    reg        rst_n;
    reg  [3:0] a;
    reg  [3:0] b;
    wire [7:0] p;

    integer i, j;
    integer errors;
    integer checked;
    reg [7:0] expected;

    mult_array dut (
        .clk  (clk),
        .rst_n(rst_n),
        .a    (a),
        .b    (b),
        .p    (p)
    );

    // 10 ns clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("mult.vcd");
        $dumpvars(0, tb_mult);

        errors  = 0;
        checked = 0;
        a       = 4'd0;
        b       = 4'd0;

        // Hold reset low for the first 2 clock cycles
        rst_n = 1'b0;
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        for (i = 0; i < 16; i = i + 1) begin
            for (j = 0; j < 16; j = j + 1) begin
                // Apply inputs away from the active edge
                @(negedge clk);
                a = i;
                b = j;
                expected = i * j;

                // Edge 1: inputs captured; edge 2: product captured into p
                repeat (2) @(posedge clk);

                // Sample half a cycle later, after all outputs have settled
                @(negedge clk);
                checked = checked + 1;
                if (p !== expected) begin
                    errors = errors + 1;
                    $display("MISMATCH: a=%0d b=%0d expected=%0d got=%0d (t=%0t)",
                             a, b, expected, p, $time);
                end
            end
        end

        if (errors == 0)
            $display("PASS: %0d vectors checked, %0d errors", checked, errors);
        else
            $display("FAIL: %0d vectors checked, %0d errors", checked, errors);

        $finish;
    end

endmodule
