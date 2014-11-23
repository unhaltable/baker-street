from django.views.decorators.csrf import ensure_csrf_cookie
from api.models import Document, Question, Page, ResearchSession, Blacklist
from api.serializers import DocumentSerializer, QuestionSerializer, UserSerializer, PageSerializer, \
    AuthTokenSerializer, ResearchSessionSerializer, BlacklistSerializer
from django.contrib import auth
from rest_framework import mixins, renderers, permissions, views, viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import list_route, detail_route
from rest_framework import generics
from rest_framework.response import Response
from pycanlii.canlii import CanLII
from api.scooby_doo.canlii_document import CanLIIDocument
from django.http import JsonResponse
from api.scooby_doo.watson_helpers import get_documents
from api.context_helpers import updateContext

class DocumentViewSet(viewsets.ModelViewSet):
    """API endpoint that allows documents to be viewed or edited"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, format=None):
        session = request.user.current_session
        page = session.current_page
        documents = get_documents(page.title, session)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, format=None):
        document = Document.objects.get(url=request.URL['url'])
        if (document.research_session != request.user.current_session):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        else:
            document.pinned = True
            document.save()
            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @list_route(methods=["GET"])
    def pinned(self, request, format=None):
        documents = Document.objects.filter(pinned=True, session=request.user.current_session)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# class QuestionViewSet(viewsets.ModelViewSet):
#     """API endpoint that allows groups to be viewed or edited"""
#     queryset = Question.objects.all()
#     serializer_class = QuestionSerializer

class AuthViewSet(viewsets.ModelViewSet):
    queryset = auth.get_user_model().objects.all()
    serializer_class = AuthTokenSerializer

    # POST /users/sign_in.json
    @list_route(methods=['POST'])
    def sign_in(self, request, format=None):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            token, created = Token.objects.get_or_create(user=serializer.object['user'])
            return Response({'token': token.key})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # POST /users/register.json
    # @list_route(methods=['POST'])
    # def register(self, request, format=None):
    #     pass

    # DELETE /users/sign_out.json
    @list_route(methods=['DELETE'], permission_classes=[permissions.IsAuthenticated])
    def sign_out(self, request, format=None):
        pass

class ResearchSessionViewSet(viewsets.ModelViewSet):
    model = ResearchSession
    serializer_class = ResearchSessionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ResearchSession.objects.filter(user=self.request.user)

    def create(self, request, format=None):
        """
        POST /research_session handler
        Gets a new research session and returns it
        """
        if 'id' in request.DATA:
            m = request.user.setCurrentSession(request.DATA['id'])
            serializer = ResearchSessionSerializer(m)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = ResearchSessionSerializer(data=request.DATA)
        if (serializer.is_valid()):
            m = request.user.researchsession_set.create()
            m.name = request.DATA['name']
            m.save()
            m = request.user.setCurrentSession(m.id)
            serializer = ResearchSessionSerializer(m)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=["GET"])
    def current(self, request, format=None):
        m = request.user.current_session
        serializer = ResearchSessionSerializer(m)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PageViewSet(viewsets.ModelViewSet):
    model = Page
    serializer_class = PageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Page.objects.filter(research_session=self.request.user.current_session, snippet=False)

    def create(self, request, format=None):
        #serializer = PageSerializer(data=request.DATA)
        session = request.user.current_session
        m = Page.objects.filter(research_session=session, title=request.DATA["title"], page_url=request.DATA["page_url"])
        if (len(m) == 1):
            updateContext(request.DATA["title"], session)
            m = session.setCurrentPage(m[0])
            serializer = PageSerializer(m)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            m = session.page_set.create(title=request.DATA["title"], page_url=request.DATA["page_url"],
                                        content=request.DATA["content"])
            m = session.setCurrentPage(m)
            serializer = PageSerializer(m)
            updateContext(request.DATA["title"], session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @list_route(methods=["GET"])
    def current(self, request, format=None):
        """
        This returns the current page according to the db, which is also the current page you're viewing
        This route is pointless, I have no clue why I made it.
        """
        m = request.user.current_session.current_page
        if (not m):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = PageSerializer(m)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BlacklistViewSet(viewsets.ModelViewSet):
    model = Blacklist
    serializer_class = BlacklistSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Blacklist.objects.filter(user=self.request.user)

    def create(self, request, format=None):
        m = request.user.blacklist_set.create(url=request.user)
        serializer = BlacklistSerializer(m)
        return Response(serializer.data, status=status.HTTP_200_OK)
