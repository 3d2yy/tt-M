"""Fail CI if no tests ran, tests failed, or tests errored (also cocotb 1.x)."""
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
cases = root.findall('.//testcase')
assert cases, 'No test cases executed'
assert not root.findall('.//failure'), 'Simulation tests failed'
assert not root.findall('.//error'), 'Simulation tests errored'
print(f'{len(cases)} simulation tests passed')
