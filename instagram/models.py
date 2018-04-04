from helper import timestamp_to_datetime


class ApiModel(object):

    @classmethod
    def object_from_dictionary(cls, entry):
        # make dict keys all strings
        if entry is None:
            return ""
        entry_str_dict = dict([(str(key), value) for key, value in entry.items()])
        object = cls(**entry_str_dict)
        object._api_dict = entry
        return object
    
    def object_to_dictionary(self):
        return self._api_dict

    def __repr__(self):
        return unicode(self).encode('utf8')


class Image(ApiModel):

    def __init__(self, url, width, height):
        self.url = url
        self.height = height
        self.width = width

    def __unicode__(self):
        return "Image: %s" % self.url


class Video(Image):

    #2017-09-27: Video media type returns a new kwarg: id
    #def __init__(self, url, width, height):
    def __init__(self, *args, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self,k,v)
        super(Image, self).__init__(*args)

    def __unicode__(self):
        return "Video: %s" % self.url


class Media(ApiModel):

    def __init__(self, id=None, **kwargs):
        self.id = id
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def get_standard_resolution_url(self):
        if self.type == 'image':
            return self.images['standard_resolution'].url
        else:
            return self.videos['standard_resolution'].url

    def get_low_resolution_url(self):
        if self.type == 'image':
            return self.images['low_resolution'].url
        else:
            return self.videos['low_resolution'].url


    def get_thumbnail_url(self):
        return self.images['thumbnail'].url


    def __unicode__(self):
        return "Media: %s" % self.id

    @classmethod
    def object_from_dictionary(cls, entry):
        new_media = Media(id=entry['id'])
        new_media._api_dict = entry
        new_media.type = entry['type']

        new_media.user = User.object_from_dictionary(entry['user'])

        new_media.images = {}
        #2017-02-23: http://stackoverflow.com/questions/42456908/instagram-api-missing-elements-in-json-response
        for version, version_info in entry.get('images',{}).iteritems():
            new_media.images[version] = Image.object_from_dictionary(version_info)

        if new_media.type == 'video':
            new_media.videos = {}
            #2017-02-23: http://stackoverflow.com/questions/42456908/instagram-api-missing-elements-in-json-response
            for version, version_info in entry.get('videos',{}).iteritems():
                new_media.videos[version] = Video.object_from_dictionary(version_info)

        if 'user_has_liked' in entry:
            new_media.user_has_liked = entry['user_has_liked']
        new_media.like_count = entry['likes']['count']
        new_media.likes = []
        if 'data' in entry['likes']:
            for like in entry['likes']['data']:
                new_media.likes.append(User.object_from_dictionary(like))

        new_media.comment_count = entry['comments']['count']
        new_media.comments = []
        #HOTFIX
        #for comment in entry['comments']['data']:
        for comment in entry['comments'].get('data',[]):
            new_media.comments.append(Comment.object_from_dictionary(comment))

        new_media.created_time = timestamp_to_datetime(entry['created_time'])
        
        new_media.users_in_photo = []
        if entry.get('users_in_photo'):
            for user_in_photo in entry['users_in_photo']:
                new_media.users_in_photo.append(UserInPhoto.object_from_dictionary(user_in_photo))
        
        if entry['location'] and 'id' in entry:
            new_media.location = Location.object_from_dictionary(entry['location'])

        new_media.caption = None
        if entry['caption']:
            new_media.caption = Comment.object_from_dictionary(entry['caption'])

        if entry['tags']:
            new_media.tags = []
            for tag in entry['tags']:
                new_media.tags.append(Tag.object_from_dictionary({'name': tag}))

        new_media.link = entry['link']

        new_media.filter = entry.get('filter')

        return new_media


class MediaShortcode(Media):

    def __init__(self, shortcode=None, **kwargs):
        self.shortcode = shortcode
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Tag(ApiModel):
    def __init__(self, name, **kwargs):
        self.name = name
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __unicode__(self):
        return "Tag: %s" % self.name


class Comment(ApiModel):
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @classmethod
    def object_from_dictionary(cls, entry):
        user = User.object_from_dictionary(entry['from'])
        user._api_dict = entry
        text = entry['text']
        created_at = timestamp_to_datetime(entry['created_time'])
        id = entry['id']
        return Comment(id=id, user=user, text=text, created_at=created_at)

    def __unicode__(self):
        return "Comment: %s said \"%s\"" % (self.user.username, self.text)


class Point(ApiModel):
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __unicode__(self):
        return "Point: (%s, %s)" % (self.latitude, self.longitude)


class Location(ApiModel):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @classmethod
    def object_from_dictionary(cls, entry):
        point = None
        if 'latitude' in entry:
            point = Point(entry.get('latitude'),
                          entry.get('longitude'))
        location = Location(entry.get('id', 0),
                       point=point,
                       name=entry.get('name', ''))
        location._api_dict = entry
        return location

    def __unicode__(self):
        return "Location: %s (%s)" % (self.id, self.point)


class User(ApiModel):
    #HOTFIX 2018-04-04: id is missing
    #def __init__(self, id, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        self.id = id
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __unicode__(self):
        return "User: %s" % self.username


class Relationship(ApiModel):

    def __init__(self, incoming_status="none", outgoing_status="none", target_user_is_private=False):
        self.incoming_status = incoming_status
        self.outgoing_status = outgoing_status
        self.target_user_is_private = target_user_is_private

    def __unicode__(self):
        follows = False if self.outgoing_status == 'none' else True
        followed = False if self.incoming_status == 'none' else True

        return "Relationship: (Follows: %s, Followed by: %s)" % (follows, followed)



class Position(ApiModel):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __unicode__(self):
        return "Position: (%s, %s)" % (self.x, self.y)

    @classmethod
    def object_from_dictionary(cls, entry):
        if 'x' in entry:
            position = Position(entry['x'], entry['y'])
            position._api_dict = entry
            return position


class UserInPhoto(ApiModel):
    def __init__(self, user, position):
        self.position = position
        self.user = user

    def __unicode__(self):
        return "UserInPhoto: (%s, %s)" % (self.user, self.position)

    @classmethod
    def object_from_dictionary(cls, entry):
        user = None
        if 'user' in entry:
            user = User.object_from_dictionary(entry['user'])

        if 'position' in entry:
            position = Position(entry['position']['x'], entry['position']['y'])
        user_in_photo = UserInPhoto(user, position)
        user_in_photo._api_dict = entry
        return user_in_photo
