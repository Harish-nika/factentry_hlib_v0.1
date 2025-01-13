import sys
sys.path.append('/home/harish/intern')
from factentry_hlib.doc_analyser import DocAnalyzer

# Initialize DocAnalyzer (you can set the input folder and output directory)
input_folder = "/home/harish/intern/factentry_hlib/tests"
output_dir = "/home/harish/intern/factentry_hlib/doc_analyser/output"

doc_analyzer = DocAnalyzer(input_folder=input_folder, output_dir=output_dir)

# Analyze a single PDF
pdf_path = "/home/harish/intern/factentry_hlib/tests/P21583050-P21221830-P21643722.pdf"
result = doc_analyzer.analyze_pdf(pdf_path)

# Output the result
print(result)
