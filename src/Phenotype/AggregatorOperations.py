import torch.nn.functional as F
import torch
from src.Utilities import Utils
import math

from src.Config import Config


def merge_linear_and_conv(linear, conv, lossy=True):
    """takes in a single linear shaped tensor and a single conv2d shaped tensor and merges them"""
    if list(conv.size())[2] != list(conv.size())[3]:
        print("conv has non square dimensions:", conv.size())
    # print("merging linear",linear.size(), "and conv",conv.size())
    if (lossy):
        """reduce conv features until it can be reshaped to match dimensionality of linear - then sum"""
        conv_features = Utils.get_flat_number(conv)
        conv_channels = list(conv.size())[1]
        linear_features = list(linear.size())[1]
        if conv_channels > linear_features:
            """pad linear"""
            # print("conv has more channels(",conv_channels,")","than linear has features(",linear_features,") - must pad linear")
            left_pad = round((conv_channels - linear_features) / 2)
            right_pad = (conv_channels - linear_features) - left_pad
            linear = F.pad(input=linear, pad=(left_pad, right_pad))
            linear_features = list(linear.size())[1]

        # print("merging conv",conv.size(),"and linear",linear.size())
        if (conv_features > linear_features):
            "reduce conv"
            reduction_factor = math.ceil(
                math.pow(conv_features / linear_features, 0.5))  # square root because max pool reduces on two dims x*y
            conv = F.max_pool2d(conv, kernel_size=(reduction_factor, reduction_factor))
            conv_features = Utils.get_flat_number(conv)

            if (conv_features > linear_features):
                raise Exception("error: reduced conv (factor=", reduction_factor,
                                ") in lossy merge with linear. but conv still has more features.\n"
                                "conv:", conv.size(), conv_features, "linear:", linear.size(), linear_features)
        batch_size = list(conv.size())[0]
        conv = conv.view(batch_size, -1)
        conv_features = list(conv.size())[1]
        feature_diff = linear_features - conv_features

        conv = F.pad(input=conv, pad=(feature_diff // 2, feature_diff - feature_diff // 2))
        # print("summing",conv.size(), "and",linear.size(),"to",torch.sum(torch.stack([conv, linear],dim=0), dim = 0))
        try:
            return torch.sum(torch.stack([conv, linear], dim=0), dim=0)
        except:
            raise Exception(
                "failed to merge conv(" + repr(conv.size()) + ") and linear(" + repr(linear.size()) + ") inputs:")

    else:
        # use an additional linear layer to map the conv features to a linear the same shape as the given linear
        raise NotImplementedError("not yet implemented lossless merge of conv and linear")


def merge_linear_outputs(previous_inputs, new_input, cat=False):
    # print("merging linear layers with different feature counts")
    if (cat):
        previous = torch.sum(torch.stack(previous_inputs), dim=0)
        return [torch.cat([previous, new_input], dim=0)]
    else:
        # print("padding linear outputs to merge")
        new_input, previous_inputs = pad_linear_outputs(previous_inputs, new_input)
        previous_inputs.append(new_input)

        if Config.test_in_run:
            features = previous_inputs[0].size()
            for inp in previous_inputs:
                new_num_features = inp.size()
                if new_num_features != features:
                    raise Exception("merge linear failed to homogenise list:" + repr([x.size() for x in previous_inputs]))
        return previous_inputs


def pad_linear_outputs(previous_inputs, new_input):
    size_diff = list(previous_inputs[0].size())[1] - list(new_input.size())[1]
    left_pad = round(abs(size_diff) / 2)
    right_pad = abs(size_diff) - left_pad
    if (size_diff > 0):
        # previous is larger
        new_input = F.pad(input=new_input, pad=(left_pad, right_pad))
    else:
        # new is larger
        for i in range(len(previous_inputs)):
            previous_inputs[i] = F.pad(input=previous_inputs[i], pad=(left_pad, right_pad))

    size_diff = list(previous_inputs[0].size())[1] - list(new_input.size())[1]
    if size_diff != 0:
        raise Exception("padding linear outputs failed. new size:", list(new_input.size())[1], "hom size:",
                        list(previous_inputs[0].size())[1])

    return new_input, previous_inputs


def merge_conv_outputs(previous_inputs, new_input):
    # print("merging conv tensors",len(previous_inputs), previous_inputs[0].size(),new_input.size())
    # conv layers here do not have
    channels1, x1, y1 = list(previous_inputs[0].size())[1], list(previous_inputs[0].size())[2], \
                        list(previous_inputs[0].size())[3]
    channels2, x2, y2 = list(new_input.size())[1], list(new_input.size())[2], list(new_input.size())[3]

    size_ratio = (x1 + y1) / (x2 + y2)
    if size_ratio < 1:
        size_ratio = 1 / size_ratio

    if round(size_ratio) > 1.45:  # a ratio less than 1.45 will be made worse by maxPooling, requiring even more padding
        # tensors are significantly different - should use a maxPool here to shrink the larger of the two
        # print("using max pooling for prev:", x1,y1,"new:",x2,y2)
        new_input, previous_inputs = max_pool_conv_input(x1, x2, y1, y2, new_input, previous_inputs)
        x1, y1, x2, y2 = previous_inputs[0].size()[2], previous_inputs[0].size()[3], new_input.size()[2], \
                         new_input.size()[3]
        if x1 != x2 or y1 != y2:
            # print("using padding for prev:", x1,y1,"new:",x2,y2)
            # larger convs have been pooled. however a small misalignment remains
            new_input, previous_inputs = pad_conv_input(x1, x2, y1, y2, new_input, previous_inputs)
        x1, y1, x2, y2 = new_input.size()[2], new_input.size()[3], previous_inputs[0].size()[2], \
                         previous_inputs[0].size()[3]
        # print("\treturning prev:", x1, y1, "new:", x2, y2)

    else:
        # tensors are similar size - can be padded
        # print("using padding, prev:", x1,y1,"new:",x2,y2)
        new_input, previous_inputs = pad_conv_input(x1, x2, y1, y2, new_input, previous_inputs)
        # print("\treturning prev:",previous_inputs[0].size(),"new:",new_input.size())

    previous_channels, new_channels = previous_inputs[-1].size()[1], new_input.size()[1]
    if not (previous_channels == new_channels):
        # print("differing channel counts", previous_channels, new_channels)
        previous_inputs = [
            merge_differing_channel_convs(new_input, torch.sum(torch.stack(previous_inputs, dim=0), dim=0))]
    else:
        previous_inputs.append(new_input)

        if Config.test_in_run:
            features = previous_inputs[0].size()
            for inp in previous_inputs:
                new_num_features = inp.size()
                if new_num_features != features:
                    raise Exception("merge conv failed to homogenise list:" + repr([x.size() for x in previous_inputs]))

    return previous_inputs


def merge_differing_channel_convs(conv_a, conv_b):
    return torch.cat([conv_a, conv_b], dim=1)


def max_pool_conv_input(x1, x2, y1, y2, new_input, previous_inputs):
    """takes a new input, and a list of homogenous previousInputs"""
    size_ratio = (x1 + y1) / (x2 + y2)
    if size_ratio < 1:
        size_ratio = 1 / size_ratio

    if (x1 + y1) > (x2 + y2):
        # previous inputs must be pooled
        # print("pooling prev")
        for i in range(len(previous_inputs)):
            previous_inputs[i] = F.max_pool2d(previous_inputs[i], kernel_size=(round(size_ratio), round(size_ratio)))

    else:
        # print("pooling new")
        new_input = F.max_pool2d(new_input, kernel_size=(round(size_ratio), round(size_ratio)))

    return new_input, previous_inputs


def pad_conv_input(x1, x2, y1, y2, new_input, previous_inputs):
    if x1 < x2:
        # previous inputs are smalller on the x axis
        left_pad = (x2 - x1) // 2
        right_pad = (x2 - x1) - left_pad
        for i in range(len(previous_inputs)):
            previous_inputs[i] = F.pad(input=previous_inputs[i], pad=(0, 0, left_pad, right_pad), mode='constant',
                                       value=0)

    elif x2 < x1:
        # new found input is smaller on x than previous
        left_pad = (x1 - x2) // 2
        right_pad = (x1 - x2) - left_pad

        new_input = F.pad(input=new_input, pad=(0, 0, left_pad, right_pad), mode='constant', value=0)

    if y1 < y2:
        # previous inputs are smalller on the x axis
        left_pad = (y2 - y1) // 2
        right_pad = (y2 - y1) - left_pad
        for i in range(len(previous_inputs)):
            previous_inputs[i] = F.pad(input=previous_inputs[i], pad=(left_pad, right_pad),
                                       mode='constant', value=0)

    elif y2 < y1:
        # new found input is smaller on x than previous
        left_pad = (y1 - y2) // 2
        right_pad = (y1 - y2) - left_pad

        new_input = F.pad(input=new_input, pad=(left_pad, right_pad), mode='constant', value=0)

    return new_input, previous_inputs