
import const
import util
import datasets
import commons
import test

import os
from os.path import join
from datetime import datetime
import argparse
import torch

######################################### SETUP #########################################
torch.autograd.set_detect_anomaly(True)
parser = argparse.ArgumentParser(description='pytorch-NetVlad', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

const.add_arguments(parser)
opt = parser.parse_args()

opt.outputFolder = os.path.join(const.runsPath, opt.expName, datetime.now().strftime('%b%d_%H-%M-%S'))

opt.logger = commons.Logger(folder=opt.outputFolder, filename=f"logger.txt")
opt.logger.log(f'Arguments: {opt}')
opt.rootPath = os.path.join(opt.allDatasetsPath, opt.rootPath)
opt.cuda = True
opt.device = "cuda"

commons.pause_while_running(opt.wait)

if opt.isDebug:
    opt.logger.log("!!! Questa è solo una prova (alcuni cicli for vengono interrotti dopo 1 iterazione), i risultati non sono attendibili !!!\n")

######################################### MODEL #########################################
opt.logger.log(f"=> Building model", False)
model = util.build_model(opt)

######################################### RESUME #########################################
best_score = 0
epoch = 0
if opt.resume:
    model_state_dict = torch.load(join(opt.resume, 'best_model.pth'))['state_dict']
    model.load_state_dict(model_state_dict, strict=False)
    epoch = torch.load(join(opt.resume, 'best_model.pth'))['epoch']
    best_score = torch.load(join(opt.resume, 'best_model.pth'))['best_score']

model = model.to(opt.device)

######################################### DATASETS #########################################
opt.logger.log(f"=> Evaluating model - Epoch: {epoch} - Best Recall@5: {best_score:.1f}")

recalls = [1, 5, 10, 20]

all_targets_recall_str = ""

if opt.scenario == 0:    
    source_test_set = datasets.WholeDataset(opt.rootPath, "val/gallery", f"val/queries")
    _, _, recalls_str  = test.test(opt, source_test_set, model)
    del _
    all_targets_recall_str += recalls_str
    opt.logger.log(f"Recalls on {source_test_set.name}: {recalls_str}")
    
    source_test_set = datasets.WholeDataset(opt.rootPath, "test/gallery", f"test/queries")
    _, previous_db_features, recalls_str  = test.test(opt, source_test_set, model)
    del _
    all_targets_recall_str += recalls_str
    opt.logger.log(f"Recalls on {source_test_set.name}: {recalls_str}")
    
    for i in range(5):
        target_test_set = datasets.WholeDataset(opt.rootPath, "test/gallery", f"test/queries_{i+1}")
        _, previous_db_features, recalls_str = test.test(opt, target_test_set, model, previous_db_features)
        opt.logger.log(f"Recalls on {target_test_set.name}: {recalls_str}")
        all_targets_recall_str += recalls_str
    
else:
    target_test_set = datasets.WholeDataset(opt.rootPath, "test/gallery", f"test/queries_{opt.scenario}")
    _, _, recalls_str = test.test(opt, target_test_set, model)
    del _
    opt.logger.log(f"Recalls on {target_test_set.name}: {recalls_str}")
    all_targets_recall_str += recalls_str

opt.logger.log(f"Recalls all targets: {all_targets_recall_str}")

