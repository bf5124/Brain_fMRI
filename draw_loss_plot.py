import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
import bottleneck as bn


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Draw train loss plot')
    parser.add_argument('--data_dir', help='Directory path for train loss data')
    parser.add_argument('--lr', help='LR of the model')
    parser.add_argument('--move_mean', type=int, default=0, help='Whether to compute moving mean or not')
    args = parser.parse_args()

    train_loss = np.load(os.path.join(args.data_dir, 'loss_history_train.npy'), allow_pickle=True)
    
    if args.move_mean:
        train_loss = bn.move_mean(train_loss, window=5, min_count=1)

    plt.scatter(range(len(train_loss)), train_loss, color='black', s=1)
    plt.xlabel('Iterations')
    plt.ylabel('Training loss')
    plt.title('Loss LR: {}'.format(args.lr))

    plt.savefig(os.path.join(args.data_dir, 'train_loss_lr{}.png'.format(args.lr)))
