import sys
import struct
import zlib
import argparse
import os

def decompress(data,endianness): # decompress saveData.ms using zlib 

    if len(data) < 8:
        raise ValueError("File must be at least 8 bytes long")
    
    if endianness == "little":
        headerPadding, decompressSize = struct.unpack("<II", data[:8]) # read in first 8 bytes as two unsigned ints.
    else:
        headerPadding, decompressSize = struct.unpack(">II", data[:8])


    print(f"Header Zeros: {headerPadding}") # should be 0
    print(f"Decompress Size: {decompressSize}") # should be decompressed size

    compressed = data[8:] # decompress everything after using zlib
    decompressed = zlib.decompress(compressed)

    print(f"Decompressed {len(decompressed)} bytes")
    print("")

    return decompressed

def LittleToBig(data): # import little endian format and convert to big endian format
    saveData = bytearray(data)

    tableOffset, numEntries = struct.unpack("<II", data[:8]) # read in the first 8 bytes of uncompressed data as unsigned ints.
    minVersion, currVersion = struct.unpack("<HH", data[8:12])

    entrySize = 144
    saveSize = len(data)

    if tableOffset < saveSize and numEntries > 0 and numEntries < 10000 and tableOffset + numEntries * entrySize <= saveSize:

        print(f"found {numEntries} entries in table at {hex(tableOffset)}")
        print("")

        for i in range(numEntries):
            entryOffset = tableOffset + i * entrySize
            tableEntry = data[entryOffset:entryOffset + entrySize]

            fileName = tableEntry[:128]
            fileLength = struct.unpack("<I", tableEntry[128:132])[0]
            fileOffset = struct.unpack("<I", tableEntry[132:136])[0]
            fileLastModified = struct.unpack("<Q", tableEntry[136:144])[0]

            print(f"At {hex(entryOffset)}, found table entry for:")
            print(f"Name:               {fileName.decode('utf-16-le')}")
            print(f"Length:             {fileLength} bytes")
            print(f"Position In File:   {hex(fileOffset)}")
            print(f"Last Modified:      {fileLastModified}")

            newFileEntry = struct.pack(">128sIIQ", fileName.decode('utf-16-le').encode('utf-16-be'), fileLength, fileOffset, fileLastModified)

            print(f"Writing new table entry at {hex(entryOffset)}.")
            print("")

            saveData[entryOffset:entryOffset + entrySize] = newFileEntry

        saveData[:8] = struct.pack(">II", tableOffset, numEntries)
        saveData[8:12] = struct.pack(">HH", minVersion, currVersion)

        return saveData
    
    else:

        print(f"DEBUG: {numEntries}")

        if tableOffset > saveSize:
            print("Error: table out of bounds.")
            
        
        if tableOffset + numEntries * entrySize <= saveSize:
            print("Error: table does not reach to end of file.")

        raise ValueError(f"Did not pass file checks.")

def BigToLittle(data): # convert big endian format to little endian

    saveData = bytearray(data)

    tableOffset, numEntries = struct.unpack(">II", data[:8]) # read in the first 8 bytes of uncompressed data as unsigned ints.
    minVersion, currVersion = struct.unpack(">HH", data[8:12])

    entrySize = 144
    saveSize = len(data)

    if tableOffset < saveSize and numEntries > 0 and numEntries < 10000 and tableOffset + numEntries * entrySize <= saveSize:

        print(f"found {numEntries} entries in table at {hex(tableOffset)}")
        print("")

        for i in range(numEntries):
            entryOffset = tableOffset + i * entrySize
            tableEntry = data[entryOffset:entryOffset + entrySize]

            fileName = tableEntry[:128]
            fileLength = struct.unpack(">I", tableEntry[128:132])[0]
            fileOffset = struct.unpack(">I", tableEntry[132:136])[0]
            fileLastModified = struct.unpack(">Q", tableEntry[136:144])[0]

            print(f"At {hex(entryOffset)}, found table entry for:")
            print(f"Name:               {fileName.decode('utf-16-be')}")
            print(f"Length:             {fileLength} bytes")
            print(f"Position In File:   {hex(fileOffset)}")
            print(f"Last Modified:      {fileLastModified}")

            newFileEntry = struct.pack("<128sIIQ", fileName.decode('utf-16-be').encode('utf-16-le'), fileLength, fileOffset, fileLastModified)

            print(f"Writing new table entry at {hex(entryOffset)}.")
            print("")

            saveData[entryOffset:entryOffset + entrySize] = newFileEntry

        saveData[:8] = struct.pack("<II", tableOffset, numEntries)
        saveData[8:12] = struct.pack("<HH", minVersion, currVersion)

        return saveData
    
    else:

        print(f"DEBUG: {numEntries}")

        if tableOffset > saveSize:
            print("Error: table out of bounds.")
            
        
        if tableOffset + numEntries * entrySize <= saveSize:
            print("Error: table does not reach to end of file.")

        raise ValueError(f"Did not pass file checks.")

def compress(data,endianness): # compress data using zlib 

    headerPadding = 0
    decompressSize = len(data)
    print("New Header:")
    print(f"Header zeros: {headerPadding}")
    print(f"Decompress Size: {decompressSize}")
    print("")

    zlibCompressed = zlib.compress(data)

    if endianness == "little":
        header = struct.pack("<II", headerPadding, decompressSize)
    else:
        header = struct.pack(">II", headerPadding, decompressSize)

    savegame = header + zlibCompressed

    return savegame

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert between Legacy Console Edition saveData.ms and savegame.dat formats.")
    parser.add_argument("file", help="Path to file")
    parser.add_argument("--to-ms", action="store_true", help="Convert from savegame.dat to saveData.ms.")
    parser.add_argument("--to-wii", action="store_true", help="Convert from saveData.ms to savegame.wii.")
    args = parser.parse_args()

    if args.to_ms and args.to_wii:
        print("Incorrect argument usage.")
        sys.exit(1)
    
    elif args.to_ms:
        with open(args.file, "rb") as f:
            data = f.read()

        saveData = decompress(data, "big")

        try:
            convertedSaveData = BigToLittle(saveData)
        except ValueError as e:
            print(f"Error: {e}")

        outputSaveData = compress(convertedSaveData, "little")

        with open("saveData.ms", "wb") as f:
            f.write(outputSaveData)

    elif args.to_wii:
        with open(args.file, "rb") as f:
            data = f.read()

        saveData = decompress(data, "little")

        try:
            convertedSaveData = LittleToBig(saveData)
        except ValueError as e:
            print(f"Error: {e}")
        
        outputSaveData = compress(convertedSaveData, "big")
        
        with open("savegame.wii", "wb") as f:
            f.write(outputSaveData)

    else:
        print("Not enough arguments.")
        sys.exit(1)    
