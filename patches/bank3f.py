from assembler import ASM
import utils


def addBank3F(rom):
    # Bank3F is used to initialize the tile data in VRAM:1 at the start of the rom.
    # The normal rom does not use this tile data to maintain GB compatibility.
    rom.patch(0, 0x0150, ASM("""
        cp   $11 ; is running on Game Boy Color?
        jr   nz, notGBC
        ldh  a, [$FF4d]
        and  $80 ; do we need to switch the CPU speed?
        jr   nz, speedSwitchDone
        ; switch to GBC speed
        ld   a, $30
        ldh  [$FF00], a
        ld   a, $01
        ldh  [$FF4d], a
        xor  a
        ldh  [$FFff], a
        stop
        db $00

    speedSwitchDone:
        xor  a
        ldh  [$FF70], a
        ld   a, $01 ; isGBC = true
        jr   Init

    notGBC:
        xor  a ; isGBC = false
    Init:
        """), ASM("""
        ; Check if we are a color gameboy, we require a color version now.
        cp $11
        jr nz, notGBC

        ; Switch to bank $3F to run our custom initializer
        ld   a, $3F
        ld   [$2100], a
        call $4000
        ; Switch back to bank 0 after loading our own initializer
        ld   a, $01
        ld   [$2100], a
        
        ; set a to 1 to indicate GBC
        ld   a, $01
        jr Init
    notGBC:
        xor a
    Init:
        """), fill_nop=True)

    rom.patch(0x3F, 0x0000, "00" * 0x200, ASM("""
        ; switch speed
        ld   a, $30
        ldh  [$FF00], a
        ld   a, $01
        ldh  [$FF4d], a
        xor  a
        ldh  [$FFff], a
        stop
        db $00

        ; Switch VRAM bank
        ld   a, $01
        ldh  [$FF4F], a

        call $28CF ; display off

        ; Use the GBC DMA to transfer our tile data
        ld   a, $68
        ldh  [$FF51], a
        ld   a, $00
        ldh  [$FF52], a

        ld   a, $80
        ldh  [$FF53], a
        ld   a, $00
        ldh  [$FF54], a

        ld   a, $7F
        ldh  [$FF55], a

    waitTillTransferDone:
        ldh  a, [$FF55]
        and  $80
        jr z, waitTillTransferDone

        ld   a, $70
        ldh  [$FF51], a
        ld   a, $00
        ldh  [$FF52], a

        ld   a, $88
        ldh  [$FF53], a
        ld   a, $00
        ldh  [$FF54], a

        ld   a, $7F
        ldh  [$FF55], a

    waitTillTransferDone2:
        ldh  a, [$FF55]
        and  $80
        jr z, waitTillTransferDone2

        ld   a, $68
        ldh  [$FF51], a
        ld   a, $00
        ldh  [$FF52], a

        ld   a, $90
        ldh  [$FF53], a
        ld   a, $00
        ldh  [$FF54], a

        ld   a, $7F
        ldh  [$FF55], a

    waitTillTransferDone3:
        ldh  a, [$FF55]
        and  $80
        jr z, waitTillTransferDone3

        ; Switch VRAM bank back
        ld   a, $00
        ldh  [$FF4F], a

        ; Switch the display back on, else the later code hangs
        ld   a, $80
        ldh  [$FF40], a

    speedSwitchDone:
        xor  a
        ldh  [$FF70], a
        
        ; Enable the timer to run 32 times per second
        xor  a
        ldh  [$FF06], a
        ld   a, $04
        ldh  [$FF07], a

        ; Set SB to $FF to indicate we have no data from hardware
        ld   a, $FF
        ldh  [$FF01], a
        ret
        """), fill_nop=True)

    # Copy all normal item graphics
    rom.banks[0x3F][0x2800:0x2B00] = rom.banks[0x2C][0x0800:0x0B00]  # main items
    rom.banks[0x3F][0x2B00:0x2C00] = rom.banks[0x2C][0x0C00:0x0D00]  # overworld key items
    rom.banks[0x3F][0x2C00:0x2D00] = rom.banks[0x32][0x3D00:0x3E00]  # dungeon key items
    # Create ruppee for palettes 0-3
    rom.banks[0x3F][0x2B80:0x2BA0] = rom.banks[0x3F][0x2A60:0x2A80]
    for n in range(0x2B80, 0x2BA0, 2):
        rom.banks[0x3F][n+1] ^= rom.banks[0x3F][n]

    # Create capacity upgrade arrows
    rom.banks[0x3F][0x2A30:0x2A40] = utils.createTileData("""
   33
  3113
 311113
33311333
  3113
  3333
""")
    rom.banks[0x3F][0x2A20:0x2A30] = rom.banks[0x3F][0x2A30:0x2A40]
    for n in range(0x2A20, 0x2A40, 2):
        rom.banks[0x3F][n] |= rom.banks[0x3F][n + 1]

    # Add the slime key and mushroom which are not in the above sets
    rom.banks[0x3F][0x2CC0:0x2D00] = rom.banks[0x2C][0x28C0:0x2900]
    # Add tunic sprites as well.
    rom.banks[0x3F][0x2C80:0x2CA0] = rom.banks[0x35][0x0F00:0x0F20]

    # Add the bowwow sprites
    rom.banks[0x3F][0x2D00:0x2E00] = rom.banks[0x2E][0x2400:0x2500]

    # Zol sprites, so we can have zol anywhere from a chest
    rom.banks[0x3F][0x2E00:0x2E60] = rom.banks[0x2E][0x1120:0x1180]
    # Patch gel(zol) entity to load sprites from the 2nd bank
    rom.patch(0x06, 0x3C09, "5202522254025422" "5200522054005420", "600A602A620A622A" "6008602862086228")
    rom.patch(0x07, 0x329B, "FFFFFFFF" "FFFFFFFF" "54005420" "52005220" "56005600",
                            "FFFFFFFF" "FFFFFFFF" "62086228" "60086028" "64086408")
    rom.patch(0x06, 0x3BFA, "56025622", "640A642A");


    # Cucco
    rom.banks[0x3F][0x2E80:0x2F00] = rom.banks[0x32][0x2500:0x2580]
    # Patch the cucco graphics to load from 2nd vram bank
    rom.patch(0x05, 0x0514,
              "5001" "5201" "5401" "5601" "5221" "5021" "5621" "5421",
              "6809" "6A09" "6C09" "6E09" "6A29" "6829" "6E29" "6C29")
    # Song symbols
    rom.banks[0x3F][0x2F00:0x2F60] = utils.createTileData("""


     ...
  . .222
 .2.2222
.22.222.
.22222.3
.2..22.3
 .33...3
 .33.3.3
 ..233.3
.22.2333
.222.233
 .222...
  ...
""" + """


      ..
     .22
    .223
   ..222
  .33.22
  .3..22
  .33.33
   ..23.
  ..233.
 .22.333
.22..233
 ..  .23
      ..
""" + """


    ...
   .222.
  .2.332
  .23.32
  .233.2
 .222222
.2222222
.2..22.2
.2.3.222
.22...22
 .2333..
  .23333
   .....""", " .23")

    # Ghost
    rom.banks[0x3F][0x2F60:0x2FE0] = rom.banks[0x32][0x1800:0x1880]

    # Instruments
    rom.banks[0x3F][0x3000:0x3200] = rom.banks[0x31][0x1000:0x1200]
    # Patch the egg song event to use the 2nd vram sprites
    rom.patch(0x19, 0x0BAC,
        "5006520654065606"
        "58065A065C065E06"
        "6006620664066606"
        "68066A066C066E06",
        "800E820E840E860E"
        "880E8A0E8C0E8E0E"
        "900E920E940E960E"
        "980E9A0E9C0E9E0E"
    )

    # Rooster
    rom.banks[0x3F][0x3200:0x3300] = rom.banks[0x32][0x1D00:0x1E00]
    rom.patch(0x19, 0x19BC,
              "42234023" "46234423" "40034203" "44034603" "4C034C23" "4E034E23" "48034823" "4A034A23",
              "A22BA02B" "A62BA42B" "A00BA20B" "A40BA60B" "AC0BAC2B" "AE0BAE2B" "A80BA82B" "AA0BAA2B")
    # Replace some main item graphics with the rooster
    rom.banks[0x2C][0x0900:0x0940] = utils.createTileData(utils.tileDataToString(rom.banks[0x32][0x1D00:0x1D40]), " 321")

    # Trade sequence items
    rom.banks[0x3F][0x3300:0x3640] = rom.banks[0x2C][0x0400:0x0740]
