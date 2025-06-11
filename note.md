### Transfer file from local to remote server

```bash
sudo scp .env.production root@157.173.222.110:/projects/substring_back/
```

### Remove the old key entry (recommended if you’re confident)

```bash

sudo ssh-keygen -R 157.173.222.110
```

### Install Docker

```bash

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Install Docker Compose

```bash

sudo apt-get install docker-compose-plugin

```