import torch
import torch.nn as nn


def conv_block(in_ch, out_ch):
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class IBN(nn.Module):
    def __init__(self, channels):
        super().__init__()
        half = channels // 2
        self.half = half
        self.inorm = nn.InstanceNorm2d(half, affine=True)
        self.bnorm = nn.BatchNorm2d(channels - half)

    def forward(self, x):
        x1, x2 = torch.split(x, [self.half, x.size(1) - self.half], dim=1)
        x1 = self.inorm(x1)
        x2 = self.bnorm(x2)
        return torch.cat([x1, x2], dim=1)


def ibn_conv_block(in_ch, out_ch):
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1),
        IBN(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class UNet(nn.Module):
    def __init__(self, in_ch=3, num_classes=3, base_ch=32, return_features=False, use_ibn=False):
        super().__init__()
        self.return_features = return_features
        block1 = ibn_conv_block if use_ibn else conv_block
        block2 = ibn_conv_block if use_ibn else conv_block

        self.enc1 = block1(in_ch, base_ch)
        self.enc2 = block2(base_ch, base_ch * 2)
        self.enc3 = conv_block(base_ch * 2, base_ch * 4)
        self.enc4 = conv_block(base_ch * 4, base_ch * 8)
        self.pool = nn.MaxPool2d(2)

        self.bottleneck = conv_block(base_ch * 8, base_ch * 16)

        self.up4 = nn.ConvTranspose2d(base_ch * 16, base_ch * 8, 2, stride=2)
        self.dec4 = conv_block(base_ch * 16, base_ch * 8)
        self.up3 = nn.ConvTranspose2d(base_ch * 8, base_ch * 4, 2, stride=2)
        self.dec3 = conv_block(base_ch * 8, base_ch * 4)
        self.up2 = nn.ConvTranspose2d(base_ch * 4, base_ch * 2, 2, stride=2)
        self.dec2 = conv_block(base_ch * 4, base_ch * 2)
        self.up1 = nn.ConvTranspose2d(base_ch * 2, base_ch, 2, stride=2)
        self.dec1 = conv_block(base_ch * 2, base_ch)

        self.out_conv = nn.Conv2d(base_ch, num_classes, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))
        b = self.bottleneck(self.pool(e4))

        d4 = self.up4(b)
        d4 = self.dec4(torch.cat([d4, e4], dim=1))
        d3 = self.up3(d4)
        d3 = self.dec3(torch.cat([d3, e3], dim=1))
        d2 = self.up2(d3)
        d2 = self.dec2(torch.cat([d2, e2], dim=1))
        d1 = self.up1(d2)
        d1 = self.dec1(torch.cat([d1, e1], dim=1))

        out = self.out_conv(d1)

        if self.return_features:
            return out, b
        return out


if __name__ == "__main__":
    m = UNet(base_ch=32, num_classes=3)
    x = torch.randn(2, 3, 256, 256)
    y = m(x)
    print("baseline U-Net:", x.shape, "-> output:", y.shape)
    assert y.shape == (2, 3, 256, 256)

    m_ibn = UNet(base_ch=32, num_classes=3, use_ibn=True)
    y_ibn = m_ibn(x)
    print("IBN U-Net:     ", x.shape, "-> output:", y_ibn.shape)
    assert y_ibn.shape == (2, 3, 256, 256)
    print("OK")
