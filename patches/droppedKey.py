from assembler import ASM


def fixDroppedKey(rom):
    # Patch the rendering code to use the dropped key rendering code.
    rom.patch(0x03, 0x1C99, None, ASM("""
        ld   a, $03
        call $3FF0
        jp $5CA6
    """))

    # Patch the key pickup code to use the chest pickup code.
    rom.patch(0x03, 0x248F, None, ASM("""
        ldh  a, [$F6] ; load room nr
        cp   $7C  ; L4 Side-view room where the key drops
        jr   nz, notSpecialSideView

        ld   hl, $D969 ; status of the room above the side-view where the key drops in dungeon 4 
        set  4, [hl]
notSpecialSideView:
        call $512A ; mark room as done
        
        ld   a, $01
        call $3FF0
        
        ldh  a, [$F1] ; Load active sprite variant
        cp   $1A
        jr   z, isAKey
        ld   a, $02
        call $3FF0
isAKey:
        ret
    """))
    rom.patch(0x03, 0x24B7, "3E", "3E")  # sanity check

    # Mark all dropped keys as keys by default.
    for n in range(0x400):
        rom.banks[0x3E][0x3800 + n] = 0x1A
    # Set the proper angler key by default
    rom.banks[0x3E][0x3800 + 0x0CE] = 0x12
    rom.banks[0x3E][0x3800 + 0x1F8] = 0x12
    # Set the proper bird key by default
    rom.banks[0x3E][0x3800 + 0x27A] = 0x14
    # Set the proper face key by default
    rom.banks[0x3E][0x3800 + 0x27F] = 0x13