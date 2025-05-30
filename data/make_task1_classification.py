import os
import json
import random
from PIL import Image

def crop_image_from_labelme(raw_file, external_file, out_file):
    os.makedirs(out_file, exist_ok=True)
    files = [item.path for item in os.scandir(raw_file) if item.is_file()]
    img_files = [f for f in files if f.endswith("jpg")]
    label_files = [f for f in files if f.endswith("json")]
    img_files.sort()
    label_files.sort()
    pat_id = [str(i) for i in range(1, 276)]
    
    externals = [item.path for item in os.scandir(external_file) if item.is_file()]
    img_external = [f for f in externals if f.endswith("jpg")]
    label_external = [f for f in externals if f.endswith("json")]
    img_external.sort()
    label_external.sort()
    external_id = list(range(len(img_external)))

    random.seed(75734)
    # train = 0.64 val = 0.16 test = 0.2
    random.shuffle(pat_id)
    train = pat_id[:round(0.64*len(pat_id))]
    val = pat_id[round(0.64*len(pat_id)):round(0.8*len(pat_id))]
    fold1 = pat_id[:round(0.16*len(pat_id))]
    fold2 = pat_id[round(0.16*len(pat_id)):round(0.32*len(pat_id))]
    fold3 = pat_id[round(0.32*len(pat_id)):round(0.48*len(pat_id))]
    fold4 = pat_id[round(0.48*len(pat_id)):round(0.64*len(pat_id))]
    fold5 = pat_id[round(0.64*len(pat_id)):round(0.8*len(pat_id))]
    test = pat_id[round(0.8*len(pat_id)):]
    test.sort()
    print(test)
    
    random.shuffle(external_id)
    train_external = external_id[:round(0.8*len(external_id))]
    val_external = external_id[round(0.8*len(external_id)):]
    fold1_external = external_id[:round(0.2*len(external_id))]
    fold2_external = external_id[round(0.2*len(external_id)):round(0.4*len(external_id))]
    fold3_external = external_id[round(0.4*len(external_id)):round(0.6*len(external_id))]
    fold4_external = external_id[round(0.6*len(external_id)):round(0.8*len(external_id))]
    fold5_external = external_id[round(0.8*len(external_id)):]
    # train_external.sort()
    # val_external.sort()
    # print(train_external)
    # print(val_external)
    # print(img_external)
    # exit()

    test_label = {}
    
    # split_compose = {"train":train, "val":val, "test":test}
    # split_external = {"train":train_external, "val":val_external, "test":[]}
    # for split in ["train", "val", "test"] :
    split_compose = {"fold1":fold1, "fold2":fold2, "fold3":fold3, "fold4":fold4, "fold5":fold5, "test":test}
    split_external = {"fold1":fold1_external, "fold2":fold2_external, "fold3":fold3_external, "fold4":fold4_external, "fold5":fold5_external, "test":[]}
    for split in ["fold1", "fold2", "fold3", "fold4", "fold5", "test"] :
        os.makedirs(os.path.join(out_file, split, "Y"), exist_ok=True)
        os.makedirs(os.path.join(out_file, split, "N"), exist_ok=True)

        for i in range(len(img_files)) :
            filename = os.path.split(img_files[i])[-1]
            if filename.split("R")[0][1:] not in split_compose[split] :
                continue
            
            image = Image.open(img_files[i])
            
            with open(label_files[i], "r") as f:
                labels = json.load(f)
            
            for j in range(len(labels["shapes"])) :
                label = labels["shapes"][j]
                
                x1 = label["points"][0][0]
                x2 = label["points"][1][0]
                y1 = label["points"][0][1]
                y2 = label["points"][1][1]
                
                x_min = int(min(x1, x2))
                x_max = int(max(x1, x2))
                y_min = int(min(y1, y2))
                y_max = int(max(y1, y2))
                x_delta = int((x_max - x_min) * 0.2)
                y_delta = int((y_max - y_min) * 0.2)
                
                x_displacement = list(range(-x_delta, x_delta))
                y_displacement = list(range(-y_delta, y_delta))
                random.shuffle(x_displacement)
                random.shuffle(y_displacement)
                
                category = label["label"]
                
                img_crop = image.crop((x_min, y_min, x_max, y_max))
                
                img_crop.save(os.path.join(out_file, split, category, f"{filename.split('.')[0]}_{j}.jpg"))
                
                if split == "test" :
                    test_label[f"{filename.split('.')[0]}_{j}"] = [category, (x_min+x_max) / 2]
                    continue

                if category == "Y" :
                    aug_size = 6
                else :
                    aug_size = 1
                
                for k in range(aug_size) :
                    xx_min = x_min + x_displacement[k]
                    yy_min = y_min + y_displacement[k]
                    xx_max = x_max + x_displacement[-k]
                    yy_max = y_max + y_displacement[-k]
                    if xx_min < 0 :
                        xx_min = 0
                    if yy_min < 0 :
                        yy_min = 0
                    if xx_min >= image.height :
                        xx_min = image.height-1
                    if yy_min >= image.width :
                        yy_min = image.width-1
                
                    img_crop = image.crop((xx_min, yy_min, xx_max, yy_max))
                    
                    img_crop.save(os.path.join(out_file, split, category, f"{filename.split('.')[0]}_{j}_aug{k+1}.jpg"))
        
        for i in range(len(img_external)) :
            filename = os.path.split(img_external[i])[-1]
            if i not in split_external[split] :
                continue
            
            image = Image.open(img_external[i])
            
            with open(label_external[i], "r") as f:
                labels = json.load(f)
                
            for j in range(len(labels["shapes"])) :
                label = labels["shapes"][j]
                
                x1 = label["points"][0][0]
                x2 = label["points"][1][0]
                y1 = label["points"][0][1]
                y2 = label["points"][1][1]
                
                x_min = int(min(x1, x2))
                x_max = int(max(x1, x2))
                y_min = int(min(y1, y2))
                y_max = int(max(y1, y2))
                x_delta = int((x_max - x_min) * 0.2)
                y_delta = int((y_max - y_min) * 0.2)
                
                x_displacement = list(range(-x_delta, x_delta))
                y_displacement = list(range(-y_delta, y_delta))
                random.shuffle(x_displacement)
                random.shuffle(y_displacement)
                
                category = label["label"]
                
                img_crop = image.crop((x_min, y_min, x_max, y_max))
                
                img_crop.save(os.path.join(out_file, split, category, f"{filename.split('.')[0]}_{j}.jpg"))
                
                if category == "Y" :
                    aug_size = 2
                else :
                    aug_size = 2

                for k in range(aug_size) :
                    xx_min = x_min + x_displacement[k]
                    yy_min = y_min + y_displacement[k]
                    xx_max = x_max + x_displacement[-k]
                    yy_max = y_max + y_displacement[-k]
                    if xx_min < 0 :
                        xx_min = 0
                    if yy_min < 0 :
                        yy_min = 0
                    if xx_min >= image.height :
                        xx_min = image.height-1
                    if yy_min >= image.width :
                        yy_min = image.width-1
                
                    img_crop = image.crop((xx_min, yy_min, xx_max, yy_max))
                    
                    img_crop.save(os.path.join(out_file, split, category, f"{filename.split('.')[0]}_{j}_aug{k+1}.jpg"))
        
        with open(f"{out_file}/test_label.json","w") as f:
            json.dump(test_label, f, indent=4)


if __name__ == '__main__':
    
    crop_image_from_labelme(raw_file='data/raw_data/Task1_labelme',
                            external_file='data/raw_data/origin_T1/origin',
                            out_file='data/dataset/Task1_crop_balanced_5fold')