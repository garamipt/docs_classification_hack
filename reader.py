from striprtf.striprtf import rtf_to_text

with open("/home/igor/code/Hackatons/UFO_docs_classification/dataset/Договоры/agentskii-dogovor-utv-resheniem-pravleniia-gk-agentstvo.rtf") as infile:
    content = infile.read()
    text = rtf_to_text(content)
print(text)