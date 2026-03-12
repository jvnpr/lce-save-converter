# lce-save-converter
Python script to convert between saveData.ms and savegame.wii

saveData.ms -> savegame.wii might be working, but savegame.wii -> saveData.ms is for sure not atm. 

convert to .wii and not .dat because .dat uses zlib compression and .dat (at least on 360) uses lzx, which python does not have an existing library for. .wii can be converted to .dat and vice versa using MCC ToolChest
