# Function Calling Script
try:
    from ultralytics import YOLO
except:
    import os
    os.system('pip uninstall ultralytics')
    os.system('pip install ultralytics')
    from ultralytics import YOLO

from PIL import Image
import os
import stat
import shutil

def get_latest_path(root_dir):
  files={filename.split('train')[-1]:filename for filename in os.listdir(root_dir) if filename.startswith("train")}

  return files[max(files.keys())]


def remove_readonly(func, path, exc_info):
    """
    Error handler for rmtree to handle read-only files.
    func: the function (os.remove or os.rmdir) that raised the error
    path: the path that caused the error
    exc_info: exception information
    """
    # make the file writable
    os.chmod(path, stat.S_IWRITE)
    # retry the function
    func(path)


def get_weights():
    """
    Returns the path to the pre-trained weights for the food classification model.
    """
    
    if not os.path.exists("./weights/best.pt"):
        weights_dir = "./weights"
        dst = os.path.join(weights_dir, "best.pt")
        os.makedirs(weights_dir, exist_ok=True)
        try:
            os.system('git clone https://huggingface.co/GboyeStack/NigerFoodAi ./model_clone')
        except:
            raise Exception("Unable to download model weights. Please check your internet connection.")
        else:
            shutil.copytree('./model_clone/runs','./runs')
            shutil.rmtree('./model_clone',onerror=remove_readonly)
            weights_path=f"./runs/classify/{get_latest_path('./runs/classify')}/weights/last.pt"
            shutil.copy(weights_path,dst)
            shutil.rmtree('./runs',onerror=remove_readonly)

    return "./weights/best.pt"


def load_model(model_path: str):
    """
    Loads the food classification model from the specified path.
    """
    
    model = YOLO(model_path)

    return model


def classify_food_image(image) -> str:
    """
    Classifies a food image and returns the predicted food name.
    """
    # model_path = get_weights()

    classifier = load_model(model_path="./weights/best.pt")

    predicted_food = classifier.names[classifier(image)[0].probs.top1]

    return predicted_food
