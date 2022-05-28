# ST++


## Getting Started

### Data Preparation

#### Pre-trained Model

[ResNet-50](https://download.pytorch.org/models/resnet50-0676ba61.pth) | [ResNet-101](https://download.pytorch.org/models/resnet101-63fe2227.pth) | [DeepLabv2-ResNet-101](https://drive.google.com/file/d/14be0R1544P5hBmpmtr8q5KeRAvGunc6i/view?usp=sharing)

#### Dataset

[Pascal JPEGImages](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCtrainval_11-May-2012.tar) 
 [Pascal SegmentationClass](https://drive.google.com/file/d/1ikrDlsai5QSf2GiSUR3f8PZUzyTubcuF/view?usp=sharing) 
 [Cityscapes leftImg8bit](https://www.cityscapes-dataset.com/file-handling/?packageID=3) 
 [Cityscapes gtFine](https://drive.google.com/file/d/1E_27g9tuHm6baBqcA7jct_jqcGA89QPm/view?usp=sharing) 

#### File Organization

```
├── ./pretrained
    ├── resnet50.pth
    ├── resnet101.pth
    └── deeplabv2_resnet101_coco_pretrained.pth

├── [Your Pascal Path]
    ├── JPEGImages
    └── SegmentationClass

├── [Your Cityscapes Path]
    ├── leftImg8bit
    └── gtFine
```


### Training and Testing

```
```
This script is for our ST framework.


## Acknowledgement

The DeepLabv2 MS COCO pre-trained model is borrowed and converted from **AdvSemiSeg**.
The image partitions are borrowed from **Context-Aware-Consistency** and **PseudoSeg**. 
Part of the training hyper-parameters and network structures are adapted from **PyTorch-Encoding**.
The strong data augmentations are borrowed from **MoCo v2** and **PseudoSeg**.
 
+ AdvSemiSeg: [https://github.com/hfslyc/AdvSemiSeg](https://github.com/hfslyc/AdvSemiSeg).
+ Context-Aware-Consistency: [https://github.com/dvlab-research/Context-Aware-Consistency](https://github.com/dvlab-research/Context-Aware-Consistency).
+ PseudoSeg: [https://github.com/googleinterns/wss](https://github.com/googleinterns/wss).
+ PyTorch-Encoding: [https://github.com/zhanghang1989/PyTorch-Encoding](https://github.com/zhanghang1989/PyTorch-Encoding).
+ MoCo: [https://github.com/facebookresearch/moco](https://github.com/facebookresearch/moco).
+ OpenSelfSup: [https://github.com/open-mmlab/OpenSelfSup](https://github.com/open-mmlab/OpenSelfSup).

