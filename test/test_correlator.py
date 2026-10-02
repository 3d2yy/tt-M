"""Check the public pin protocol against an independent integer specification."""
import random
import cocotb
from cocotb.triggers import Timer
from reference import correlate, DEFAULT_WEIGHTS, DEFAULT_PATTERN


class Host:
    def __init__(self, dut):
        self.dut = dut

    async def tick(self):
        self.dut.clk.value = 0
        await Timer(10, units='ns')
        self.dut.clk.value = 1
        await Timer(10, units='ns')

    @property
    def status(self):
        return int(self.dut.uio_out.value)

    @property
    def ready(self):
        return bool(self.status & 0x20)

    @property
    def valid(self):
        return bool(self.status & 0x40)

    @property
    def hit(self):
        return bool(self.status & 0x80)

    async def reset(self):
        self.dut.ena.value = 1
        self.dut.ui_in.value = 0
        self.dut.uio_in.value = 0
        self.dut.rst_n.value = 0
        await self.tick()
        await self.tick()
        self.dut.rst_n.value = 1
        await self.tick()
        assert self.ready and not self.valid and not self.hit
        assert int(self.dut.uio_oe.value) == 0xE0

    async def command(self, opcode, value=0):
        assert self.ready, 'Host must wait for READY'
        self.dut.ui_in.value = value & 0xFF
        self.dut.uio_in.value = (opcode << 1) | 1
        await self.tick()
        self.dut.uio_in.value = 0

    async def result(self):
        self.dut.uio_in.value = 0
        await Timer(1, units='ns')
        low = int(self.dut.uo_out.value)
        self.dut.uio_in.value = 0x10
        await Timer(1, units='ns')
        word = low | int(self.dut.uo_out.value) << 8
        self.dut.uio_in.value = 0
        return word - 65536 if word & 0x8000 else word

    async def sample(self, value):
        await self.command(0, value)
        assert not self.ready and not self.valid and not self.hit
        for index in range(8):
            await self.tick()
            if index < 7:
                assert not self.ready and not self.valid
        assert self.ready and self.valid
        return await self.result()

    async def configure(self, weights, threshold):
        for index, value in enumerate(weights):
            await self.command(1, index)
            await self.command(2, value & 0x0F)
        await self.command(3, threshold & 0xFF)
        await self.command(4, threshold >> 8)
        await self.command(5)


@cocotb.test()
async def default_pattern_and_warmup(dut):
    host = Host(dut)
    await host.reset()
    samples = [32 * sign for sign in DEFAULT_PATTERN] + [0] * 8
    for n, (sample, expected) in enumerate(zip(samples, correlate(samples, DEFAULT_WEIGHTS))):
        assert await host.sample(sample) == expected
        assert host.hit == (n >= 7 and expected >= 160)
        if n == 7:
            assert expected == 256 and host.hit
    retained = await host.result()
    await host.command(6)
    assert not host.valid and not host.hit
    assert await host.result() == retained


@cocotb.test()
async def random_windows_and_configuration(dut):
    host = Host(dut)
    await host.reset()
    rng = random.Random(20261002)
    for _ in range(24):
        weights = [rng.randrange(-8, 8) for _ in range(8)]
        threshold = rng.randrange(0, 16384)
        await host.configure(weights, threshold)
        samples = [rng.randrange(-128, 128) for _ in range(64)]
        for n, (sample, expected) in enumerate(zip(samples, correlate(samples, weights))):
            assert await host.sample(sample) == expected
            assert host.hit == (n >= 7 and expected >= threshold)
    await host.command(5)
    assert await host.result() == 0 and not host.valid
    assert await host.sample(127) == 127 * weights[0]
    assert not host.hit


@cocotb.test()
async def exhaustive_signed_multiplier_and_accumulator_limits(dut):
    host = Host(dut)
    await host.reset()
    await host.configure([0] * 8, 16383)
    for coefficient in range(-8, 8):
        await host.command(1, 0)
        await host.command(2, coefficient & 0x0F)
        for sample in range(-128, 128):
            assert await host.sample(sample) == sample * coefficient
            assert not host.hit
    for weights, value, expected in [([-8]*8, -128, 8192),
                                      ([-8]*8, 127, -8128),
                                      ([7]*8, -128, -7168),
                                      ([7]*8, 127, 7112)]:
        await host.configure(weights, max(expected, 0))
        for n in range(8):
            actual = await host.sample(value)
            assert actual == (n + 1) * value * weights[0]
            assert host.hit == (n == 7 and expected >= 0)


@cocotb.test()
async def busy_ignore_enable_pause_and_reset(dut):
    host = Host(dut)
    await host.reset()
    await host.command(0, 37)
    for opcode, data in [(2, 7), (0, 99)]:
        dut.uio_in.value = (opcode << 1) | 1
        dut.ui_in.value = data
        await host.tick()
    dut.uio_in.value = 0
    dut.ena.value = 0
    for _ in range(5):
        await host.tick()
        assert not host.ready and not host.valid
    dut.ena.value = 1
    for n in range(6):
        await host.tick()
        assert host.valid == (n == 5)
    assert await host.result() == -37
    assert await host.sample(0) == 37
    dut.ena.value = 0
    dut.uio_in.value = 1
    dut.ui_in.value = 100
    await host.tick()
    dut.uio_in.value = 0
    dut.ena.value = 1
    await host.tick()
    assert host.ready and host.valid and await host.result() == 37
    await host.command(0, 100)
    await host.tick()
    await host.reset()
    assert await host.result() == 0
    assert await host.sample(37) == -37


@cocotb.test()
async def threshold_equality_nop_and_held_strobe(dut):
    host = Host(dut)
    await host.reset()
    await host.configure([1] + [0] * 7, 20)
    for _ in range(7):
        await host.sample(20)
        assert not host.hit
    assert await host.sample(20) == 20 and host.hit
    assert await host.sample(19) == 19 and not host.hit
    assert await host.sample(-20) == -20 and not host.hit
    await host.command(7, 255)
    assert host.valid and await host.result() == -20
    await host.command(4, 0xC0)
    assert await host.sample(20) == 20 and host.hit
    dut.ui_in.value = 31
    dut.uio_in.value = 1
    await host.tick()
    for _ in range(8):
        await host.tick()
    assert host.ready and host.valid and await host.result() == 31
    dut.uio_in.value = 1
    await host.tick()
    assert not host.ready and not host.valid
    dut.uio_in.value = 0
    for _ in range(8):
        await host.tick()
    assert host.ready and host.valid
