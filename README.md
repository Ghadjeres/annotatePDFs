# annotatePDFs
Add URIs provided by a .yaml to PDFs

Clone this repo:
`git clone git@github.com:Ghadjeres/annotatePDFs.git`


Install JohnMulligan's fork of pyPDF2
(from git@github.com:JohnMulligan/PyPDF2.git)

`cd annotatePDFs/PyPDF2`

`python setup.py install`

Test with:
`python annotatePDFs.py example/pdf_dir example/dict.yaml`

Uses pdftotext to generate bounding boxes.
There are some issues with pdftotext.
