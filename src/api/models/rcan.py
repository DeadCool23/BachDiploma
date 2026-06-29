from models import common
import torch.nn as nn
from typing import List, Union, Tuple
from dataclasses import dataclass

@dataclass
class RCANConfig:
    n_resgroups: int = 10
    n_resblocks: int = 20
    n_feats: int = 64
    reduction: int = 16
    scale: Union[int, List[int]] = 2
    res_scale: float = 1.0
    
    n_colors: int = 3
    rgb_range: int = 255
    rgb_mean: Tuple[float, ...] = (0.4488, 0.4371, 0.4040)
    rgb_std: Tuple[float, ...] = (1.0, 1.0, 1.0)
    
    kernel_size: int = 3
    use_batch_norm: bool = False
    
    def __post_init__(self):
        if isinstance(self.scale, int):
            self.scale = [self.scale]


class CALayer(nn.Module):
    def __init__(self, channel: int, reduction: int = 16):
        super(CALayer, self).__init__()
        reduced_channels = max(channel // reduction, 1)
        
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv_du = nn.Sequential(
            nn.Conv2d(channel, reduced_channels, 1, padding=0, bias=True),
            nn.ReLU(inplace=True),
            nn.Conv2d(reduced_channels, channel, 1, padding=0, bias=True),
            nn.Sigmoid()
        )

    def forward(self, x):
        y = self.avg_pool(x)
        y = self.conv_du(y)
        return x * y


class RCAB(nn.Module):
    def __init__(
        self,
        conv,
        n_feat: int,
        kernel_size: int,
        reduction: int,
        bias: bool = True,
        bn: bool = False,
        act=nn.ReLU(True),
        res_scale: float = 1.0
    ):
        super(RCAB, self).__init__()
        self.res_scale = res_scale
        
        modules_body = []
        for i in range(2):
            modules_body.append(conv(n_feat, n_feat, kernel_size, bias=bias))
            if bn:
                modules_body.append(nn.BatchNorm2d(n_feat))
            if i == 0:
                modules_body.append(act)
        modules_body.append(CALayer(n_feat, reduction))
        
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        res = self.body(x)
        if self.res_scale != 1.0:
            res = res.mul(self.res_scale)
        return res + x


class ResidualGroup(nn.Module):
    def __init__(
        self,
        conv,
        n_feat: int,
        kernel_size: int,
        reduction: int,
        act,
        res_scale: float,
        n_resblocks: int
    ):
        super(ResidualGroup, self).__init__()
        
        modules_body = [
            RCAB(
                conv, n_feat, kernel_size, reduction,
                bias=True, bn=False, act=nn.ReLU(True), res_scale=res_scale
            )
            for _ in range(n_resblocks)
        ]
        modules_body.append(conv(n_feat, n_feat, kernel_size))
        
        self.body = nn.Sequential(*modules_body)

    def forward(self, x):
        res = self.body(x)
        return res + x


class RCAN(nn.Module):
    def __init__(self, args, conv=common.default_conv):
        super(RCAN, self).__init__()
        
        if isinstance(args, RCANConfig):
            self.config = args
        else:
            self.config = RCANConfig(
                n_resgroups=getattr(args, 'n_resgroups', 10),
                n_resblocks=getattr(args, 'n_resblocks', 20),
                n_feats=getattr(args, 'n_feats', 64),
                reduction=getattr(args, 'reduction', 16),
                scale=getattr(args, 'scale', 2),
                res_scale=getattr(args, 'res_scale', 1.0),
                n_colors=getattr(args, 'n_colors', 3),
                rgb_range=getattr(args, 'rgb_range', 255),
                kernel_size=getattr(args, 'kernel_size', 3)
            )
        
        rgb_mean = self.config.rgb_mean
        rgb_std = self.config.rgb_std
        
        self.sub_mean = common.MeanShift(self.config.rgb_range, rgb_mean, rgb_std)
        
        modules_head = [conv(self.config.n_colors, self.config.n_feats, self.config.kernel_size)]
        self.head = nn.Sequential(*modules_head)

        modules_body = [
            ResidualGroup(
                conv,
                self.config.n_feats,
                self.config.kernel_size,
                self.config.reduction,
                act=nn.ReLU(True),
                res_scale=self.config.res_scale,
                n_resblocks=self.config.n_resblocks
            )
            for _ in range(self.config.n_resgroups)
        ]
        modules_body.append(conv(self.config.n_feats, self.config.n_feats, self.config.kernel_size))
        self.body = nn.Sequential(*modules_body)

        scale = self.config.scale[0] if self.config.scale else 1
        modules_tail = [
            common.Upsampler(conv, scale, self.config.n_feats, act=False),
            conv(self.config.n_feats, self.config.n_colors, self.config.kernel_size)
        ]
        self.tail = nn.Sequential(*modules_tail)
        
        self.add_mean = common.MeanShift(self.config.rgb_range, rgb_mean, rgb_std, 1)

    def forward(self, x):
        x = self.sub_mean(x)
        x = self.head(x)

        res = self.body(x)
        res += x

        x = self.tail(res)
        x = self.add_mean(x)

        return x

    def load_state_dict(self, state_dict, strict=False):
        own_state = self.state_dict()
        for name, param in state_dict.items():
            if name in own_state:
                if isinstance(param, nn.Parameter):
                    param = param.data
                try:
                    own_state[name].copy_(param)
                except Exception:
                    if name.find('tail') >= 0:
                        print('Replace pre-trained upsampler to new one...')
                    else:
                        raise RuntimeError('While copying the parameter named {}, '
                                           'whose dimensions in the model are {} and '
                                           'whose dimensions in the checkpoint are {}.'
                                           .format(name, own_state[name].size(), param.size()))
            elif strict:
                if name.find('tail') == -1:
                    raise KeyError('unexpected key "{}" in state_dict'
                                   .format(name))

        if strict:
            missing = set(own_state.keys()) - set(state_dict.keys())
            if len(missing) > 0:
                raise KeyError('missing keys in state_dict: "{}"'.format(missing))
    
    def count_parameters(self):
        total_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        non_trainable_params = sum(p.numel() for p in self.parameters() if not p.requires_grad)
        
        print(f"Total parameters: {total_params:,}")
        print(f"Trainable parameters: {trainable_params:,}")
        print(f"Non-trainable parameters: {non_trainable_params:,}")
        return total_params