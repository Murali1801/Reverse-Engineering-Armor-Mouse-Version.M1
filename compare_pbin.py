import os

FILE_1 = "./Data/Default.pbin"
FILE_2 = "./Data/Profile-yellow.pbin"

if not os.path.exists(FILE_1) or not os.path.exists(FILE_2):
    print("❌ Error: Make sure both .pbin files are in this folder!")
    exit()

with open(FILE_1, "rb") as f1, open(FILE_2, "rb") as f2:
    data1 = f1.read()
    data2 = f2.read()

print(f"📊 {FILE_1} Size: {len(data1)} bytes")
print(f"📊 {FILE_2} Size: {len(data2)} bytes")

if len(data1) != len(data2):
    print("⚠️ Warning: The files are different sizes! The comparison might be shifted.")

print("\n--- HEX DIFFERENCE REPORT ---")
print("Offset | Default | New Profile")
print("------------------------------")

diff_count = 0
# Compare up to the length of the shorter file
min_len = min(len(data1), len(data2))

for i in range(min_len):
    if data1[i] != data2[i]:
        # Print the memory offset and the hex values
        print(f"0x{i:04X} |   {data1[i]:02X}    |    {data2[i]:02X}")
        diff_count += 1

print("------------------------------")
print(f"✅ Found {diff_count} byte differences.")
print("👉 COPY AND PASTE THIS OUTPUT TO THE AI!")