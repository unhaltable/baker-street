from django.views.decorators.csrf import ensure_csrf_cookie
from api.models import Document, Question, Page, ResearchSession
from api.serializers import DocumentSerializer, QuestionSerializer, UserSerializer, PageSerializer, \
    AuthTokenSerializer, ResearchSessionSerializer
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

class DocumentViewSet(viewsets.ModelViewSet):
    """API endpoint that allows documents to be viewed or edited"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

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
        if 'id' in request.QUERY_PARAMS:
            m = request.user.setCurrentSession(request.PARAMS['id'])
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
    def current(self, request):
        m = request.user.current_session
        serializer = ResearchSessionSerializer(m)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=["GET"])
    def documents(self, request, pk=None):
        canlii = CanLII("5tt8fdbp4s5jqjsj7arvfgbj")
        dbs = canlii.case_databases()
        db = dbs[0]
        s = []
        for x in range(8):
            s.append(CanLIIDocument(db[x]).json())
        return JsonResponse(s, safe=False)


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, format=None):
        #serializer = PageSerializer(data=request.DATA)
        session = request.user.current_session
        m = Page.objects.filter(research_session=session, title=request.DATA["title"], page_url=request.DATA["page_url"])
        if (len(m) == 1):
            m = session.setCurrentPage(m[0])
            serializer = PageSerializer(m)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            m = session.page_set.create(title=request.DATA["title"], page_url = request.DATA["page_url"])
            m = session.setCurrentPage(m)
            serializer = PageSerializer(m)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @list_route(methods=["GET"])
    def current(self, request):
        m = request.user.current_session.current_page
        serializer = PageSerializer(m)
        return Response(serializer.data, status=status.HTTP_200_OK)
