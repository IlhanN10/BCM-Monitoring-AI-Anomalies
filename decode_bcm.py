import struct

raw = [
    61, 134, 3, 156,
    61, 53, 6, 176,
    61, 142, 18, 29,
    62, 116, 215, 4,
    62, 3, 128, 118,
    62, 111, 74, 65,
    66, 26, 102, 102,
    0, 128, 0, 0
]

for i in range(0, len(raw), 4):
    chunk = raw[i:i+4]
    value = struct.unpack(">f", bytes(chunk))[0]
    print(f"Wert {i//4 + 1}: {value}")