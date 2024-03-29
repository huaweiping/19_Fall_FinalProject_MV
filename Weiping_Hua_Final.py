# -*- coding: utf-8 -*-
"""Untitled

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZcfVAN4_NNW1OwrFQOEMpB6wWVG9dV5S
"""

# =============================================================================
# ==============================Question 2====================================
# =============================================================================
import os, cv2, re, random
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import torch.nn as nn
import torch.optim as optim
import sklearn.metrics as metric

# !pip install -U -q kaggle
# from google.colab import files
# !cp kaggle.json ~/.kaggle/
# !kaggle datasets download -d chetankv/dogs-cats-images
# !unrar x "Linnaeus 5 128X128.rar"

preproccessing_train = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.Resize(size=(224,224)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

preproccessing_test = transforms.Compose([
    transforms.Resize(size=(224,224)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

data_dir = './Linnaeus 5 128X128'

trainset =  torchvision.datasets.ImageFolder(data_dir + '/train', transform = preproccessing_train)
testset =  torchvision.datasets.ImageFolder(data_dir + '/test', transform = preproccessing_test)

trainloader = torch.utils.data.DataLoader(trainset, shuffle=True, batch_size=16, num_workers=16)
testloader = torch.utils.data.DataLoader(testset, shuffle=True, batch_size=64, num_workers=64)

# =======================================================================
# =========================Here is the program========================
# =======================================================================



device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Assuming that we are on a CUDA machine, this should print a CUDA device:

print(device)

net_vgg16 = torchvision.models.vgg16(pretrained=True)
print(net_vgg16)
# If want to use batch normalization
# net_vgg16 = torchvision.models.vgg16_bn(pretrained=True)
print(net_vgg16)
classes = ['berry', 'bird', 'dog', 'flower', 'other']

net_vgg16.to(device)


for param in net_vgg16.parameters():
  param.requires_grad = False

# If don't want to use dropout. set the value to 0
net_vgg16.classifier[2] = nn.modules.Dropout(0,False)
net_vgg16.classifier[5] = nn.modules.Dropout(0,False)
net_vgg16.classifier[6] = nn.Linear(4096,5)

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net_vgg16.parameters(), lr=1e-5,momentum=0.9)

net_vgg16.to(device)
net_vgg16.train()
print('start')
# train_loss, train_acc = train(net_vgg16, device, train_iterator, optimizer, criterion)
# print(train_loss)
# print(train_acc)
for epoch in range(10):  # loop over the dataset multiple times
    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        # get the inputs; data is a list of [inputs, labels]
        inputs, labels = data[0].to(device), data[1].to(device)
        # inputs = inputs.to(device)
        # labels = labels.to(device)
        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net_vgg16(inputs)        
        _, test = torch.max(outputs, 1)

        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if i % 30 == 29:    # print every 2000 mini-batches
          print('[%d, %5d] loss: %.3f' %
                (epoch + 1, i + 1, running_loss / 2000))
          running_loss = 0.0
PATH = './net_vgg16.pth'
torch.save(net_vgg16.state_dict(), PATH)

net_vgg16.load_state_dict(torch.load(PATH))
# net_vgg16.to(device)

list_ground_truth = []
list_prediction = []
classes = ['berry', 'bird', 'dog', 'flower', 'other']

net_vgg16.eval()


with torch.no_grad():
  for i, data in enumerate(testloader, 0):
    inputs, labels = data[0].to(device), data[1].to(device)
    # inputs = inputs.to(device)
    # labels = labels.to(device)
    outputs = net_vgg16(inputs)
    _, predicted = torch.max(outputs, 1)

    c = (predicted == labels).squeeze()    
    for i in range(len(labels)):
      list_ground_truth.append(classes[labels.cpu().numpy()[i]])
      list_prediction.append(classes[predicted.cpu().numpy()[i]])

test_classfication = metric.classification_report(list_ground_truth, list_prediction, target_names = classes, output_dict=False)
test_confusion = metric.confusion_matrix(list_ground_truth, list_prediction, labels = classes)
test_accuracy = metric.accuracy_score(list_ground_truth, list_prediction)

print(test_classfication)
print(test_confusion)
print(test_accuracy)

# =============================================================================
# ==============================Question 3====================================
# =============================================================================

import numpy as np
import cv2
from google.colab.patches import cv2_imshow
import glob
import matplotlib.pyplot as plt

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((19*13,3), np.float32)
objp[:,:2] = np.mgrid[0:19,0:13].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

images = glob.glob('*.bmp')

for Iname in images:
  image1 = cv2.cvtColor(cv2.imread(Iname), cv2.COLOR_BGR2GRAY)
  found, corners = cv2.findChessboardCorners(image1, (19,13))
  if found:
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    corners_sub = cv2.cornerSubPix(image1,corners,(11,11),(-1,-1),criteria)
  
    imgpoints.append(corners_sub)
    objpoints.append(objp)

cv2.drawChessboardCorners(image1, (19,13), corners, found)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, image1.shape[::-1],None,None)
Rotation = cv2.Rodrigues(rvecs[0])[0]
wtc = np.array(tvecs[0])
wTc = np.column_stack((Rotation, wtc))
Camera_matrix = np.dot(mtx,np.column_stack((Rotation.T, -np.dot(Rotation.T, wtc))))

# print(mtx)
print(Camera_matrix)
cv2_imshow(image1)


img_new = np.dot(Camera_matrix, np.array([0,0,0,1]).reshape(4,1))
print(img_new)

# =============================================================================
# ==============================Question 3====================================
# =============================================================================

import numpy as np
import scipy as sp
import math

def projection_matrix(camera_parameters, homography):
    """
    From the camera calibration matrix and the estimated homography
    compute the 3D projection matrix
    """
    # Compute rotation along the x and y axis as well as the translation
    homography = homography * (-1)
    rot_and_transl = np.dot(np.linalg.inv(camera_parameters), homography)
    col_1 = rot_and_transl[:, 0]
    col_2 = rot_and_transl[:, 1]
    col_3 = rot_and_transl[:, 2]
    # normalise vectors
    l = math.sqrt(np.linalg.norm(col_1, 2) * np.linalg.norm(col_2, 2))
    rot_1 = col_1 / l
    rot_2 = col_2 / l
    translation = col_3 / l
    # compute the orthonormal basis
    c = rot_1 + rot_2
    p = np.cross(rot_1, rot_2)
    d = np.cross(c, p)
    rot_1 = np.dot(c / np.linalg.norm(c, 2) + d / np.linalg.norm(d, 2), 1 / math.sqrt(2))
    rot_2 = np.dot(c / np.linalg.norm(c, 2) - d / np.linalg.norm(d, 2), 1 / math.sqrt(2))
    rot_3 = np.cross(rot_1, rot_2)
    # finally, compute the 3D projection matrix from the model to the current frame
    projection = np.stack((rot_1, rot_2, rot_3, translation)).T
    print(camera_parameters)
    return np.dot(camera_parameters, projection)



# Assume we use the object coordinates and image pixel coordinates in the first question
P_Object = np.array(objpoints)
[rows, cols] = P_Object[0].shape

P_Object = np.column_stack((P_Object[0],np.ones([rows,1])))

p_image = np.asarray(imgpoints[0])
p_image = np.squeeze(p_image)

i = rows - 1
A_camera_matrix = np.array([[P_Object[i, 0],P_Object[i, 1], 1, 0, 0, 0, 
              -np.dot(p_image[i,0], P_Object[i, 0]),-np.dot(p_image[i,0], 
              P_Object[i, 1]),-p_image[i,0]],
              [0, 0, 0,
              P_Object[i, 0],P_Object[i, 1], 1, 
              -np.dot(p_image[i,1], P_Object[i, 0]),-np.dot(p_image[i,1], P_Object[i, 1]),-p_image[i,1]]])

i = 1
while i < rows:
  A_camera_matrix = np.row_stack((A_camera_matrix,[[P_Object[i, 0],P_Object[i, 1], 1, 0, 0, 0, 
              -np.dot(p_image[i,0], P_Object[i, 0]),-np.dot(p_image[i,0], 
              P_Object[i, 1]),-p_image[i,0]],
              [0, 0, 0,
              P_Object[i, 0],P_Object[i, 1], 1, 
              -np.dot(p_image[i,1], P_Object[i, 0]),-np.dot(p_image[i,1], P_Object[i, 1]),-p_image[i,1]]]))
  i = i + 1

[u,s,vh] = np.linalg.svd(A_camera_matrix)
# print (vh.T)


homography_matrix = np.array(([vh.T[0, -1],vh.T[1, -1],vh.T[2, -1]],[vh.T[3, -1],vh.T[4, -1],vh.T[5, -1]],[vh.T[6, -1],vh.T[7, -1],vh.T[8, -1]]))

print ('homography_matrix_no_Z:\n',homography_matrix)


camera_parameters = mtx
camera_matrix = projection_matrix(camera_parameters, homography_matrix) 
print ('camera_matrix:\n',camera_matrix)

obj_cubepoints = np.array([[0,0,0,1], 
              [18,0,0,1],
              [18,12,0,1],
              [0,12,0,1],
              [0,0,5,1], 
              [18,0,5,1],
              [18,12,5,1],
              [0,12,5,1]])
print(obj_cubepoints)
img_cubepoints = np.dot(camera_matrix, obj_cubepoints[0].T)
print(img_cubepoints)

# =============================================================================
# ==============================Question 4====================================
# =============================================================================
import torch
import torch.nn as nn
import torch.nn.functional as F
import os, cv2, re, random
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import torch.nn as nn
import torch.optim as optim
import sklearn.metrics as metric

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class Net(nn.Module):

    def __init__(self,in_dim, hidden_dim, n_layer, n_class):
        super(Net, self).__init__()

        self.n_layer = n_layer
        self.hidden_dim = hidden_dim
        # an affine operation: y = Wx + b
        self.lstm = nn.LSTM(in_dim, hidden_dim, n_layer,
                            batch_first=True)
        self.classifier = nn.Linear(hidden_dim, n_class)

    def forward(self, x):
        result, _ = self.lstm(x)
        result = result[:, -1, :]
        result = self.classifier(result)
        return result

# Assuming that we are on a CUDA machine, this should print a CUDA device:

print(device)
train_dataset = torchvision.datasets.MNIST(
    root='./data', train=True, transform=transforms.ToTensor(), download=True)

test_dataset = torchvision.datasets.MNIST(
    root='./data', train=False, transform=transforms.ToTensor())

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=64)


net = Net(28, 128, 2, 10)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.01)

classes = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

net.train()
for epoch in range(20):

    running_loss = 0.0

    for i, data in enumerate(train_loader, 1):
        inputs, label = data

        inputs = inputs.squeeze(1)

        # Forward
        out = net(inputs)
        loss = criterion(out, label)
        running_loss += loss.data.item()



        optimizer.zero_grad()    
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()   
        if i % 200 == 0:    # print 
            print('[%d, %5d] loss: %.3f' %
                  (epoch + 1, i + 1, running_loss / 200))
            running_loss = 0.0




net.eval()
list_ground_truth = []
list_prediction = []

with torch.no_grad():
  for i, data in enumerate(test_loader, 1):
    inputs, labels = data

    inputs = inputs.squeeze(1)
    outputs = net(inputs)
    _, predicted = torch.max(outputs, 1)

    c = (predicted == labels).squeeze()    
    for i in range(len(labels)):
      list_ground_truth.append(classes[labels.cpu().numpy()[i]])
      list_prediction.append(classes[predicted.cpu().numpy()[i]])

test_classfication = metric.classification_report(list_ground_truth, list_prediction, target_names = classes, output_dict=False)
test_confusion = metric.confusion_matrix(list_ground_truth, list_prediction, labels = classes)
test_accuracy = metric.accuracy_score(list_ground_truth, list_prediction)

print(test_classfication)
print(test_confusion)
print(test_accuracy)