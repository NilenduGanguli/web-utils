import os
import random
import string
import zipfile
from lorem_text import lorem

def generate_lorem_ipsum(length):
    return lorem.paragraphs(length)

def generate_nested_zip(directory, levels, total_files, max_length,max_dir):
    if not os.path.exists(directory):
        os.makedirs(directory)

    def add_files_to_zip(zipf, remaining_files, current_level):
        print(remaining_files,levels,sep="  \  ")
        num_files = random.randint(1,2 if remaining_files else remaining_files )
        num_folders = random.randint(0,max_dir)

        if current_level<=levels :
            for _ in range(num_files):
                file_name = ''.join(random.choices(string.ascii_lowercase, k=8)) + ".pdf"
                content = generate_lorem_ipsum(random.randint(10, max_length))
                zipf.writestr(file_name, content.encode('utf-8'))

            for _ in range(num_folders):
                folder_name = "zip" + str(random.randint(1, 100)) + ".zip"
                with zipfile.ZipFile(folder_name, 'w') as sub_zip:
                    add_files_to_zip(sub_zip, remaining_files // num_folders if num_folders!=0 else remaining_files, current_level + 1)
                zipf.write(folder_name)
                os.remove(folder_name)

    with zipfile.ZipFile(os.path.join(directory, "nested_zip.zip"), 'w') as zipf:
        add_files_to_zip(zipf, total_files, 1)

target_directory = "./zip_payload/"
levels = 9
max_dir = 2
total_files = 100
max_length = 2000

generate_nested_zip(target_directory, levels, total_files, max_length,max_dir)
print("Nested zip file generated successfully at", os.path.join(target_directory, "nested_zip.zip"))
