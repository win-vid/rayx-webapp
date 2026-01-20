import os


def remove_file(savePath, rml_file):
    """
    Removes a file from the server.
    """

    path = os.path.join(savePath, rml_file.filename)
        
    try:
        os.remove(path)
    except:
        print("File could not be found or removed.")

def save_file(savePath, rml_file):
    """
    Saves a file on the server.
    """
    
    path = os.path.join(savePath, rml_file.filename)
    rml_file.save(path)