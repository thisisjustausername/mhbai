import json
import re
import zlib

class Pdf:
    def __init__(self, pdf_path: str):
        self.path = pdf_path
        self.content = self.read_content()

    def read_content(self) -> bytes:
        """
        read_content \n
        reads a pdf
        :return: the content of the pdf
        :rtype: bytes
        """
        with open(self.path, 'rb') as file:
            data = file.read()
        return data

    def extract_objects(self) -> list:
        """
        extract_objects \n
        finds the xref to each object and then extracts that object
        :return: list of objects
        :rtype: list
        """

        # find the start of xref
        # start_xref the index of the first char after the last match
        start_xref = int(list(re.finditer(rb'startxref\s+(\d+)', self.content))[-1].group(1))
        xref_data = self.content[start_xref:]
        assert xref_data.startswith(b'xref')

        # find the xref header
        xref_header_match = re.match(rb'xref\s+(\d+)\s+(\d+)', xref_data)
        assert xref_header_match is not None

        # start object
        # index of the first object is saved as the first number in the pattern match
        start_obj = int(xref_header_match.group(1))

        # number of objects
        # number of elements is saved as the second number in the pattern match
        count = int(xref_header_match.group(2))

        # end
        header_end = xref_header_match.end()

        # body
        xref_body = xref_data[header_end:]

        # split the document into xref entries
        xref_entries = []
        for i in range(count):
            entry = xref_body[i * 20:(i + 1) * 20].strip(b'\n')
            if len(entry) < 18:
                continue  # skip invalid/incomplete lines

            offset = int(entry[0:10])
            generation = int(entry[11:16])
            in_use = entry[17:18].decode('ascii')
            xref_entries.append({
                'obj_num': start_obj + i,
                'offset': offset,
                'generation': generation,
                'in_use': in_use
            })