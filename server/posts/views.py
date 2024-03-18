from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Post
from .serializers import PostSerializer, ServerPostSerializer
from follow.models import Follows
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q
import uuid
from auth.BasicOrTokenAuthentication import BasicOrTokenAuthentication
from authors.models import Author
from authors.serializers import AuthorSerializer
from markdownx.utils import markdownify
from node.models import Node
import requests
from SocialDistribution.settings import SERVER
from auth.BasicOrTokenAuthentication import BasicOrTokenAuthentication
import string


class PostList(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by("-published")
    serializer_class = PostSerializer


class ProfilePost(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        try:
            # Filter posts by author ID
            queryset = Post.objects.filter(
                authorId=author_id, visibility__in=["PUBLIC", "FRIENDS"]
            )
            queryset = queryset.exclude(contentType__startswith="image/")

            # Order by published date
            queryset = queryset.order_by("-published")

            # Serialize the queryset to JSON
            serializer = PostSerializer(queryset, many=True)

            # Return serialized data as JSON response
            return Response(serializer.data)
        except Exception as e:
            # Handle exceptions (e.g., author not found, serializer errors)
            return Response({"error": str(e)}, status=500)


class ProfilePostForStranger(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        try:
            # Validate author_id as UUID
            uuid.UUID(author_id)
            print(author_id, type(author_id))
            # Filter posts by author ID
            queryset = Post.objects.filter(authorId=author_id, visibility="PUBLIC")
            queryset = queryset.exclude(contentType__startswith="image/")

            # Order by published date
            queryset = queryset.order_by("-published")

            # Serialize the queryset to JSON
            serializer = PostSerializer(queryset, many=True)

            # Return serialized data as JSON response
            return Response(serializer.data)
        except Exception as e:
            # Handle exceptions (e.g., author not found, serializer errors)
            return Response({"error": str(e)}, status=500)


class ProfilePostForHimself(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        try:
            # Filter posts by author ID
            queryset = Post.objects.filter(authorId=author_id)
            queryset = queryset.exclude(contentType__startswith="image/")

            # Order by published date
            queryset = queryset.order_by("-published")

            # Serialize the queryset to JSON
            serializer = PostSerializer(queryset, many=True)

            # Return serialized data as JSON response
            return Response(serializer.data)
        except Exception as e:
            # Handle exceptions (e.g., author not found, serializer errors)
            return Response({"error": str(e)}, status=500)


class PostById(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id, post_id):
        try:
            post = Post.objects.get(id=post_id)
            if post.visibility != "FRIENDS":
                serializer = PostSerializer(post)
                return Response(serializer.data)
            else:
                # Check if the user is friends with the author
                follower = Follows.objects.filter(
                    follower_id=author_id,
                    followed_id=post.authorId.id,
                    acceptedRequest=True,
                ).exists()
                followed = Follows.objects.filter(
                    follower_id=post.authorId.id,
                    followed_id=author_id,
                    acceptedRequest=True,
                ).exists()
                if follower and followed:
                    serializer = PostSerializer(post)
                    return Response(serializer.data)
                else:
                    return Response(status=status.HTTP_403_FORBIDDEN)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class PostDetail(APIView):
    authentication_classes = [BasicOrTokenAuthentication]

    def get_serializer_class(self):
        return PostSerializer

    def get(self, request, author_id, post_id):
        try:
            post = Post.objects.get(id=post_id)
            base_url = request.build_absolute_uri("/")
            serializer = PostSerializer(post, context={"base_url": base_url})
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, author_id, post_id):
        try:
            print("request.data", request.data)
            post = Post.objects.get(id=post_id)

            request_data = request.data.copy()
            request_data["authorId"] = author_id
            print("Current request_data image:", request_data["image"])
            if request_data["image"]:
                # Delete old image post
                if post.image_ref:
                    image_blob = request.data["image"]
                    image_info = image_blob.split(",")
                    post.image_ref.content = image_info[1]
                    post.image_ref.contentType = image_info[0][5:]
                    post.image_ref.save()
                else:
                    print("I AM CREATING A NEW POST | Current post_id:", post_id)
                    print("Before making | Current image_ref?:", post.image_ref)
                    # Create a new one
                    id, response = self.create_image_post(
                        request, author_id, post_id, request.data["image"]
                    )
                    if response:
                        request_data["image_ref"] = id
                        print("After making | Current image_ref:", id)

            # # serializer accepts CommonMark content
            # if request_data["contentType"] == "text/markdown":
            #     request_data["content"] = markdownify(request_data["content"])
            serializer = PostSerializer(post, data=request_data, partial=True)
            if serializer.is_valid():
                if str(request.user.id) == author_id or request.GET.get("request_host"):
                    serializer.save()

                    node = Node.objects.all()
                    print("NODES", node)
                    query_set = Author.objects.get(id=author_id)
                    serializer = AuthorSerializer(query_set)
                    author = serializer.data
                    print("AUTHOR", author)

                    if author["host"] == SERVER:
                        # make a request to all nodes api/authors/<str:author_id>/posts/<str:post_id>/
                        for n in node:
                            url = n.host + f"/api/authors/{author_id}/posts/{post_id}/"

                            response = requests.put(
                                url,
                                json=request_data,
                                auth=(n.username, n.password),
                                params={"request_host": SERVER},
                            )

                    return Response(serializer.data, status=status.HTTP_200_OK)
            # print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create_image_post(self, request, author_id, post_id, image_blob):
        try:
            request_data = request.data.copy()
            image_info = image_blob.split(",")

            request_data["content"] = image_info[1]
            request_data["contentType"] = image_info[0][5:]
            request_data["image"] = None
            # Ensure that authorId is passed as an integer
            request_data["authorId"] = author_id
            # print("New Data created:")
            print(request_data)

            serializer = PostSerializer(data=request_data, partial=True)

            if serializer.is_valid():
                if str(request.user.id) == author_id:
                    serializer.save()
                    saved_data = serializer.data
                    saved_id = saved_data.get("id", None)
                    print("Saved id:", saved_id)
                    return saved_id, True
            # print(serializer.errors)
            return None, False
        except Post.DoesNotExist:
            return None, False

    def delete(self, request, author_id, post_id):
        try:
            regular_post = Post.objects.get(id=post_id)
            if str(regular_post.authorId.id) == author_id:
                # Delete the associated image post, if it exists
                if regular_post.image_ref:
                    regular_post.image_ref.delete()

                # Delete the regular post
                regular_post.delete()

                # get all nodes - for remote deleting
                query_set = Author.objects.get(id=author_id)
                serializer = AuthorSerializer(query_set)
                author = serializer.data
                if author["host"] == SERVER:
                    node = Node.objects.all()
                    for n in node:
                        # send the post to the inbox of every other author
                        # /api/authors?request_host=${encodeURIComponent(server)}
                        url = n.host + f"/api/authors"
                        print("URL", url)
                        response = requests.get(
                            url,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                        remoteAuthors = response.json().get("items", [])

                        for remoteAuthor in remoteAuthors:
                            print("REMOTE AUTHOR", remoteAuthor)
                            url = n.host + f"/api/authors/{author_id}/posts/{post_id}/"
                            response = requests.delete(
                                url,
                                auth=(n.username, n.password),
                                params={"request_host": SERVER},
                            )
                            print(response.status_code)

                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class AuthorPosts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        queryset = Post.objects.filter(authorId=author_id)
        queryset = queryset.exclude(contentType__startswith="image/")

        # Order by published date
        queryset = queryset.order_by("-published")
        base_url = request.build_absolute_uri("/")
        serializer = PostSerializer(queryset, many=True, context={"base_url": base_url})
        return Response(serializer.data)

    def post(self, request, author_id):
        request_data = request.data.copy()
        print("DATA", request_data)
        request_data["authorId"] = author_id
        if request_data["image"]:
            id, response = self.create_image_post(
                request, author_id, request.data["image"]
            )
            if response:
                request_data["image_ref"] = id
                print("After making | Current image_ref?:", id)

        # serializer accepts CommonMark content
        if request_data["contentType"] == "text/markdown":
            request_data["content"] = markdownify(request_data["content"])

        serializer = ServerPostSerializer(data=request_data)
        if serializer.is_valid():
            print("VALID OR NOT")
            if str(request.user.id) == author_id:
                # update
                serializer.save()
                print("SERIALIZER DATA", serializer.data)

                remoteData = {
                    "type": "post",
                    "id": str(serializer.data["id"]),
                    "authorId": author_id,
                    "title": serializer.data["title"],
                    "content": serializer.data["content"],
                    "contentType": serializer.data["contentType"],
                    "visibility": serializer.data["visibility"],
                    "image_ref": str(serializer.data["image_ref"]),
                    "sharedBy": None,
                    "isShared": False,
                }

                # get all nodes
                node = Node.objects.all()
                print("NODES", node)
                remoteAuthors = []
                # make a request to all nodes api/authors/<str:author_id>/inbox/
                for n in node:
                    # send the post to the inbox of every other author
                    # /api/authors?request_host=${encodeURIComponent(server)}
                    if request.data.get("visibility") == "PUBLIC":
                        url = n.host + f"/api/authors"
                        print("URL", url)
                        response = requests.get(
                            url,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                        remoteAuthors = response.json().get("items", [])
                    elif request.data.get("visibility") == "FRIENDS":
                        url = n.host + f"/api/friends/friends/{author_id}"

                        response = requests.get(
                            url,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                        print("RESPONSE", response.json())
                        remoteAuthors = response.json()
                        print("REMOTE AUTHORS", remoteAuthors)

                    for remoteAuthor in remoteAuthors:
                        print("REMOTE AUTHOR", remoteAuthor)
                        try:
                            id = remoteAuthor["id"]
                        except KeyError:
                            id = remoteAuthor["user_id"]

                        url = n.host + f"/api/authors/{str(id)}/inbox/"

                        response = requests.post(
                            url,
                            json=remoteData,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                        print("sfhd", response)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_image_post(self, request, author_id, image_blob):
        try:
            request_data = request.data.copy()
            image_info = image_blob.split(",")
            request_data["content"] = image_info[1]
            request_data["contentType"] = image_info[0][5:]
            request_data["image"] = None
            request_data["authorId"] = author_id

            print("image post: ", request_data)
            serializer = ServerPostSerializer(data=request_data)
            print("Serializer validated:", serializer.is_valid())
            if serializer.is_valid():
                if str(request.user.id) == author_id:
                    serializer.save()
                    saved_data = serializer.data
                    saved_id = saved_data.get("id", None)
                    return saved_id, True
            return None, False
        except Exception as e:
            return None, False


class PublicPosts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter posts by authorId and visibility='PUBLIC'
        queryset = Post.objects.filter(visibility="PUBLIC")
        queryset = queryset.exclude(contentType__startswith="image/")

        # Order by published date
        queryset = queryset.order_by("-published")
        base_url = request.build_absolute_uri("/")
        serializer = PostSerializer(queryset, many=True, context={"base_url": base_url})
        return Response(serializer.data, status=status.HTTP_200_OK)


class FollowingPosts(APIView):
    def get(self, request):
        try:
            user_id = request.user.id

            # Get posts authored by users the current user follows
            followed_users_ids = Follows.objects.filter(
                follower_id=user_id, acceptedRequest=True
            ).values_list("followed_id", flat=True)

            # Include the current user's ID in the list of followed users
            followed_users_ids = list(followed_users_ids)
            followed_users_ids.append(user_id)

            queryset = Post.objects.filter(
                visibility__in=["PUBLIC", "FRIENDS"],
                authorId__in=followed_users_ids,
            ).exclude(contentType__startswith="image/")
            # queryset = queryset.exclude(contentType__startswith="image/")

            # Order by published date
            queryset = queryset.order_by("-published")

            # Filter FRIENDS-only posts further to include only posts from users who are friends
            if "FRIENDS" in queryset.values_list("visibility", flat=True):
                friends_ids = Follows.objects.filter(
                    follower_id=user_id,
                    followed_id__in=queryset.filter(visibility="FRIENDS").values_list(
                        "authorId", flat=True
                    ),
                    acceptedRequest=True,
                ).values_list("followed_id", flat=True)
                queryset = queryset.filter(authorId__in=list(friends_ids) + [user_id])

            # Serialize the queryset to JSON
            base_url = request.build_absolute_uri("/")
            serializer = PostSerializer(
                queryset, many=True, context={"base_url": base_url}
            )

            # Return serialized data as JSON response
            return Response(serializer.data)

        except Exception as e:
            # Handle exceptions (e.g., author not found, serializer errors)
            return Response({"error": str(e)}, status=500)


class SharedPost(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, author_id, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        print("I ENTERED HERE")
        if post.visibility == "PUBLIC" and author_id != str(post.authorId.id):
            serializer = ServerPostSerializer(post)
            shared_post = serializer.data
            shared_post["published"] = timezone.now()
            shared_post["isShared"] = True
            # sharedBy means original author
            shared_post["sharedBy"] = shared_post["authorId"]
            # authorId is the author sharing the post
            shared_post["authorId"] = author_id
            shared_post["visibility"] = "PUBLIC"
            shared_post["originalContent"] = shared_post["content"]
            shared_post["content"] = request.data["content"]
            if post.image_ref:
                shared_post["image_ref"] = post.image_ref.id
            else:
                shared_post["image_ref"] = None
            serializer = ServerPostSerializer(data=shared_post)
            print("VALID?: ", serializer.is_valid())
            if serializer.is_valid():
                serializer.save()
                # get all nodes
                publish = shared_post.pop("published")
                shared_post["id"] = serializer.data["id"]
                shared_post["sharedBy"] = str(shared_post["sharedBy"])
                shared_post["image_ref"] = str(shared_post["image_ref"])
                node = Node.objects.all()
                print(shared_post)
                remoteAuthors = []
                # make a request to all nodes api/authors/<str:author_id>/inbox/
                for n in node:
                    # send the post to the inbox of every other author
                    # /api/authors?request_host=${encodeURIComponent(server)}
                    if shared_post["visibility"] == "PUBLIC":
                        url = n.host + f"/api/authors"
                        print("URL", url)
                        response = requests.get(
                            url,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                        remoteAuthors = response.json().get("items", [])
                    elif shared_post["visibility"] == "FRIENDS":
                        url = n.host + f"/api/friends/friends/{author_id}"

                        response = requests.get(
                            url,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                        print("RESPONSE", response.json())
                        remoteAuthors = response.json()
                        print("REMOTE AUTHORS", remoteAuthors)

                    for remoteAuthor in remoteAuthors:
                        print("REMOTE AUTHOR", remoteAuthor)
                        try:
                            id = remoteAuthor["id"]
                        except KeyError:
                            id = remoteAuthor["user_id"]

                        url = n.host + f"/api/authors/{str(id)}/inbox/"

                        response = requests.post(
                            url,
                            json=shared_post,
                            auth=(n.username, n.password),
                            params={"request_host": SERVER},
                        )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"error": "You are not authorized to share this post"},
                status=status.HTTP_403_FORBIDDEN,
            )


# authors/<str:author_id>/posts/<str:post_id>/image/
class ImagePost(APIView):
    authentication_classes = [BasicOrTokenAuthentication]

    def get(self, request, author_id, post_id):
        try:
            post = Post.objects.get(id=post_id)
            if post.image_ref != None:
                base_url = request.build_absolute_uri("/")
                serializer = PostSerializer(
                    post.image_ref, context={"base_url": base_url}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, author_id, post_id):
        try:
            regular_post = Post.objects.get(id=post_id)
            if str(regular_post.authorId.id) == author_id:
                # Delete the associated image post, if it exists
                if regular_post.image_ref:
                    regular_post.image_ref.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
