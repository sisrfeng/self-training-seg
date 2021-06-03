from dataset.cityscapes import Cityscapes
from dataset.pascal import PASCAL
from model.semseg.deeplabv2 import DeepLabV2
from model.semseg.deeplabv3plus import DeepLabV3Plus
from model.semseg.pspnet import PSPNet
from util.utils import count_params, meanIOU

import argparse
import os
import torch
from torch.nn import CrossEntropyLoss, DataParallel
from torch.optim import SGD
from torch.utils.data import DataLoader
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description='Semi-supervised Semantic Segmentation -- Training')

    # basic settings
    parser.add_argument('--data-root',
                        type=str,
                        default='/data/lihe/datasets/PASCAL-VOC-2012',
                        help='root path of training dataset')
    parser.add_argument('--dataset',
                        type=str,
                        default='pascal',
                        choices=['pascal', 'cityscapes', 'coco'],
                        help='training dataset')
    parser.add_argument('--batch-size',
                        type=int,
                        default=16,
                        help='batch size of training')
    parser.add_argument('--lr',
                        type=float,
                        default=None,
                        help='learning rate')
    parser.add_argument('--epochs',
                        type=int,
                        default=None,
                        help='training epochs')
    parser.add_argument('--crop-size',
                        type=int,
                        default=None,
                        help='cropping size of training samples')
    parser.add_argument('--backbone',
                        type=str,
                        choices=['resnet50', 'resnet101'],
                        default='resnet50',
                        help='backbone of semantic segmentation model')
    parser.add_argument('--model',
                        type=str,
                        choices=['deeplabv3plus', 'pspnet', 'deeplabv2'],
                        default='deeplabv3plus',
                        help='model for semantic segmentation')

    # semi-supervised settings
    parser.add_argument('--mode',
                        type=str,
                        default='train',
                        choices=['train', 'semi_train'],
                        help='choose supervised/semi-supervised setting')
    parser.add_argument('--labeled-id-path',
                        type=str,
                        default=None,
                        required=True,
                        help='path of labeled image ids')
    parser.add_argument('--unlabeled-id-path',
                        type=str,
                        default=None,
                        help='path of unlabeled image ids')
    parser.add_argument('--pseudo-mask-path',
                        type=str,
                        default=None,
                        help='path of generated pseudo masks')
    parser.add_argument('--save-path',
                        type=str,
                        default=None,
                        required=True,
                        help='path of saved checkpoints')

    args = parser.parse_args()
    return args


def main(args):
    if not os.path.exists(args.save_path):
        os.makedirs(args.save_path)
    if not os.path.exists(os.path.join(args.save_path, 'checkpoints')):
        os.mkdir(os.path.join(args.save_path, 'checkpoints'))

    if args.mode == 'semi_train':
        assert os.path.exists(args.pseudo_mask_path), \
            'the path of pseudo masks does not exist'
        assert args.unlabeled_id_path is not None, \
            'the path of unlabeled images ids must be specified in semi_train mode'

    dataset_zoo = {'pascal': PASCAL, 'cityscapes': Cityscapes, 'coco': COCO}
    trainset = dataset_zoo[args.dataset](args.data_root, args.mode, args.crop_size, args.labeled_id_path,
                                         args.unlabeled_id_path, args.pseudo_mask_path)
    valset = dataset_zoo[args.dataset](args.data_root, 'val', None)

    # in extremely scarce-data regime, oversample the labeled images
    if args.mode == 'train' and len(trainset.ids) < 200:
        trainset.ids *= 2

    trainloader = DataLoader(trainset, batch_size=args.batch_size, shuffle=True,
                             pin_memory=False, num_workers=16, drop_last=True)
    valloader = DataLoader(valset, batch_size=args.batch_size if args.dataset == 'cityscapes' else 1,
                           shuffle=False, pin_memory=False, num_workers=4, drop_last=False)

    model_zoo = {'deeplabv3plus': DeepLabV3Plus, 'pspnet': PSPNet, 'deeplabv2': DeepLabV2}
    model = model_zoo[args.model](args.backbone, len(trainset.CLASSES))
    print('\nParams: %.1fM' % count_params(model))

    head_lr_multiple = 10.0
    if args.model == 'deeplabv2':
        assert args.backbone == 'resnet101'
        model.load_state_dict(torch.load('/data/lihe/models/deeplabv2_resnet101_coco_pretrained.pth'))
        head_lr_multiple = 1.0

    criterion = CrossEntropyLoss(ignore_index=255)
    optimizer = SGD([{'params': model.backbone.parameters(), 'lr': args.lr},
                     {'params': [param for name, param in model.named_parameters()
                                 if 'backbone' not in name],
                      'lr': args.lr * head_lr_multiple}],
                    lr=args.lr, momentum=0.9, weight_decay=1e-4)

    model = DataParallel(model).cuda()

    iters = 0
    total_iters = len(trainloader) * args.epochs

    previous_best = 0.0

    for epoch in range(args.epochs):
        print("\n==> Epoch %i, learning rate = %.4f\t\t\t\t\t previous best = %.2f" %
              (epoch, optimizer.param_groups[0]["lr"], previous_best))

        model.train()
        total_loss = 0.0
        tbar = tqdm(trainloader)

        for i, (img, mask) in enumerate(tbar):
            img, mask = img.cuda(), mask.cuda()

            pred = model(img)
            loss = criterion(pred, mask)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            iters += 1
            lr = args.lr * (1 - iters / total_iters) ** 0.9
            optimizer.param_groups[0]["lr"] = lr
            optimizer.param_groups[1]["lr"] = lr * head_lr_multiple

            tbar.set_description('Loss: %.3f' % (total_loss / (i + 1)))

        metric = meanIOU(num_classes=len(valloader.dataset.CLASSES))

        model.eval()
        tbar = tqdm(valloader)

        with torch.no_grad():
            for img, mask, _ in tbar:
                img = img.cuda()
                pred = model(img)
                pred = torch.argmax(pred, dim=1)

                metric.add_batch(pred.cpu().numpy(), mask.numpy())
                mIOU = metric.evaluate()[-1]

                tbar.set_description('mIOU: %.2f' % (mIOU * 100.0))

        mIOU *= 100.0
        if mIOU > previous_best:
            if previous_best != 0:
                os.remove(os.path.join(args.save_path, '%s_%s_%.2f.pth' % (args.model, args.backbone, previous_best)))
            previous_best = mIOU
            torch.save(model.module.state_dict(),
                       os.path.join(args.save_path, '%s_%s_%.2f.pth' % (args.model, args.backbone, mIOU)))

        if args.mode == 'train' and epoch % 10 == 9:
            torch.save(model.module.state_dict(),
                       os.path.join(args.save_path,
                                    'checkpoints/%s_%s_epoch_%i_%.2f.pth' % (args.model, args.backbone, epoch, mIOU)))


if __name__ == '__main__':
    args = parse_args()

    if args.epochs is None:
        args.epochs = {'pascal': 80, 'cityscapes': 240, 'coco': 30}[args.dataset]
    if args.lr is None:
        args.lr = {'pascal': 0.001, 'cityscapes': 0.004, 'coco': 0.004}[args.dataset] / 16 * args.batch_size
    if args.crop_size is None:
        args.crop_size = {'pascal': 321, 'cityscapes': 721, 'coco': 321}[args.dataset]

    print(args)

    main(args)
