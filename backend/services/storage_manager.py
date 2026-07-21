import os
import shutil
import uuid

from config import STORAGE_DIR as CONFIG_STORAGE_DIR

STORAGE_DIR = str(CONFIG_STORAGE_DIR)


UPLOAD_DIR = os.path.join(
    STORAGE_DIR,
    "uploads"
)


OUTPUT_DIR = os.path.join(
    STORAGE_DIR,
    "outputs"
)



def initialize_storage():

    folders = [
        UPLOAD_DIR,
        OUTPUT_DIR
    ]

    for folder in folders:
        os.makedirs(
            folder,
            exist_ok=True
        )



def save_upload(file_path):

    initialize_storage()


    extension = os.path.splitext(file_path)[1]


    filename = (
        str(uuid.uuid4())
        +
        extension
    )


    destination = os.path.join(
        UPLOAD_DIR,
        filename
    )


    shutil.copy(
        file_path,
        destination
    )


    return destination



def save_output(
    file_path,
    model_name
):

    initialize_storage()


    model_folder = os.path.join(
        OUTPUT_DIR,
        model_name
    )


    os.makedirs(
        model_folder,
        exist_ok=True
    )


    extension = os.path.splitext(file_path)[1]


    filename = (
        str(uuid.uuid4())
        +
        extension
    )


    destination = os.path.join(
        model_folder,
        filename
    )


    shutil.copy(
        file_path,
        destination
    )


    return destination
