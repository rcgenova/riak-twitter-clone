riak-admin bucket-type create user '{"props":{"consistent":true}}'
riak-admin bucket-type activate user

riak-admin bucket-type create user-map '{"props":{"datatype":"map"}}'
riak-admin bucket-type activate user-map

riak-admin bucket-type create user-set '{"props":{"datatype":"set"}}'
riak-admin bucket-type activate user-set

riak-admin bucket-type create user-default
riak-admin bucket-type activate user-default

riak-admin bucket-type create post
riak-admin bucket-type activate post
