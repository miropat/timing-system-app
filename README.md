#Setting up the virtual system on a Raspberry PI
Install docker

docker build -t timing-simulator .
docker run -it -p 65432:65432 --name timing-simulator timing-simulator

If already running but need to restart
docker run -it -p65432:65432 virtual-system

And if edits are needed its easy to delete with the name and then build again:
docker rm timing-simulator

-d detached mode, if there is no need to see whats going on
