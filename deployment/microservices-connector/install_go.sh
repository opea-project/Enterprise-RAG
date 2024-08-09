sudo apt-get update
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -xvf go1.21.0.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo mv go /usr/local
sudo rm go1.21.0.linux-amd64.tar.gz

echo "
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH" >> ~/.profile
