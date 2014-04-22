import base64, struct, zlib, sys
from xml.dom import minidom

new_file_extension='.merged'

print sys.argv

if len(sys.argv) <= 1 or sys.argv[1] == '-h' or sys.argv[1] == '--help' or sys.argv[1] == '/?' or sys.argv[1] == '/help':
	print 'python TMXMerge.py [--leapOfFaith] refFile targetFile [targetFile]*'
	print '\tUpdates targetFile(s) with tilesets in refFile'
	print '\t--leapOfFaith\tWrites new files over source files'
	exit(0)

arg_index = 1
if sys.argv[1] == '--leapOfFaith':
	new_file_extension=''
	arg_index+=1
	
if len(sys.argv) <= arg_index+1:
	print 'Error: Expected at least two files. Use -h for usage.'
	exit(1)

template = sys.argv[arg_index]
filesToMerge = sys.argv[arg_index+1:]

document = minidom.parse(template)
new_tilesets = document.getElementsByTagName ('tileset')
new_tilesets_ids = {}
for tileset in new_tilesets:
	new_tilesets_ids[tileset.getAttribute('name')] = int(tileset.getAttribute('firstgid'))

for file in filesToMerge:
	document = minidom.parse(file)
	old_tilesets = document.getElementsByTagName('tileset')
	old_tilesets_ids = {}
	tilesets_deltas = {}
	for tileset in old_tilesets:
		name = tileset.getAttribute('name')
		old_tilesets_ids[name] = int(tileset.getAttribute('firstgid'))
		if not new_tilesets_ids.has_key(name):
			print 'WARNING : File '+file+' references tileset '+name+' but that tileset is missing from new template.'
		else:
			tilesets_deltas[name] = new_tilesets_ids[name] - old_tilesets_ids[name]
	
	layers = document.getElementsByTagName('layer')
	first_layer = layers[0]
	for layer in layers:
		attr_text = layer.getElementsByTagName('data')[0].childNodes[0].data
		width = int(layer.getAttribute('width'))
		height = int(layer.getAttribute('height'))
		data = zlib.decompress(base64.b64decode(attr_text))
		numbers = struct.unpack ('<'+('I'*width*height), data)
		new_numbers = []
		for number in numbers:
			if (number == 0):
				new_numbers.append(0)
				continue
			flipdata = number & (0x80000000 | 0x40000000 | 0x20000000)
			gid = number & ~(0x80000000 | 0x40000000 | 0x20000000)
			tileset = ''
			tileset_id = 0
			for name in old_tilesets_ids.keys():
				if (old_tilesets_ids[name] <= gid) and (old_tilesets_ids[name] > tileset_id):
					tileset = name
					tileset_id = old_tilesets_ids[name]
			gid += tilesets_deltas[tileset]
			new_numbers.append(gid | flipdata)
		newdata = struct.pack('<'+('I'*width*height), *new_numbers)
		layer.getElementsByTagName('data')[0].childNodes[0].data = base64.b64encode (zlib.compress(newdata))
	
	map = document.getElementsByTagName('map')[0]
	for tileset in map.getElementsByTagName('tileset'):
		tileset.unlink()
		map.removeChild(tileset)
	
	for tileset in new_tilesets:
		map.insertBefore(tileset, first_layer)
	
	f = open(file+new_file_extension, 'w')
	f.write(document.toxml())
