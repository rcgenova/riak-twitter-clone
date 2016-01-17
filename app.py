from flask import Flask, jsonify, abort, request, make_response
import riak
from riak.datatypes import Map, Set

import json
import hashlib
import uuid
from time import gmtime, strftime

client = riak.RiakClient(host="127.0.0.1", pb_port=8087)

app = Flask(__name__)

def add_post(user_id, post_id, bucket):

    # Used to update 'posts' and 'timelines', based on bucket parameter
    # New post_ids are prepended to the list

    bucket_type = 'user-default'
    bucket = client.bucket_type(bucket_type).bucket(bucket)

    fetched = bucket.get(user_id)
    if fetched.data == None:
        fetched.data = {}
        fetched.data['post_ids'] = [post_id]
    else:
        fetched.data['post_ids'].insert(0, post_id)

    fetched.store()

def get_follow(user_id, bucket):

    # Returns 'followers' or 'following' based on bucket parameter
    
    bucket_type = 'user-set'
    bucket = client.bucket_type(bucket_type).bucket(bucket)

    fetched = bucket.get(user_id)
    follow = []
    for item in fetched:
        follow.append(item)

    return follow

def fan_out(user_id, post_id):

    # Call add_post for each follower

    followers = get_follow(user_id, 'followers')
    for user_id in followers:
        add_post(user_id, post_id, 'timeline')

def get_posts(user_id):

    # Iterates over post_ids to populate posts object
    
    user_posts_bucket = client.bucket_type('user-default').bucket('posts')
    user_post_ids = user_posts_bucket.get(user_id)

    posts = []
    print user_post_ids
    if user_post_ids.data is not None:
        posts_bucket = client.bucket_type('post').bucket('posts')
        for post_id in user_post_ids.data['post_ids']:
            post = posts_bucket.get(post_id).data
            del post['user_id']
            posts.append(post)

    return posts

def get_timeline(user_id):

    # Iterates over post_ids to populate timeline object
    
    timeline_bucket = client.bucket_type('user-default').bucket('timeline')
    timeline_ids = timeline_bucket.get(user_id)

    timeline = []
    if timeline_ids.data is not None:
        posts_bucket = client.bucket_type('post').bucket('posts')
        for post_id in timeline_ids.data['post_ids']:
            post = posts_bucket.get(post_id).data
            timeline.append(post)

    return timeline

def update_stats(user_id, stat, increment_flag=True):

    # Per user counters stored for: 'following', 'followers', 'posts'

    stats_bucket = client.bucket_type('user-map').bucket('stats')
    stats = Map(stats_bucket, user_id)

    if increment_flag:
        stats.counters[stat].increment()
    else:
        stats.counters[stat].decrement()

    stats.store(return_body=False)

def get_stats(user_id):

    # Returns user statistics
    
    stats_bucket = client.bucket_type('user-map').bucket('stats')
    stats = Map(stats_bucket, user_id)
    stats.reload()
    stats_dict = {}
    stats_dict['posts'] = stats.counters['posts'].value
    stats_dict['following'] = stats.counters['following'].value
    stats_dict['followers'] = stats.counters['followers'].value

    return stats_dict

@app.route('/')
def index():
    return "Riak Twitter Clone"

@app.route('/riak-twitter-clone/api/v1.0/user/new', methods=['POST'])
def create_user():

    bucket_type = 'user'
    bucket = client.bucket_type(bucket_type).bucket('users')

    user = {}
    key = request.json['user_id'].encode('utf8')
    user['password_hash'] = hashlib.md5(request.json['password']).hexdigest()
    record = bucket.new(key, data=user)
    record.store()

    return jsonify({'user': user}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    
    bucket_type = 'user'
    bucket = client.bucket_type(bucket_type).bucket('users')

    fetched = bucket.get(user_id)

    return jsonify({'user': fetched.data})

@app.route('/riak-twitter-clone/api/v1.0/user/follow', methods=['POST'])
def follow_user():

    # Maintain separate following and followers lists
    # 'primary_user_id' and 'secondary_user_id' consititute payload
    # primary follows secondary

    bucket_type = 'user-set'

    primary_user_id = request.json['primary_user_id'].encode('utf8')
    secondary_user_id = request.json['secondary_user_id'].encode('utf8')

    # Add secondary_user_id to 'following' set for primary_user_id
    following = client.bucket_type(bucket_type).bucket('following').get(primary_user_id)
    following.add(secondary_user_id)
    following.update()
    update_stats(primary_user_id, 'following')

    # Add primary_user_id to 'followers' set for secondary_user_id
    followers = client.bucket_type(bucket_type).bucket('followers').get(secondary_user_id)
    followers.add(primary_user_id)
    followers.update()
    update_stats(secondary_user_id, 'followers')

    return jsonify({'primary_user_id': request.json['primary_user_id'], 'secondary_user_id': request.json['secondary_user_id']}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/unfollow', methods=['POST'])
def unfollow_user():

    bucket_type = 'user-set'

    primary_user_id = request.json['primary_user_id'].encode('utf8')
    secondary_user_id = request.json['secondary_user_id'].encode('utf8')

    # Remove secondary_user_id from 'following' set for primary_user_id
    following = client.bucket_type(bucket_type).bucket('following').get(primary_user_id)
    following.discard(secondary_user_id)
    following.update()
    update_stats(primary_user_id, 'following', False)

    # Remove primary_user_id from 'followers' set for secondary_user_id
    followers = client.bucket_type(bucket_type).bucket('followers').get(secondary_user_id)
    followers.discard(primary_user_id)
    followers.update()
    update_stats(secondary_user_id, 'followers', False)

    return jsonify({'primary_user_id': request.json['primary_user_id'], 'secondary_user_id': request.json['secondary_user_id']}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/followers/<string:user_id>', methods=['GET'])
def get_followers_api(user_id):

    return jsonify({'followers': get_follow(user_id.encode('utf8'), 'followers')}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/following/<string:user_id>', methods=['GET'])
def get_following(user_id):
    
    return jsonify({'following': get_follow(user_id.encode('utf8'), 'following')}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/posts/<string:user_id>', methods=['GET'])
def get_posts_api(user_id):
    
    return jsonify({'posts': get_posts(user_id)}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/timeline/<string:user_id>', methods=['GET'])
def get_timeline_api(user_id):
    
    return jsonify({'timeline': get_timeline(user_id)}), 201

@app.route('/riak-twitter-clone/api/v1.0/user/stats/<string:user_id>', methods=['GET'])
def get_stats_api(user_id):

    user_id = user_id.encode('utf8')
    return jsonify({'stats': get_stats(user_id)}), 201

@app.route('/riak-twitter-clone/api/v1.0/post', methods=['POST'])
def new_post():

    bucket_type = 'post'
    bucket = client.bucket_type(bucket_type).bucket('posts')

    user_id = request.json['user_id'].encode('utf8')

    post = {}
    key = uuid.uuid4().hex
    post['user_id'] = user_id
    post['timestamp'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    post['text'] = request.json['text']
    record = bucket.new(key, data=post)
    record.store()

    add_post(user_id, key, 'posts')  # updates the list of posts for the user
    update_stats(user_id, 'posts')

    add_post(user_id, key, 'timeline')  # adds the post to the user's timeline
    fan_out(user_id, key) # update timeline for followers; ultimately calls add_post for each

    return jsonify({'id': key, 'post': post}), 201

@app.route('/riak-twitter-clone/api/v1.0/post/<string:post_id>', methods=['GET'])
def get_post(post_id):
    
    bucket_type = 'post'
    bucket = client.bucket_type(bucket_type).bucket('posts')

    fetched = bucket.get(post_id)

    return jsonify({'post': fetched.data})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)
