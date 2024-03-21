# Pytorch environment that starts a conda environment from a yaml file

# Use the official image as a parent image
FROM pytorch/pytorch:latest

# Set the working directory
WORKDIR /wmex

RUN conda env create -f environment.yml

# Create an image from the container: docker build -t wmex .
