import os
from argparse import ArgumentParser
import errno
import numpy as np
import torch
from pytorch_lightning import Trainer, seed_everything
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from .model import Challenger
from torchsummary import summary

def main(hparams):
#     if hparams.gpus == 0:
#         raise ValueError(("Training on CPU is not supported, please run again "
#                           "on a system with GPU and '--gpus' > 0."))
    print("start")
    if hparams.seed is not None:
        seed = hparams.seed
    else:
        seed = np.random.randint(1, high=10000, size=1)[0]
    print(seed)
    seed_everything(seed)
    np.seterr(divide='ignore', invalid='ignore')
    
    slurm_id = os.environ.get("SLURM_JOBID")
    if slurm_id is None:
        version = None
    else:
        version = str(hparams.design +"_" + slurm_id)
    logger = TensorBoardLogger(hparams.logdir,
                               name=hparams.exp_name, #+"_{hparams.c1}"
                               version=version)
    checkpoint_path = os.path.join(logger.experiment.get_logdir(),
                                   "checkpoints",
                                   "aaaifinal_{epoch:02d}-{loss:.2e}-{roc_auc:.2f}")
    checkpoint_callback = ModelCheckpoint(filepath=checkpoint_path,
                                          save_top_k=5,
                                          monitor="val/roc_auc",
                                          mode="max")
    
    model = Challenger(hparams)
    print(hparams)
    print(model)

    
    trainer = Trainer.from_argparse_args(hparams, 
                                         checkpoint_callback=checkpoint_callback,
                                         logger=logger,
                                         deterministic=True)
    trainer.fit(model)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser = Challenger.add_model_specific_args(parser)
    parser = Trainer.add_argparse_args(parser)

    parser.add_argument("root_directory", type=str,
                        help="Directory containing images and segmentation masks.")
    
    parser.add_argument("clinical_data_path", type=str,
                        help="Path to CSV file containing the clinical data.")
    
    parser.add_argument("logdir", type=str,
                        help="Directory where training logs will be saved.")
    
    parser.add_argument("--cache_dir", type=str, default="./data/data_cache",
                        help="Directory where the preprocessed data will be saved.")
    
    parser.add_argument("--pred_save_path", type=str, default="./data/predictions/cnn.csv",
                        help="Directory where final predictions will be saved.")
    
    parser.add_argument("--num_workers", type=int, default=1,
                        help="Number of worker processes to use for data loading.")
    
    parser.add_argument("--exp_name", type=str, default="challenger",
                        help="Experiment name for logging purposes.")
    
    parser.add_argument ("--design", type=str, default="aaai_cnn",
                        help="Choose architecture design")
    
    parser.add_argument ("--seed", type=int, default=None,
                        help="Choose architecture design")
    

    hparams = parser.parse_args()
    try:
        main(hparams)
    except OSError as e:
        pass
    
