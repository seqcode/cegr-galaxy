#!/usr/bin/env python
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--input', dest='input', help='Input gff dataset')
args = parser.parse_args()

# Create the collection output directory.
collection_path = (os.path.join(os.getcwd(), 'output'))
# Keep track of motif occurrences.
header_line = None
motif_ids = []
file_handles = []
for line in open(args.input, 'r'):
    if line.startswith('#'):
        if header_line is None:
            header_line = line
        continue
    items = line.split('\t')
    attribute = items[8]
    attributes = attribute.split(';')
    name = attributes[0]
    motif_id = name.split('=')[1]
    file_name = os.path.join(collection_path, 'MOTIF%s.gff' % motif_id)
    if motif_id in motif_ids:
        i = motif_ids.index(motif_id)
        fh = file_handles[i]
        fh.write(line)
    else:
        fh = open(file_name, 'wb')
        if header_line is not None:
            fh.write(header_line)
        fh.write(line)
        motif_ids.append(motif_id)
        file_handles.append(fh)
for file_handle in file_handles:
    file_handle.close()
