# Connected Vehicles Solution## Solution overview## Features## Running Solution### Requirements### Steps## Deployment on cloud#### Building docker images

cd cvgs

./mvnw package -Pprod verify jib:dockerBuild

cd ../cms

./mvnw package -Pprod verify jib:dockerBuild

cd ../vds

./mvnw package -Pprod verify jib:dockerBuild#### Pushing docker images to docker hub



### Google cloud platform### Microsoft Azure#### Requirements1. kubectl: The command line tool to interact with Kubernetes. Install and configure it.2. Azure CLI: The command line tool to interact with Azure. Install and log in with your Azure account(You can create a free account if you don't have one already).#### Stepsaz loginaz group create --name connectedVehicles --location eastusaz aks create --resource-group connectedVehicles --name connectedVehicles --node-count 2 --enable-addons monitoring --generate-ssh-keysaz aks get-credentials --resource-group connectedVehicles --name connectedVehiclescd k8skubectl apply -f registrykubectl apply -f cvgskubectl apply -f cmskubectl apply -f vds
