# riak-twitter-clone

Demo app that emulates a Twitter-like REST API. Utilizes Python Flask and Riak Data Types (CRDTs).

## Setup

### Python pre-requisites

```bash
$ sudo yum install -y python-setuptools gcc python-devel libffi-devel openssl-devel
$ sudo easy_install pip
$ sudo pip install flask
$ sudo pip install riak
```

### Install Riak

```bash
$ wget http://s3.amazonaws.com/downloads.basho.com/riak/2.1/2.1.3/rhel/7/riak-2.1.3-1.el7.centos.x86_64.rpm
$ sudo rpm -Uvh riak-2.1.3-1.el7.centos.x86_64.rpm
```

### Set ulimit

```bash
$ echo 'riak soft nofile 65536' | sudo tee --append /etc/security/limits.conf
$ echo 'riak hard nofile 65536' | sudo tee --append /etc/security/limits.conf
$ echo "$USER soft nofile 65536" | sudo tee --append /etc/security/limits.conf
$ echo "$USER hard nofile 65536" | sudo tee --append /etc/security/limits.conf
```

### Start Riak

```bash
$ sudo riak start
```

### Clone riak-twitter-clone

```bash
$ git clone git@github.com:rcgenova/riak-twitter-clone.git
```

### Create bucket types

```bash
$ cd riak-twitter-clone
$ sudo bash admin.bash
```

## Usage

Start the API:  

```bash
$ python app.py
```

Open another SSH tab and run the example commands below:  

### New user

POST /api/v1.0/user/new -d {"user":[USER_ID],"password":[PASSWORD]}  

```bash
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/new -H "Content-Type: application/json" -d '{"user_id":"rgenova@basho.com","password":"passnow"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/new -H "Content-Type: application/json" -d '{"user_id":"user2@basho.com","password":"passnow"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/new -H "Content-Type: application/json" -d '{"user_id":"user3@basho.com","password":"passnow"}'
```

### Get user

GET /api/v1.0/user/[USER_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/rgenova@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/user2@basho.com
```

(The only property currently stored is the password hash.)

### Follow user

PUT /api/v1.0/user/follow -d {"primary_user_id":[PRIMARY_USER_ID],"secondary_user_id":[SECONDARY_USER_ID]}  

(primary follows secondary)

```bash
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/follow -H "Content-Type: application/json" -d '{"primary_user_id":"rgenova@basho.com","secondary_user_id":"user2@basho.com"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/follow -H "Content-Type: application/json" -d '{"primary_user_id":"rgenova@basho.com","secondary_user_id":"user3@basho.com"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/follow -H "Content-Type: application/json" -d '{"primary_user_id":"user2@basho.com","secondary_user_id":"user3@basho.com"}'
```

### Unfollow user

PUT /api/v1.0/user/unfollow -d {"primary_user_id":[PRIMARY_USER_ID],"secondary_user_id":[SECONDARY_USER_ID]}  

(primary unfollows secondary)

```bash
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/user/unfollow -H "Content-Type: application/json" -d '{"primary_user_id":"user2@basho.com","secondary_user_id":"user3@basho.com"}'
```

### Get followers

GET /api/v1.0/user/followers/[USER_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/followers/user2@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/followers/user3@basho.com
```

### Get following

GET /api/v1.0/user/following/[USER_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/following/rgenova@basho.com
```

### New post

POST /api/v1.0/post -d {"user":[USER_ID],"text":[TEXT]}  

```bash
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/post -H "Content-Type: application/json" -d '{"user_id":"rgenova@basho.com","text":"rgenova post #1"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/post -H "Content-Type: application/json" -d '{"user_id":"user2@basho.com","text":"user2 post #1"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/post -H "Content-Type: application/json" -d '{"user_id":"user3@basho.com","text":"user3 post #1"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/post -H "Content-Type: application/json" -d '{"user_id":"user3@basho.com","text":"user3 post #2"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/post -H "Content-Type: application/json" -d '{"user_id":"user3@basho.com","text":"user3 post #3"}'
$ curl -i -X POST http://localhost:5000/riak-twitter-clone/api/v1.0/post -H "Content-Type: application/json" -d '{"user_id":"user3@basho.com","text":"user3 post #4"}'
```

### Get post

GET /api/v1.0/post/[POST_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/post/[POST_ID]
```

(Substitute a `post_id` returned from a new post command above.)

### Get user timeline

GET /api/v1.0/user/timeline/[USER_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/timeline/rgenova@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/timeline/user2@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/timeline/user3@basho.com
```

### Get user posts

GET /api/v1.0/user/posts/[USER_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/posts/rgenova@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/posts/user3@basho.com
```

### Get stats

GET /api/v1.0/user/stats/[USER_ID]  

```bash
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/stats/rgenova@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/stats/user2@basho.com
$ curl http://localhost:5000/riak-twitter-clone/api/v1.0/user/stats/user3@basho.com
````



