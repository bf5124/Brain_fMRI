import torch
import torch.optim as optim
import torch.nn as nn
import multi_input_resnet3d 
import numpy as np
from mri_dataset import ThreeInputMRIDataset
from model_3d import train_multi_input, eval
import argparse
import os
import apex


if __name__ == "__main__":
    torch.cuda.set_device(0)

    # Parsing arguments
    parser = argparse.ArgumentParser(description='Multi-channel/input ResNet3D for regression')
    parser.add_argument('--data_dir1', help='Directory path for first dataset')
    parser.add_argument('--data_dir2', help='Directory path for second dataset (second and third are same)')
    parser.add_argument('--output_dir')
    parser.add_argument('--epoch', type=int, default=30)
    parser.add_argument('--train_batch_size', type=int, default=2)
    parser.add_argument('--valid_batch_size', type=int, default=4)
    parser.add_argument('--checkpoint_state', default='')
    parser.add_argument('--checkpoint_epoch', type=int, default=0)
    parser.add_argument('--checkpoint_opt', default='')
    parser.add_argument('--resize', type=int, default=0)
    parser.add_argument('--normalize', type=bool, default=False)
    parser.add_argument('--log', type=bool, default=False)
    parser.add_argument('--lr', type=float, default=0.01)
    parser.add_argument('--momentum', type=float, default=0.5)
    parser.add_argument('--optimizer', default='sgd', help='Optimizer type: adam, sgd')
    parser.add_argument('--sync_bn', default=False, help='Use sync batch norm or not (True/False)')
    args = parser.parse_args()

    model = multi_input_resnet3d.tri_input_resnet3D50(devices=[0,1,2,3])
    
    # Load from checkpoint, if available
    if args.checkpoint_state:
        saved_state = torch.load(args.checkpoint_state, map_location='cpu')
        model.load_state_dict(saved_state)
        print('Loaded model from checkpoint')

    # Convert async batch norm to sync batch norm, if applicable
    if args.sync_bn:
        model = apex.parallel.convert_syncbn_model(model)
        print('Using sync batch norm')

    # Load and create datasets
    train_img = np.load(os.path.join(args.data_dir1, 'train_data_img.npy'), allow_pickle=True)
    valid_img = np.load(os.path.join(args.data_dir1, 'valid_data_img.npy'), allow_pickle=True)
    test_img = np.load(os.path.join(args.data_dir1, 'test_data_img.npy'), allow_pickle=True)

    train_img_fa = np.load(os.path.join(args.data_dir2, 'train_data_img_fa.npy'), allow_pickle=True)
    valid_img_fa = np.load(os.path.join(args.data_dir2, 'valid_data_img_fa.npy'), allow_pickle=True)
    test_img_fa = np.load(os.path.join(args.data_dir2, 'test_data_img_fa.npy'), allow_pickle=True)


    train_img_md = np.load(os.path.join(args.data_dir2, 'train_data_img_md.npy'), allow_pickle=True)
    valid_img_md = np.load(os.path.join(args.data_dir2, 'valid_data_img_md.npy'), allow_pickle=True)
    test_img_md = np.load(os.path.join(args.data_dir2, 'test_data_img_md.npy'), allow_pickle=True)

    train_target = np.load(os.path.join(args.data_dir1, 'train_data_target.npy'), allow_pickle=True)
    valid_target = np.load(os.path.join(args.data_dir1, 'valid_data_target.npy'), allow_pickle=True)
    test_target = np.load(os.path.join(args.data_dir1, 'test_data_target.npy'), allow_pickle=True)

    train_dataset = ThreeInputMRIDataset(train_img, train_img_fa, train_img_md, train_target, args.resize, args.normalize, args.log)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.train_batch_size)
    valid_dataset = ThreeInputMRIDataset(valid_img, valid_img_fa, valid_img_md, valid_target, args.resize, args.normalize, args.log)
    valid_loader = torch.utils.data.DataLoader(valid_dataset, batch_size=args.valid_batch_size)
    test_dataset = ThreeInputMRIDataset(test_img, test_img_fa, test_img_md, test_target, args.resize, args.normalize, args.log)
    test_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.train_batch_size)

    if args.optimizer == 'sgd':
        optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)
    elif args.optimizer == 'adam':
        optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=0.001)

    if args.checkpoint_state:
        saved_opt_state = torch.load(args.checkpoint_opt, map_location='cpu')
        optimizer.load_state_dict(saved_opt_state)
        print('Loaded optimizer from saved state')
    
    loss = nn.L1Loss()

    if not args.checkpoint_state:
        train_multi_input(model, args.epoch, train_loader, valid_loader, test_loader, optimizer, loss, args.output_dir)
    else:
        train_multi_input(model, args.epoch, train_loader, valid_loader, test_loader, optimizer, loss, args.output_dir, checkpoint_epoch=args.checkpoint_epoch)
