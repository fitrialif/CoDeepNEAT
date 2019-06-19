import torch.nn as nn
import torch.optim as optim


class Net(nn.Module):
    def __init__(self, layers, lr=0.001, beta1=0.9, beta2=0.999, loss_fn=nn.MSELoss()):
        super(Net, self).__init__()
        self.model = nn.Sequential(*layers)
        self.loss_fn = loss_fn
        self.lr = lr
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.lr, betas=(beta1, beta2))

        # print('Created network with architecture:', self.model, sep='\n')

    def forward(self, input):
        return self.model(input)


class BlueprintNet(nn.Module):
    def __init__(self, model, lr=0.01, beta1=0.9, beta2=0.999, loss_fn=nn.NLLLoss()):
        super(BlueprintNet, self).__init__()
        self.model = model
        self.loss_fn = loss_fn
        self.lr = lr
        self.optimizer = optim.SGD(self.model.parameters(), lr=self.lr, momentum=0.5)

        # print('Created network with architecture:', self.model, sep='\n')

    def forward(self, input):
        return self.model(input)
