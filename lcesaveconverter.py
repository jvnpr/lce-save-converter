import os
import sys
import argparse
import struct
import zlib

LITTLE_ENDIAN = 0
BIG_ENDIAN = 1

def ZlibDecomp(data,size):
    processData = data[8:]
    decompObj = zlib.decompressobj()
    decompData = decompObj.decompress(processData)

    if len(decompData) != size:
        raise ValueError("Size of decompressed data did not match header!")
    else:
        return decompData

def ZlibComp(data):
    processData = data
    compObj = zlib.compressobj()
    compData = compObj.compress(processData)
    compData += compObj.flush()
    return compData

def ProcessHeader(data, endian):
    if endian == 0:
        headerPadding, decompressSize = struct.unpack("<II", data[:8]) # read in first 8 bytes as two unsigned ints.
    else:
        headerPadding, decompressSize = struct.unpack(">II", data[:8])

    if headerPadding == 0:
        return decompressSize
    else:
        raise ValueError("Header padding is non zero value!")

def StitchHeader(data,size,endian):

    structEndianWrite = "<" # what endian format we need to output to the buffer (default little)

    if endian == 1: # reverse these if we're converting to big endian. 
        structEndianWrite = ">" # write out big endian
    
    buffer = bytearray()

    headerPadding = 0
    decompressedSize = size
    header = struct.pack(f"{structEndianWrite}II", headerPadding, decompressedSize)

    buffer = header + data
    return buffer


def ConvertDataToEndian(data,endian):

    dataBuffer = bytearray(data)

    structEndianRead = ">" # what endian format the file we're reading from has     (default big)
    structEndianWrite = "<" # what endian format we need to output to the buffer    (default little)
    textEncodingRead = "utf-16-be"
    textEncodingWrite = "utf-16-le"

    if endian == 1: # reverse these if we're converting to big endian. 
        structEndianRead = "<" # read in little endian
        structEndianWrite = ">" # write out big endian
        textEncodingRead = "utf-16-le"
        textEncodingWrite = "utf-16-be"

    tableOffset, numEntries, minVersion, currVersion = struct.unpack(f"{structEndianRead}IIHH", data[:12]) # read in the first 12 bytes of data: 2 unsigned 32bit ints and 2 unsigned 16 bit ints. 

    entrySize = 144 # FileSaveDataFormatV2 or whatever it's called im LAZY! 
    saveSize = len(dataBuffer)

    if tableOffset < saveSize and numEntries > 0 and numEntries < 10000 and tableOffset + numEntries * entrySize <= saveSize:

        print(f"found {numEntries} entries in table at {hex(tableOffset)}")
        print("")

        for i in range(numEntries):
            entryOffset = tableOffset + i * entrySize
            tableEntry = dataBuffer[entryOffset:entryOffset + entrySize]

            fileName = tableEntry[:128].decode(textEncodingRead).rstrip("\x00")
            fileLength = struct.unpack(f"{structEndianRead}I", tableEntry[128:132])[0]
            fileOffset = struct.unpack(f"{structEndianRead}I", tableEntry[132:136])[0]
            fileLastModified = struct.unpack(f"{structEndianRead}Q", tableEntry[136:144])[0]

            print(f"At {hex(entryOffset)}, found table entry for:")
            print(f"Name:               {fileName}")
            print(f"Length:             {fileLength} bytes")
            print(f"Position In File:   {hex(fileOffset)}")
            print(f"Last Modified:      {fileLastModified}")

            newFileEntry = struct.pack(f"{structEndianWrite}128sIIQ", fileName.encode(textEncodingWrite).ljust(128, b"\x00"), fileLength, fileOffset, fileLastModified)

            print(f"Writing new table entry at {hex(entryOffset)}.")
            print("")

            dataBuffer[entryOffset:entryOffset + entrySize] = newFileEntry

        dataBuffer[:12] = struct.pack(f"{structEndianWrite}IIHH", tableOffset, numEntries, minVersion, currVersion)

        return dataBuffer
    
    else:

        print(f"DEBUG: {numEntries}")

        raise ValueError(f"Did not pass file checks.")

def main():
    parser = argparse.ArgumentParser(description="Convert between Legacy Console Edition saveData.ms and savegame.wii formats.")

    parser.add_argument("-i", "--input", required=True, help="Input file")
    parser.add_argument("output", nargs="?", help="Output file")

    conversion = parser.add_mutually_exclusive_group(required=True)
    conversion.add_argument("--to-ms", action="store_true", help="Convert from savegame.dat to saveData.ms.")
    conversion.add_argument("--to-wii", action="store_true", help="Convert from saveData.ms to savegame.wii.")

    args = parser.parse_args()

    if args.output is None:
        if args.to_ms:
            args.output = "saveData.ms"
        elif args.to_wii:
            args.output = "savegame.wii"
        
    convertToEndian = LITTLE_ENDIAN
    convertFromEndian = BIG_ENDIAN

    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")

    with open(args.input, "rb") as f:
            inputFile = f.read()

    if args.to_wii:
        convertToEndian = BIG_ENDIAN
        convertFromEndian = LITTLE_ENDIAN

    decompressSize = ProcessHeader(inputFile,convertFromEndian) # data currently in big endian
    saveData = ZlibDecomp(inputFile,decompressSize)
    newSaveData = ConvertDataToEndian(saveData,convertToEndian) # convert to little endian
    compressedSaveData = ZlibComp(newSaveData)
    finalSaveData = StitchHeader(compressedSaveData,len(newSaveData),convertToEndian)
    

    with open(args.output, "wb") as f:
            f.write(finalSaveData)

if __name__ == "__main__":
    main()
