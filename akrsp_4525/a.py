file_path = "data.txt"  

result = []

try:
    with open(file_path, "r") as file:
        lines = file.read()
        segments = lines.split("\n\t\n")
        print(len(segments))
        for segment in segments:
            ms = []
            keep = ""
            segment = segment.strip()
            segment = segment.split("\n")
            
            for line in segment:
                line = line.strip()
                try:
                    uuid, label = line.split("\t")
                    if label == "Keep":
                        keep = uuid
                    elif label == "Merge":
                        ms.append(uuid)
                except:
                    #ooo
                    print("", end="")

            if keep != "":
                print("keep found, ms len = ", len(ms))
                for m in ms:
                    result.append(",".join([m, keep]))
            else:
                print("Keep NOT FOUND, ms len = ", len(ms))
                    
except FileNotFoundError:
    print(f"File not found: {file_path}")
    exit()

with open("output.csv", "w") as file:
    file.write('individual_uuid' + ','+ 'individual_uuid_to_merge_into' + "\n")
    for r in result:
        file.write(r + "\n")