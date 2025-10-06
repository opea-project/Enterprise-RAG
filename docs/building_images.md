# Build the images in Intel® AI for Enterprise RAG

## Configure the Environment
To prepare your environment for development and deployment, run the following command:

```sh
ansible-playbook -u $USER -K playbooks/application.yaml --tags configure -e @inventory/test-cluster/config.yaml
```

This command will configure various tools in your environment, including `Docker`, `Helm`, `make`, `zip`, and `jq`.

> [!NOTE]
> Before running the script, be aware that it uses `sudo` privileges to install the mentioned packages and configure settings. Use with caution, as this may overwrite existing configurations.

---

## Docker Images

Deployment utilizes Docker images - check [docker images list](../docs/docker_images_list.md) for detailed information. 

Prebuilt images for Intel® AI for Enterprise RAG components are publicly available on [OPEA Docker Hub](https://hub.docker.com/u/opea?page=1&search=erag) and are used by default, as defined by the  `registry` and `tag` values in [../deployment/inventory/sample/config.yaml](../deployment/inventory/sample/config.yaml).

If you prefer to build the images manually and push them to a private registry, follow the steps below. Then, update the registry and tag values in your `config.yaml` file accordingly to point to them.

### Build and Push Images

The `update_images.sh` script is responsible for building the images for these microservices from source and pushing them to a specified registry. The script consists of three main steps: build images, set up the registry, and push the images. To execute all at once, run:
```bash
./update_images.sh --build --setup-registry --push
```

Alternatively, you can run each step separately. Below is a detailed description of each step, along with additional options. You can also run `./update_images.sh --help` for more information.

#### Step 1: Build

The first step is to build the images for each microservice component using the source code. This involves compiling the code, packaging it into Docker images, and performing any necessary setup tasks.

```bash
./update_images.sh --build
```

> [!NOTE]
> - You can build individual images, for example `./update_images.sh --build embedding-usvc reranking-usvc` which only builds the embedding and reranking images.
> - To list all available image names, run `./update_images.sh --help` and refer to the "Components Available" section.
> - Use `-j <number of concurrent tasks>` parameter to increase the number of concurrent tasks.
> - Use `--tag <your tag>` to set a custom image tag. Defaults to `latest` if not specified.

#### Step 2: Setup Registry

The second step is to configure the registry where the built images will be pushed. This may involve
setting up authentication, specifying the image tags, and defining other configuration parameters.

```bash
./update_images.sh --setup-registry
```

By default, the registry is set to `localhost:5000` You can change this by specifying a different registry using the `--registry` option.

#### Step 3: Push

The final step is to push the built images to the configured registry. This ensures that the images are
deployed to the desired environment and can be accessed by the application.

```bash
./update_images.sh --push
```