import os
import pandas as pd
from pyth.plugins.plaintext.writer import PlaintextWriter
from pyth.plugins.rtf15.reader import Rtf15Reader 
 
def parse_rtf(file_path): 
    # Read the RTF file 
    doc = Rtf15Reader.read(open(file_path, "rb")) 
 
    # Extract plain text from the document 
    text = PlaintextWriter.write(doc).getvalue() 
     
    return text 
 
# Example usage 

i = 0
names = ["Договоры", "Заявления", "Приказы", "Соглашения", "Уставы"]
inds = ["contract", "application", "order", "arrangement", "statute"]

for j in range(5):
    for entry in os.scandir(f"dataset/{names[j]}"):
        try:
            data_one = pd.DataFrame({"class": [], "text": []})
            text = parse_rtf(f"dataset/{names[j]}/" + entry.name)
            data_one.loc[i] = [inds[j], text]
            data_one.to_csv(
                    "dataset/dataset.csv",
                    mode="a",
                    index=False,
                    header=(i==0),
                )
            i+=1
        except:
            print(entry.name)