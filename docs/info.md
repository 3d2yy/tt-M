# How it works

This design is an eight-tap signed FIR correlator. It evaluates

`y[n] = sum(h[k] * x[n-k], k=0..7)`.

Samples are signed 8-bit integers (-128..127), coefficients are signed 4-bit integers (-8..7), and tap zero multiplies the newest sample. The 15-bit signed accumulator covers the exact possible result range (-8128..8192). The output is sign-extended to 16 bits and read one byte at a time.

One shared multiplier and accumulator evaluate one tap per enabled clock cycle. No ADC, RF input stage, coefficient learning, packet decoder, or normalization is included. A host sends digital samples synchronously to `clk`.

Reset installs the time-order pattern `[1,1,-1,-1,1,-1,1,-1]`, hence newest-first coefficients `[-1,1,-1,1,-1,-1,1,1]`, and a threshold of 160. Sending the time-order pattern at amplitude 32 gives a final result of 256.

# How to test

## Pins

| Pins | Direction | Meaning |
|---|---|---|
| `ui_in[7:0]` | Input | Command data; signed byte for SAMPLE |
| `uo_out[7:0]` | Output | Selected byte of the last result |
| `uio[0]` | Input | STROBE: accept a command when READY is high |
| `uio[3:1]` | Input | Command opcode |
| `uio[4]` | Input | READ_HIGH: 0 selects low byte, 1 selects high byte |
| `uio[5]` | Output | READY: able to accept a command |
| `uio[6]` | Output | RESULT_VALID: a completed result is available |
| `uio[7]` | Output | HIT: last full window meets the positive threshold |

`uio_oe` is `0xE0`: the host must not drive pins 5..7. Reset is active low and asynchronous. With `ena=0`, registers hold their state and READY is low; an in-progress calculation resumes when enabled again. Status and result outputs otherwise retain their values.

## Commands

Each command is accepted at a rising clock edge with `ena=1`, READY=1 and STROBE=1. Data, opcode and strobe must meet setup/hold requirements. STROBE is level-sensitive, not an edge detector. Keeping it high accepts another command at the next eligible edge. Commands presented while busy are discarded; there is no input queue.

| Opcode | Command | Data |
|---|---|---|
| 0 | SAMPLE | Signed 8-bit sample |
| 1 | INDEX | Coefficient address in bits 2..0 |
| 2 | WEIGHT | Signed coefficient in bits 3..0; upper bits ignored |
| 3 | THRESHOLD_LOW | Threshold bits 7..0 |
| 4 | THRESHOLD_HIGH | Threshold bits 13..8 in data bits 5..0; upper bits ignored |
| 5 | CLEAR | Clear sample history, result and flags; preserve configuration |
| 6 | ACK | Clear RESULT_VALID and HIT; preserve result and history |
| 7 | NOP | No state change |

Threshold is unsigned (0..16383). HIT uses **signed positive** comparison `y >= threshold`; a large negative score does not trigger. Results from the first seven samples are zero-padded and valid, but cannot trigger. Threshold zero is allowed and can trigger on a zero full-window score.

Configuration writes do not alter the previous result or flags. Finish all coefficient/threshold writes and issue CLEAR before starting a new acquisition. Change configuration only between acquisitions to keep interpretation consistent.

## Timing and result read

If SAMPLE is accepted at edge N, RESULT_VALID and READY go low. Tap evaluations occur at N+1 through N+8. At N+8 the result, HIT and RESULT_VALID update, and READY returns high. The next SAMPLE can be accepted at N+9. These edge counts apply with `ena` continuously high.

Read the low and high result bytes while RESULT_VALID is high and without sending another SAMPLE or CLEAR between reads. Combine the bytes as a signed two's-complement 16-bit integer. There is no output queue: a later completed result overwrites the previous result. HIT is a retained flag for the last completed window, not a one-cycle pulse or a count of unique events.

## Quick example

1. Reset the chip and release reset; keep `ena=1`.
2. Send samples `[32,32,-32,-32,32,-32,32,-32]` using SAMPLE, waiting for READY before each one.
3. After the last eight calculation cycles, RESULT_VALID and HIT are high.
4. READ_HIGH=0 returns `0x00`; READ_HIGH=1 returns `0x01`: score 256.
5. Issue ACK to clear both flags, or send a new SAMPLE to calculate the next window.

Local verification: run the commands in README.md. Tests cover all 4096 sample/coefficient pairs, accumulation extremes, random sliding windows, configuration, threshold equality, warm-up, disabled operation, reset while busy and commands ignored while busy. The same testbench can run with `GATES=yes` and the PDK/netlist supplied by Tiny Tapeout.

# External hardware

For digital verification, a synchronous host supplying the input bytes and controls is sufficient. Analog signal acquisition additionally requires external conditioning and an ADC. The microcontroller or FPGA host must generate signals synchronized to the chip clock; arbitrary asynchronous GPIO transitions are not supported.
