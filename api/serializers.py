from api.models import Document, Question, ResearchSession, Page
from django.contrib import auth
from rest_framework import serializers

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Document
        fields = ('title', '')


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Question
        fields = ('question_text', 'document')


class ResearchSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchSession
        fields = ('name', 'id')
        read_only_fields = ('id',)

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.name = attrs.get('name', instance.name)
            return instance
        return ResearchSession(**attrs)



class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = auth.get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password', 'groups',
                  'is_active', 'last_login', 'date_joined')
        write_only_fields = ('password',)


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = auth.authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise serializers.ValidationError(msg)
                attrs['user'] = user
                return attrs
            else:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg)
        else:
            msg = 'Must include "email" and "password"'
            raise serializers.ValidationError(msg)


class AuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)
    user = UserSerializer(read_only=True)
    token = AuthTokenSerializer(read_only=True)

    # def restore_object(self, attrs, instance=None):
    #     return {
    #
    #     }


class PageSerializer(serializers.HyperlinkedModelSerializer):
    content = serializers.CharField(required=False)
    class Meta:
        model = Page
        fields = ('page_url', 'title', 'content', 'website', 'pinned')

