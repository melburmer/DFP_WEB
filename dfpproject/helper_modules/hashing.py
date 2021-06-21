
import os
import hashlib

def hash_file(file_path,size_in_mb=10):
	h = hashlib.sha1()

	with open(file_path, 'rb') as file:
		chunk = 0
		count = 0
		while chunk != b'' and count < 1024*size_in_mb: # read 10mb from data
			chunk = file.read(1024)
			h.update(chunk)
			count += 1


	return h.hexdigest()



def rename_by_hash(file_path):

	parent_folder, file_name = os.path.split(file_path)
	name, ext = file_name.split(".")
	hash_val = hash_file(file_path)
	name = str(hash_val) + "#" + name + "." + ext 
	os.rename(file_path,os.path.join(parent_folder,name))
	print("file renamed with hash value of " + str(hash_val))
 
 