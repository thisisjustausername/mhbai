# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai and pdf_reader.
#
# For usage please contact the developer.

import json
import re
import zlib

class Pdf:
    """
    reads pdfs and extracts information
    """

    def __init__(self, pdf_path: str):
        """
        initializes class variables
        Parameters:
            pdf_path (str): path to pdf file
        """
        self.path: str = pdf_path
        self.content: bytes = self.read_content()

    def read_content(self) -> bytes:
        """
        reads a pdf
        Returns: 
            bytes: the content of the pdf
        """
        with open(self.path, 'rb') as file:
            data = file.read()
        return data

    def extract_objects(self, additional_bytes: int=100000) -> list:
        """
        finds the xref to each object and then extracts that object
        Parameters: 
            dditional_bytes (int): how many bytes to read ahead of start of object in order to select the whole object
        Returns: 
            List[Dict[str, str | bytes | int]]: list of objects
        """

        # find the start of xref
        # start_xref the index of the first char after the last match
        # print(b'xref' in self.content)
        start_xref = int(list(re.finditer(rb'startxref\s+(\d+)', self.content))[0].group(1))
        # print([i for i in list(re.finditer(rb'startxref\s+(\d+)', self.content))if self.content[int(i.group(1)):].startswith(b'xref')])
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

            # extract important information about objects
            offset = int(entry[0:10])
            generation = int(entry[11:16])
            in_use = entry[17:18].decode('ascii')

            next_100k = self.content[offset:offset + additional_bytes]  # read ahead

            # Find the `endobj` marker
            end_index = next_100k.find(b'endobj')
            if end_index == -1:
                xref_entries.append({
                    'obj_num': start_obj + i,
                    'offset': offset,
                    'generation': generation,
                    'in_use': in_use,
                    'information': f"The object may be longer than {additional_bytes} bytes."
                })
                continue

            # contains the entire data of the object
            object_data = next_100k[:end_index + len(b'endobj')]

            # if the object is encoded as a stream decode it
            stream_match = re.search(rb'stream\s*[\r\n]+(.*?)endstream', object_data, re.DOTALL)
            if stream_match:

                # first match is being saved as stream_raw
                stream_raw = stream_match.group(1)

                # trying to decode the stream, each stream holds the content of exactly a single page
                try:
                    # decompress the stream
                    stream_decompressed = zlib.decompress(stream_raw)

                    # decode the stream
                    stream_decoded = stream_decompressed.decode("latin1", errors="ignore")

                    # save information in a dict
                    xref_entries.append({'obj_num': start_obj + i,
                        'offset': offset,
                        'generation': generation,
                        'in_use': in_use,
                        'data': stream_decoded,
                        'information': "success"})

                except Exception as e: # if Exception occurs, save without "data"
                    xref_entries.append({
                        'obj_num': start_obj + i,
                        'offset': offset,
                        'generation': generation,
                        'in_use': in_use,
                        'information': f"The object is a stream but during decompression / decoding an error occured."
                    })
                    continue
            else: # if no stream matched, save this information
                xref_entries.append({'obj_num': start_obj + i,
                                     'offset': offset,
                                     'generation': generation,
                                     'in_use': in_use,
                                     'data': object_data.decode("latin1", errors="ignore"), # TODO works without decoding too, but for typechecking make it str, check whether this actually works
                                     'information': "success - no stream"})
        # return xref_entries
        return xref_entries