from __future__ import annotations

import random

import torch
from typing import TYPE_CHECKING

from torch.utils.data import DataLoader
from torchvision.transforms import transforms

from src2.Configuration import config
from src2.Phenotype.NeuralNetwork.Evaluator.DataLoader import load_data

from sklearn.metrics import accuracy_score
import numpy as np

if TYPE_CHECKING:
    from src2.Phenotype.NeuralNetwork.NeuralNetwork import Network


def evaluate(model: Network, num_epochs=config.epochs_in_evolution):
    """trains model on training data, test on testing and returns test acc"""
    if config.dummy_run:
        return random.random()

    # TODO add in augmentations
    composed_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    train_loader = load_data(composed_transform, 'train')
    for epoch in range(num_epochs):
        train_epoch(model, train_loader)

    return get_test_acc(model, load_data(composed_transform, 'test'))


def train_epoch(model: Network, train_loader: DataLoader, max_batches=20):
    model.train()
    loss = 0
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        if max_batches != -1 and batch_idx > max_batches:
            break
        model.optimizer.zero_grad()
        loss += train_batch(model, inputs, targets)


def train_batch(model: Network, inputs: torch.tensor, labels: torch.tensor):
    device = config.get_device()
    inputs, labels = inputs.to(device), labels.to(device)

    output = model(inputs)
    m_loss = model.loss_fn(output, labels)
    m_loss.backward()
    model.optimizer.step()

    return m_loss.item()


def get_test_acc(model: Network, test_loader: DataLoader):
    model.eval()
    # print("testing")

    count = 0
    total_acc = 0

    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(test_loader):
            inputs, targets = inputs.to(config.get_device()), targets.to(config.get_device())

            output = model(inputs)

            softmax = torch.exp(output).cpu()
            prob = list(softmax.numpy())
            predictions = np.argmax(prob, axis=1)

            acc = accuracy_score(targets.cpu(), predictions)
            total_acc += acc
            count = batch_idx

    return total_acc / count
