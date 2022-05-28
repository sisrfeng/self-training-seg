export Semi_cfg='pascal/1_8/split_0'

CUDA_VISIBLE_DEVICES=6,7 python -W ignore main.py                    \
    --dataset             pascal                                     \
    --data-root           /data2/wf2/self-training-seg/dataset/voc   \
    --batch-size          16                                         \
    --backbone            resnet50                                   \
    --model               deeplabv3plus                              \
    --labeled-id-path     dataset/splits/$Semi_cfg/labeled.txt   \
    --unlabeled-id-path   dataset/splits/$Semi_cfg/unlabeled.txt \
    --pseudo-mask-path    outdir/pseudo_masks/$Semi_cfg          \
    --save-path           outdir/models/$Semi_cfg

# ST++:
    # --plus --reliable-id-path outdir/reliable_ids/$Semi_cfg

