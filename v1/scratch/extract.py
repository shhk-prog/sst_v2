import urllib.request
import urllib.error
import pypdf
import io
import re

urls = [
    "https://aclanthology.org/2024.lrec-main.647.pdf",
    "https://openreview.net/pdf?id=uV8LGh2DCx",
    "https://aclanthology.org/2025.naacl-long.254.pdf",
    "https://proceedings.neurips.cc/paper_files/paper/2022/file/70c26937fbf3d4600b69a129031b66ec-Paper-Conference.pdf",
    "https://arxiv.org/pdf/2310.12808",
    "https://arxiv.org/pdf/2603.21705",
    "https://arxiv.org/pdf/2512.16245",
    "https://arxiv.org/pdf/2411.06824",
    "https://aclanthology.org/2025.acl-long.1055.pdf",
    "https://arxiv.org/pdf/2503.17239"
]

def extract_info(text):
    lines = text.split('\n')
    extracted = []
    capture = False
    for i, line in enumerate(lines):
        lower = line.lower()
        if re.search(r'(dataset|baseline|benchmark|compare|evaluate|experiment)', lower):
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            extracted.append(" ".join(lines[start:end]))
    return "\n---\n".join(extracted[:20]) # Limit to 20 matches

with open("scratch/summary.txt", "w") as f:
    for i, url in enumerate(urls):
        f.write(f"\n{'='*40}\nPaper {i+1}: {url}\n{'='*40}\n")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                pdf_file = io.BytesIO(response.read())
                reader = pypdf.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Extract sections like Abstract, Experiments
                info = extract_info(text)
                f.write(info)
        except Exception as e:
            f.write(f"Error: {e}\n")

print("Done")
